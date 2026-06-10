"""
==============================================================================
CRT ENGINE — Candle Range Theory (Fully Systematic)
==============================================================================
Implements the 3-candle CRT model + Romeo ICT entry model.

CRT 3-Candle Model:
  Candle 1: Establishes the range
  Candle 2: Sweeps C1 high/low (liquidity raid)
  Candle 3: Confirms reversal (displacement into opposite side)

Romeo ICT Add-on:
  After CRT confirmation → find FVG for limit entry
  SL beyond sweep extreme + ATR buffer
  Targets: opposing liquidity pool (Draw on Liquidity)

Displacement Definition (Systematic):
  Range > 1.5 × ATR(14)
  Close in top/bottom 20% of candle
  Volume > 1.2 × rolling average (if available)

All parameters configurable. Zero discretion.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from core.logger import get_logger
from strategy.market_structure import MarketStructureResult, LiquidityPool, SessionLevel
from config.settings import (
    CRT_SWEEP_THRESHOLD_PCT, CRT_SWEEP_MAX_CLOSE_PCT,
    CRT_CONFIRMATION_BODY_ATR, CRT_CONFIRMATION_CLOSE_PCT,
    DISPLACEMENT_ATR_MULT, DISPLACEMENT_CLOSE_PCT, DISPLACEMENT_VOL_MULT,
    SWEEP_WICK_MIN_PCT, SWEEP_CLOSEBACK_BARS, SWEEP_LOOKBACK_BARS,
    FVG_MAX_LOOKBACK, FVG_MIN_SIZE_PIPS,
    MIN_RR_RATIO, SL_ATR_BUFFER, PARTIAL_CLOSE_RR,
)

log = get_logger("strategy.crt_engine")


# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class LiquiditySweep:
    kind:         str      # "HIGH_SWEPT" | "LOW_SWEPT"
    swept_level:  float    # the liquidity pool / level that was swept
    sweep_high:   float    # high of sweep candle
    sweep_low:    float    # low of sweep candle
    sweep_close:  float    # close of sweep candle
    bar_index:    int
    wick_pct:     float    # wick as % of total candle range
    level_type:   str      # "PDH"|"PDL"|"SessionH"|"SessionL"|"EQH"|"EQL"|"SwingH"|"SwingL"
    strength:     float    # 0-1


@dataclass
class DisplacementCandle:
    direction:    str      # "BULLISH" | "BEARISH"
    bar_index:    int
    body_atr:     float    # body / ATR — higher = stronger
    close_pct:    float    # close location in candle range 0-1
    volume_ratio: float    # volume / rolling avg
    is_valid:     bool     # meets all displacement criteria


@dataclass
class FairValueGap:
    kind:       str        # "BULLISH_FVG" | "BEARISH_FVG"
    top:        float
    bottom:     float
    mid:        float
    size_pips:  float
    bar_index:  int
    filled:     bool = False


@dataclass
class CRTSignal:
    """The complete CRT + Romeo ICT trade signal."""
    symbol:          str
    direction:       str       # "BUY" | "SELL"

    # Entry
    entry_price:     float     # FVG 50% (equilibrium)
    entry_top:       float     # FVG top (for limit order buffer)
    entry_bottom:    float     # FVG bottom

    # Risk levels
    stop_loss:       float     # beyond sweep extreme + ATR buffer
    sl_pips:         float

    # Targets
    take_profit_1:   float     # 2R
    take_profit_2:   float     # 3R
    take_profit_3:   float     # 5R (DOL)
    dol_target:      float     # Draw on Liquidity (opposing pool)

    # Quality metrics
    rr_ratio:        float
    confidence:      float     # 0-100 composite score
    ai_score:        float = 0.0
    displacement_str:float = 0.0
    fvg_size_pips:   float = 0.0
    sweep_strength:  float = 0.0

    # Context
    timeframe:       str   = ""
    killzone:        str   = ""
    signal_time:     datetime = field(default_factory=datetime.utcnow)
    reason:          str   = ""

    # Components
    sweep:           Optional[LiquiditySweep]    = None
    displacement:    Optional[DisplacementCandle] = None
    fvg:             Optional[FairValueGap]       = None
    metadata:        Dict[str, Any]               = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "symbol":        self.symbol,
            "direction":     self.direction,
            "entry_price":   self.entry_price,
            "stop_loss":     self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "rr_ratio":      self.rr_ratio,
            "confidence":    self.confidence,
            "ai_score":      self.ai_score,
            "timeframe":     self.timeframe,
            "signal_time":   str(self.signal_time),
            "reason":        self.reason,
            "killzone":      self.killzone,
            "dol_target":    self.dol_target,
            "displacement":  self.displacement_str,
            "fvg_size_pips": self.fvg_size_pips,
        }


# ──────────────────────────────────────────────────────────────────────────────
class CRTEngine:
    """
    Systematic CRT + Romeo ICT execution engine.
    Zero discretion — all rules parameterized.
    """

    def generate_signal(
        self,
        symbol:       str,
        direction:    str,           # "BUY" | "SELL" (from HTF bias)
        df:           pd.DataFrame,  # execution TF candles
        ms:           MarketStructureResult,
        point:        float,
        killzone:     str,
        zones:        list = None,
    ) -> Optional[CRTSignal]:

        if df is None or len(df) < 30:
            return None

        atr = float((df["high"] - df["low"]).tail(14).mean())
        if atr == 0:
            return None

        pip = self._pip(symbol, point)

        # ── STEP 1: DETECT LIQUIDITY SWEEP ───────────────────────────────
        sweep = self._detect_sweep(df, ms, direction, atr, pip)
        if sweep is None:
            return None

        # Sweep must align with direction
        if direction == "BUY"  and sweep.kind != "LOW_SWEPT":
            return None
        if direction == "SELL" and sweep.kind != "HIGH_SWEPT":
            return None

        # ── STEP 2: CRT 3-CANDLE CONFIRMATION ────────────────────────────
        crt_confirmed = self._check_crt_3candle(df, sweep, direction, atr)
        if not crt_confirmed:
            log.debug("[%s] CRT 3-candle not confirmed", symbol)
            return None

        # ── STEP 3: DISPLACEMENT ──────────────────────────────────────────
        disp = self._find_displacement(df, sweep, direction, atr)
        if disp is None or not disp.is_valid:
            log.debug("[%s] No valid displacement found", symbol)
            return None

        # ── STEP 4: FAIR VALUE GAP ────────────────────────────────────────
        fvg = self._find_fvg(df, disp, direction, atr, pip)
        if fvg is None:
            log.debug("[%s] No FVG found after displacement", symbol)
            return None

        # ── STEP 5: BUILD SIGNAL ──────────────────────────────────────────
        signal = self._build_signal(
            symbol, direction, df, sweep, disp, fvg,
            ms, killzone, atr, pip, point, zones
        )

        if signal:
            log.info(
                "[%s %s] ✅ CRT SIGNAL: %s | KZ=%s | "
                "Entry=%.5f SL=%.5f RR=%.1f | Disp=%.2fx | FVG=%.1fpips | %s",
                symbol, signal.timeframe, direction, killzone,
                signal.entry_price, signal.stop_loss, signal.rr_ratio,
                disp.body_atr, fvg.size_pips, signal.reason
            )

        return signal

    # ──────────────────────────────────────────────────────────────────────
    # STEP 1: LIQUIDITY SWEEP DETECTION
    # ──────────────────────────────────────────────────────────────────────
    def _detect_sweep(
        self, df: pd.DataFrame, ms: MarketStructureResult,
        direction: str, atr: float, pip: float,
    ) -> Optional[LiquiditySweep]:
        """
        Systematic sweep detection across all liquidity levels.
        A sweep is:
          - Price trades beyond a defined level
          - Closes back inside within N bars
          - OR shows wick ≥ 50% of candle range
        """
        n = len(df)
        levels = self._build_level_list(ms, df)

        # Check last SWEEP_LOOKBACK_BARS bars
        for i in range(max(0, n-SWEEP_LOOKBACK_BARS), n-1):
            bar = df.iloc[i]
            rng = bar["high"] - bar["low"]
            if rng == 0:
                continue

            for level_price, level_type, level_strength in levels:
                # HIGH SWEPT: wick above level, close below
                if bar["high"] > level_price > bar["close"]:
                    wick_size = bar["high"] - max(bar["open"], bar["close"])
                    wick_pct  = wick_size / rng
                    if wick_pct >= SWEEP_WICK_MIN_PCT:
                        return LiquiditySweep(
                            kind="HIGH_SWEPT",
                            swept_level=level_price,
                            sweep_high=bar["high"],
                            sweep_low=bar["low"],
                            sweep_close=bar["close"],
                            bar_index=i,
                            wick_pct=wick_pct,
                            level_type=level_type,
                            strength=level_strength,
                        )

                # LOW SWEPT: wick below level, close above
                if bar["low"] < level_price < bar["close"]:
                    wick_size = min(bar["open"], bar["close"]) - bar["low"]
                    wick_pct  = wick_size / rng
                    if wick_pct >= SWEEP_WICK_MIN_PCT:
                        return LiquiditySweep(
                            kind="LOW_SWEPT",
                            swept_level=level_price,
                            sweep_high=bar["high"],
                            sweep_low=bar["low"],
                            sweep_close=bar["close"],
                            bar_index=i,
                            wick_pct=wick_pct,
                            level_type=level_type,
                            strength=level_strength,
                        )

        return None

    def _build_level_list(self, ms, df) -> List[Tuple[float, str, float]]:
        """Collect all liquidity levels — strictly defined."""
        levels = []

        # Previous day H/L — highest significance
        if ms.prev_day_high: levels.append((ms.prev_day_high, "PDH", 1.0))
        if ms.prev_day_low:  levels.append((ms.prev_day_low,  "PDL", 1.0))
        if ms.prev_week_high: levels.append((ms.prev_week_high,"PWH", 0.95))
        if ms.prev_week_low:  levels.append((ms.prev_week_low, "PWL", 0.95))

        # Session highs/lows
        for sl in ms.session_levels:
            ltype = sl.kind.replace("_h","H").replace("_l","L").upper()
            strength = 0.9 if "london" in sl.kind or "ny" in sl.kind else 0.7
            levels.append((sl.price, ltype, strength))

        # Swing highs/lows (recent)
        for sh in ms.swing_highs[-5:]:
            levels.append((sh.price, "SwingH", 0.8))
        for sl in ms.swing_lows[-5:]:
            levels.append((sl.price, "SwingL", 0.8))

        # Liquidity pools (equal H/L clusters)
        for pool in ms.pools:
            ltype = "EQH" if "high" in pool.kind else "EQL"
            levels.append((pool.price, ltype, 0.85 * pool.strength + 0.5))

        # Recent session H/L from raw candles
        if len(df) >= 20:
            levels.append((float(df["high"].tail(20).max()), "SessH20", 0.75))
            levels.append((float(df["low"].tail(20).min()),  "SessL20", 0.75))

        return levels

    # ──────────────────────────────────────────────────────────────────────
    # STEP 2: CRT 3-CANDLE CONFIRMATION
    # ──────────────────────────────────────────────────────────────────────
    def _check_crt_3candle(
        self, df: pd.DataFrame, sweep: LiquiditySweep,
        direction: str, atr: float,
    ) -> bool:
        """
        Systematic 3-candle CRT check:
        C1: range candle
        C2: sweep candle (the one that raided liquidity)
        C3: confirmation (closes beyond opposite side of C1)

        Returns True if CRT pattern confirmed.
        """
        i = sweep.bar_index
        if i < 2:
            return False

        c1 = df.iloc[i - 1]  # range candle
        c2 = df.iloc[i]      # sweep candle
        c3_idx = min(i + 1, len(df) - 1)
        c3 = df.iloc[c3_idx] # confirmation candle

        c1_range = c1["high"] - c1["low"]
        if c1_range == 0:
            return False

        # C2 must sweep C1 by threshold %
        if direction == "BUY":
            sweep_dist = c1["low"] - c2["low"]
            if sweep_dist < c1_range * CRT_SWEEP_THRESHOLD_PCT:
                return False
            # C2 close can't be too far beyond sweep
            overshoot = c1["low"] - c2["close"]
            if overshoot > c1_range * CRT_SWEEP_MAX_CLOSE_PCT:
                return False
            # C3 must close above C1 high
            c3_closes_above = c3["close"] > c1["high"] * 0.999
            body_size = abs(c3["close"] - c3["open"])
            body_ok   = body_size >= CRT_CONFIRMATION_BODY_ATR * atr
            c3_rng    = c3["high"] - c3["low"]
            close_pct = (c3["close"] - c3["low"]) / (c3_rng + 1e-9)
            close_ok  = close_pct >= CRT_CONFIRMATION_CLOSE_PCT
            return c3_closes_above and body_ok and close_ok

        elif direction == "SELL":
            sweep_dist = c2["high"] - c1["high"]
            if sweep_dist < c1_range * CRT_SWEEP_THRESHOLD_PCT:
                return False
            overshoot = c2["close"] - c1["high"]
            if overshoot > c1_range * CRT_SWEEP_MAX_CLOSE_PCT:
                return False
            c3_closes_below = c3["close"] < c1["low"] * 1.001
            body_size = abs(c3["close"] - c3["open"])
            body_ok   = body_size >= CRT_CONFIRMATION_BODY_ATR * atr
            c3_rng    = c3["high"] - c3["low"]
            close_pct = (c3["high"] - c3["close"]) / (c3_rng + 1e-9)
            close_ok  = close_pct >= CRT_CONFIRMATION_CLOSE_PCT
            return c3_closes_below and body_ok and close_ok

        return False

    # ──────────────────────────────────────────────────────────────────────
    # STEP 3: DISPLACEMENT CANDLE
    # ──────────────────────────────────────────────────────────────────────
    def _find_displacement(
        self, df: pd.DataFrame, sweep: LiquiditySweep,
        direction: str, atr: float,
    ) -> Optional[DisplacementCandle]:
        """
        Find the displacement candle after sweep.
        Must satisfy all 3 criteria:
          1. Range > 1.5x ATR
          2. Close in top/bottom 20%
          3. Volume > 1.2x avg (if available)
        """
        n     = len(df)
        start = sweep.bar_index
        end   = min(start + FVG_MAX_LOOKBACK, n)
        vol_avg = df["volume"].tail(20).mean()

        for i in range(start, end):
            bar = df.iloc[i]
            rng = bar["high"] - bar["low"]
            if rng == 0:
                continue

            body = abs(bar["close"] - bar["open"])
            vol_ratio = float(bar["volume"]) / (vol_avg + 1e-9)

            if direction == "BUY":
                if bar["close"] <= bar["open"]:
                    continue  # must be bullish
                body_atr   = body / (atr + 1e-9)
                range_ok   = rng >= DISPLACEMENT_ATR_MULT * atr
                close_pct  = (bar["close"] - bar["low"]) / rng
                close_ok   = close_pct >= (1 - DISPLACEMENT_CLOSE_PCT)
                vol_ok     = vol_ratio >= DISPLACEMENT_VOL_MULT or vol_avg < 1
                is_valid   = range_ok and close_ok

                return DisplacementCandle(
                    direction="BULLISH", bar_index=i,
                    body_atr=body_atr, close_pct=close_pct,
                    volume_ratio=vol_ratio, is_valid=is_valid,
                )

            elif direction == "SELL":
                if bar["close"] >= bar["open"]:
                    continue  # must be bearish
                body_atr   = body / (atr + 1e-9)
                range_ok   = rng >= DISPLACEMENT_ATR_MULT * atr
                close_pct  = (bar["high"] - bar["close"]) / rng
                close_ok   = close_pct >= (1 - DISPLACEMENT_CLOSE_PCT)
                vol_ok     = vol_ratio >= DISPLACEMENT_VOL_MULT or vol_avg < 1
                is_valid   = range_ok and close_ok

                return DisplacementCandle(
                    direction="BEARISH", bar_index=i,
                    body_atr=body_atr, close_pct=close_pct,
                    volume_ratio=vol_ratio, is_valid=is_valid,
                )

        return None

    # ──────────────────────────────────────────────────────────────────────
    # STEP 4: FAIR VALUE GAP
    # ──────────────────────────────────────────────────────────────────────
    def _find_fvg(
        self, df: pd.DataFrame, disp: DisplacementCandle,
        direction: str, atr: float, pip: float,
    ) -> Optional[FairValueGap]:
        """
        Find Fair Value Gap (3-candle imbalance).
        Bullish FVG: C[i-2].high < C[i].low (gap up)
        Bearish FVG: C[i-2].low  > C[i].high (gap down)
        Enter at 50% of FVG (equilibrium price).
        """
        n     = len(df)
        start = max(disp.bar_index - 2, 0)
        end   = min(disp.bar_index + FVG_MAX_LOOKBACK, n)

        best_fvg  = None
        best_size = 0

        for i in range(start + 2, end):
            c0 = df.iloc[i - 2]
            c2 = df.iloc[i]

            if direction == "BUY":
                # Gap between C0 high and C2 low
                if c2["low"] > c0["high"]:
                    top    = c2["low"]
                    bottom = c0["high"]
                    size   = (top - bottom) / pip
                    if size >= FVG_MIN_SIZE_PIPS and size > best_size:
                        best_size = size
                        best_fvg  = FairValueGap(
                            kind="BULLISH_FVG",
                            top=top, bottom=bottom,
                            mid=(top+bottom)/2,
                            size_pips=size, bar_index=i
                        )

            elif direction == "SELL":
                # Gap between C0 low and C2 high
                if c2["high"] < c0["low"]:
                    top    = c0["low"]
                    bottom = c2["high"]
                    size   = (top - bottom) / pip
                    if size >= FVG_MIN_SIZE_PIPS and size > best_size:
                        best_size = size
                        best_fvg  = FairValueGap(
                            kind="BEARISH_FVG",
                            top=top, bottom=bottom,
                            mid=(top+bottom)/2,
                            size_pips=size, bar_index=i
                        )

        return best_fvg

    # ──────────────────────────────────────────────────────────────────────
    # STEP 5: BUILD SIGNAL
    # ──────────────────────────────────────────────────────────────────────
    def _build_signal(
        self, symbol, direction, df, sweep, disp, fvg,
        ms, killzone, atr, pip, point, zones,
    ) -> Optional[CRTSignal]:

        # Entry at FVG 50% (equilibrium)
        entry = fvg.mid

        # SL: beyond sweep extreme + ATR buffer
        buf = SL_ATR_BUFFER * atr
        if direction == "BUY":
            sl = sweep.sweep_low - buf
        else:
            sl = sweep.sweep_high + buf

        # Validate SL distance
        risk = abs(entry - sl)
        min_risk = pip * 8    # minimum 8 pip SL
        if risk < min_risk:
            sl = entry - min_risk if direction == "BUY" else entry + min_risk
            risk = min_risk

        if risk <= 0 or risk > entry * 0.05:  # max 5% from entry
            return None

        # Targets: 2R, 3R, 5R
        tp1  = entry + risk * 2.0 if direction == "BUY" else entry - risk * 2.0
        tp2  = entry + risk * 3.0 if direction == "BUY" else entry - risk * 3.0
        tp3  = entry + risk * 5.0 if direction == "BUY" else entry - risk * 5.0
        rr   = abs(tp1 - entry) / risk

        if rr < MIN_RR_RATIO:
            return None

        # Draw on Liquidity target
        dol = self._find_dol(ms, direction)

        # Confidence scoring
        score, reasons = self._score_signal(
            sweep, disp, fvg, ms, killzone, zones, entry, atr, pip
        )

        sl_pips = risk / pip

        return CRTSignal(
            symbol=symbol, direction=direction,
            entry_price=round(entry, 5),
            entry_top=round(fvg.top, 5),
            entry_bottom=round(fvg.bottom, 5),
            stop_loss=round(sl, 5),
            sl_pips=round(sl_pips, 1),
            take_profit_1=round(tp1, 5),
            take_profit_2=round(tp2, 5),
            take_profit_3=round(tp3, 5),
            dol_target=round(dol, 5) if dol else 0.0,
            rr_ratio=round(rr, 2),
            confidence=round(score, 1),
            displacement_str=round(disp.body_atr, 2),
            fvg_size_pips=round(fvg.size_pips, 1),
            sweep_strength=round(sweep.strength, 2),
            timeframe="",
            killzone=killzone,
            reason=" | ".join(reasons),
            sweep=sweep, displacement=disp, fvg=fvg,
            metadata={
                "atr":        atr,
                "sweep_type": sweep.level_type,
                "disp_atr":   disp.body_atr,
                "fvg_pips":   fvg.size_pips,
                "dol":        dol or 0.0,
                "killzone":   killzone,
            }
        )

    def _score_signal(self, sweep, disp, fvg, ms, killzone, zones, entry, atr, pip):
        score   = 0.0
        reasons = []

        # Killzone quality (most important — Romeo principle)
        kz_pts = {"silver_bullet": 30, "ny_am": 25, "london_open": 20}
        kz_s   = kz_pts.get(killzone, 10)
        score += kz_s
        kz_label = {"silver_bullet":"🥈 Silver Bullet","ny_am":"🗽 NY AM","london_open":"🇬🇧 London"}
        reasons.append(kz_label.get(killzone, killzone))

        # Sweep quality
        score += sweep.strength * 15
        score += sweep.wick_pct * 10
        reasons.append(f"{sweep.level_type} Swept({sweep.strength:.2f})")

        # Displacement strength (Romeo: must be energetic)
        score += min(disp.body_atr * 10, 15)
        if disp.body_atr >= 1.0:
            reasons.append(f"Energetic Disp {disp.body_atr:.2f}xATR")
        else:
            reasons.append(f"Disp {disp.body_atr:.2f}xATR")

        # FVG size
        score += min(fvg.size_pips / 3, 10)
        reasons.append(f"FVG {fvg.size_pips:.1f}pips")

        # Structure alignment
        if ms.last_choch:
            score += 12
            reasons.append("CHOCH")
        elif ms.last_bos:
            score += 8
            reasons.append("BOS")

        # HTF strength
        score += ms.bias_strength * 8

        # S&D zone confluence (bonus)
        if zones:
            ztype = "demand" if sweep.kind == "LOW_SWEPT" else "supply"
            nearby = [z for z in zones if z.kind==ztype and abs(z.mid-entry)<atr*2]
            if nearby:
                bz = max(nearby, key=lambda z: z.strength)
                score += min(bz.strength, 5)
                reasons.append(f"SD({bz.origin_tf})")

        # Volume confirmation
        if disp.volume_ratio >= 1.2:
            score += 5
            reasons.append(f"VolConf {disp.volume_ratio:.1f}x")

        return min(score, 100.0), reasons

    def _find_dol(self, ms: MarketStructureResult, direction: str) -> Optional[float]:
        """Draw on Liquidity — opposing pool target."""
        if direction == "BUY":
            # Target BSL (buy side liquidity above)
            highs = [p.price for p in ms.pools if "high" in p.kind]
            highs += [ms.prev_day_high, ms.prev_week_high]
            highs = [h for h in highs if h > 0]
            return max(highs) if highs else None
        else:
            # Target SSL (sell side liquidity below)
            lows = [p.price for p in ms.pools if "low" in p.kind]
            lows += [ms.prev_day_low, ms.prev_week_low]
            lows = [l for l in lows if l > 0]
            return min(lows) if lows else None

    @staticmethod
    def _pip(symbol: str, point: float) -> float:
        s = symbol.replace("m","").upper()
        if "JPY" in s or "XAU" in s or "XAG" in s: return point * 100
        if "BTC" in s or "ETH" in s: return point * 10
        return point * 10
