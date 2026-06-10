"""
==============================================================================
ROMEO ICT STRATEGY ENGINE
==============================================================================
Based on RomeoTPT / ICT 2022 Model

Core Philosophy: "Liquidity is Fuel"
Market moves to:
  1. Hunt liquidity (stop raids on retail traders)
  2. Rebalance inefficiencies (Fair Value Gaps)

Entry Model:
  Step A: HTF Bias (where is price going?)
  Step B: Liquidity Purge (PDH/PDL/Session High/Low swept)
  Step C: Market Structure Shift with DISPLACEMENT (aggressive snap)
  Step D: FVG entry (limit order at gap, SL above/below sweep candle)

Time Macros (EST):
  London Open:    02:00 - 05:00 EST
  NY AM Session:  08:30 - 11:00 EST  ← Primary focus
  Silver Bullet:  10:00 - 11:00 EST  ← Highest quality

Draw on Liquidity (DOL):
  If swept a low → target opposing high (ERL to IRL)
  If swept a high → target opposing low (ERL to IRL)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from core.logger import get_logger
from config.settings import MIN_RR_RATIO

log = get_logger("strategy.romeo_ict")


# ── TIME MACROS (EST = UTC-5, or UTC-4 during DST) ────────────────────────
# We work in UTC and convert
KILLZONES_UTC = {
    "london_open":   (7,  10),    # 02:00-05:00 EST = 07:00-10:00 UTC
    "ny_am":         (13, 16),    # 08:30-11:00 EST = 13:30-16:00 UTC
    "silver_bullet": (15, 16),    # 10:00-11:00 EST = 15:00-16:00 UTC
}

# DST adjustment (March-Nov = EDT = UTC-4)
KILLZONES_UTC_DST = {
    "london_open":   (6,  9),
    "ny_am":         (12, 15),
    "silver_bullet": (14, 15),
}

# Minimum displacement to confirm MSS — ATR multiplier
DISPLACEMENT_MIN_ATR = 0.8   # move must be >= 0.8 * ATR to be "energetic"
DISPLACEMENT_CHOPPY_MAX = 0.4  # if < 0.4 * ATR, it's choppy — skip

# FVG parameters
FVG_MIN_SIZE_ATR  = 0.1      # minimum FVG size relative to ATR
FVG_MAX_LOOKBACK  = 10       # look back N bars for FVG after MSS

# SL buffer — pips beyond sweep candle
SL_BUFFER_PIPS = {
    "DEFAULT": 3,
    "JPY":     5,
    "XAU":     50,
    "XAG":     20,
    "BTC":     200,
    "ETH":     80,
}


def _pip_size(symbol: str, point: float) -> float:
    s = symbol.replace("m","").upper()
    if "JPY" in s:  return point * 100
    if "XAU" in s or "XAG" in s: return point * 100
    if "BTC" in s or "ETH" in s: return point * 10
    return point * 10


def _sl_buffer(symbol: str, point: float) -> float:
    s = symbol.replace("m","").upper()
    pip = _pip_size(symbol, point)
    if "JPY" in s: return SL_BUFFER_PIPS["JPY"] * pip
    if "XAU" in s: return SL_BUFFER_PIPS["XAU"] * pip
    if "XAG" in s: return SL_BUFFER_PIPS["XAG"] * pip
    if "BTC" in s: return SL_BUFFER_PIPS["BTC"] * pip
    if "ETH" in s: return SL_BUFFER_PIPS["ETH"] * pip
    return SL_BUFFER_PIPS["DEFAULT"] * pip


def _is_dst() -> bool:
    """Approximate DST check (March-November)."""
    month = datetime.utcnow().month
    return 3 <= month <= 11


def get_current_killzone() -> Optional[str]:
    """Return current killzone name or None if outside."""
    hour = datetime.utcnow().hour
    zones = KILLZONES_UTC_DST if _is_dst() else KILLZONES_UTC
    for name, (start, end) in zones.items():
        if start <= hour < end:
            return name
    return None


def is_in_killzone() -> bool:
    return get_current_killzone() is not None


# ──────────────────────────────────────────────────────────────────────────
@dataclass
class FairValueGap:
    """A three-candle FVG — gap between candle[0].high and candle[2].low (bullish)
    or candle[0].low and candle[2].high (bearish)."""
    kind:       str      # "bullish" | "bearish"
    top:        float
    bottom:     float
    bar_index:  int
    size_pips:  float
    filled:     bool = False

    @property
    def mid(self): return (self.top + self.bottom) / 2

    @property
    def entry_price(self):
        """Entry at 50% of FVG (equilibrium)."""
        return self.mid

    @property
    def entry_top(self):
        """Conservative entry — top of FVG for bearish, bottom for bullish."""
        return self.top if self.kind == "bullish" else self.bottom


@dataclass
class LiquiditySweep:
    kind:       str     # "HIGH_SWEPT" | "LOW_SWEPT"
    level:      float   # the level that was swept
    sweep_high: float   # high of sweep candle
    sweep_low:  float   # low of sweep candle
    bar_index:  int
    strength:   float   # 0-1 (how significant the level was)


@dataclass
class MarketStructureShift:
    direction:    str    # "BULLISH" | "BEARISH"
    break_price:  float  # price level that was broken
    displacement: float  # size of displacement move in ATR units
    bar_index:    int
    energetic:    bool   # True if displacement > DISPLACEMENT_MIN_ATR


@dataclass
class RomeoSignal:
    symbol:         str
    direction:      str        # "BUY" | "SELL"
    entry_price:    float      # at FVG 50% level
    stop_loss:      float      # beyond sweep candle + buffer
    take_profit_1:  float      # 2R
    take_profit_2:  float      # 3R
    take_profit_3:  float      # 5R (Draw on Liquidity target)
    rr_ratio:       float
    confidence:     float      # 0-100
    ai_score:       float = 0.0
    timeframe:      str   = ""
    signal_time:    datetime = field(default_factory=datetime.utcnow)
    reason:         str   = ""
    zone:           object = None
    fvg:            Optional[FairValueGap] = None
    sweep:          Optional[LiquiditySweep] = None
    mss:            Optional[MarketStructureShift] = None
    killzone:       str   = ""
    dol_target:     float = 0.0   # Draw on Liquidity target
    metadata:       Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
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
        }


# ──────────────────────────────────────────────────────────────────────────
class RomeoICTStrategy:
    """
    Romeo ICT / ICT 2022 Model implementation.

    Signal generation sequence:
    1. Confirm killzone (time window)
    2. Detect liquidity sweep (PDH/PDL or session H/L swept)
    3. Confirm MSS with displacement (energetic move)
    4. Find FVG left by displacement
    5. Set entry, SL, targets
    """

    def generate_signal(
        self,
        symbol:             str,
        higher_tf_bias:     str,    # "bullish" | "bearish" | "neutral"
        higher_tf_strength: float,
        current_price:      float,
        point:              float,
        df_htf:             pd.DataFrame,   # H1 or H4 for context
        df_entry:           pd.DataFrame,   # M5 or M15 for entry
        entry_tf:           str,
        zones:              list = None,    # S&D zones as confluence
    ) -> Optional[RomeoSignal]:

        if higher_tf_bias == "neutral" or higher_tf_strength < 0.35:
            return None

        if df_entry is None or len(df_entry) < 30:
            return None

        # ── STEP 1: KILLZONE CHECK ────────────────────────────────────────
        killzone = get_current_killzone()
        if killzone is None:
            log.debug("[%s] Outside killzone — skip", symbol)
            return None

        atr = float((df_entry["high"]-df_entry["low"]).tail(14).mean())
        if atr == 0: return None

        pip = _pip_size(symbol, point)

        # ── STEP 2: LIQUIDITY SWEEP DETECTION ────────────────────────────
        sweep = self._detect_liquidity_sweep(df_htf, df_entry, atr, symbol)
        if sweep is None:
            log.debug("[%s] No liquidity sweep found", symbol)
            return None

        # Sweep must align with HTF bias
        # If bullish → looking for LOW swept (trap for sellers, price goes up)
        # If bearish → looking for HIGH swept (trap for buyers, price goes down)
        if higher_tf_bias == "bullish" and sweep.kind != "LOW_SWEPT":
            return None
        if higher_tf_bias == "bearish" and sweep.kind != "HIGH_SWEPT":
            return None

        # ── STEP 3: MSS WITH DISPLACEMENT ────────────────────────────────
        direction = "BUY" if higher_tf_bias == "bullish" else "SELL"
        mss = self._detect_mss(df_entry, direction, sweep, atr)
        if mss is None:
            log.debug("[%s] No MSS found after sweep", symbol)
            return None

        if not mss.energetic:
            log.debug("[%s] MSS not energetic (choppy) — skip", symbol)
            return None

        # ── STEP 4: FAIR VALUE GAP ────────────────────────────────────────
        fvg = self._find_fvg(df_entry, direction, mss, atr, pip)
        if fvg is None:
            log.debug("[%s] No FVG found after MSS", symbol)
            return None

        # ── STEP 5: BUILD SIGNAL ──────────────────────────────────────────
        signal = self._build_signal(
            symbol, direction, current_price, fvg, sweep, mss,
            higher_tf_strength, killzone, atr, pip, point,
            entry_tf, zones, df_htf
        )

        if signal:
            log.info(
                "[%s %s] ✅ ROMEO SIGNAL: %s | Killzone=%s | "
                "Entry=%.5f SL=%.5f TP1=%.5f RR=%.1f | %s",
                symbol, entry_tf, signal.direction, killzone,
                signal.entry_price, signal.stop_loss,
                signal.take_profit_1, signal.rr_ratio, signal.reason
            )

        return signal

    # ──────────────────────────────────────────────────────────────────────
    # STEP 2: LIQUIDITY SWEEP DETECTION
    # ──────────────────────────────────────────────────────────────────────
    def _detect_liquidity_sweep(
        self,
        df_htf:   pd.DataFrame,
        df_entry: pd.DataFrame,
        atr:      float,
        symbol:   str,
    ) -> Optional[LiquiditySweep]:
        """
        Detect if price recently swept:
        - Previous Day High/Low (PDH/PDL)
        - Session High/Low
        - Old Swing High/Low
        """
        df = df_entry
        n  = len(df)
        if n < 20: return None

        # Define key liquidity levels from HTF
        levels = self._get_liquidity_levels(df_htf, df_entry)

        # Check last 10 bars for sweeps
        check_bars = min(10, n - 5)
        for i in range(n - check_bars, n - 1):
            bar = df.iloc[i]
            next_bar = df.iloc[i + 1] if i + 1 < n else None

            for level_price, level_strength, level_type in levels:
                # High swept: wick above level but close below
                if (bar["high"] > level_price and
                        bar["close"] < level_price):
                    # Confirm: next bar also below level
                    return LiquiditySweep(
                        kind="HIGH_SWEPT",
                        level=level_price,
                        sweep_high=bar["high"],
                        sweep_low=bar["low"],
                        bar_index=i,
                        strength=level_strength,
                    )

                # Low swept: wick below level but close above
                if (bar["low"] < level_price and
                        bar["close"] > level_price):
                    return LiquiditySweep(
                        kind="LOW_SWEPT",
                        level=level_price,
                        sweep_high=bar["high"],
                        sweep_low=bar["low"],
                        bar_index=i,
                        strength=level_strength,
                    )

        return None

    def _get_liquidity_levels(
        self,
        df_htf:   pd.DataFrame,
        df_entry: pd.DataFrame,
    ) -> List[Tuple[float, float, str]]:
        """
        Return (price, strength, label) for key liquidity levels.
        Higher strength = more significant.
        """
        levels = []
        if df_htf is not None and len(df_htf) >= 5:
            # Previous session high/low (last 2 HTF candles)
            pdh = df_htf["high"].iloc[-2]
            pdl = df_htf["low"].iloc[-2]
            levels.append((pdh, 0.9, "PDH"))
            levels.append((pdl, 0.9, "PDL"))

            # Previous 5-bar swing highs/lows
            swing_high = df_htf["high"].tail(10).max()
            swing_low  = df_htf["low"].tail(10).min()
            levels.append((swing_high, 0.8, "SwingH"))
            levels.append((swing_low,  0.8, "SwingL"))

        if df_entry is not None and len(df_entry) >= 20:
            # Session high/low from entry TF
            sess_high = df_entry["high"].tail(20).max()
            sess_low  = df_entry["low"].tail(20).min()
            levels.append((sess_high, 0.7, "SessH"))
            levels.append((sess_low,  0.7, "SessL"))

            # Equal highs/lows (retail clusters)
            highs = df_entry["high"].tail(30).values
            lows  = df_entry["low"].tail(30).values
            for j in range(len(highs)-1):
                for k in range(j+1, min(j+5, len(highs))):
                    if abs(highs[j]-highs[k]) / (highs[j]+1e-9) < 0.0002:
                        levels.append(((highs[j]+highs[k])/2, 0.85, "EQH"))
                    if abs(lows[j]-lows[k]) / (lows[j]+1e-9) < 0.0002:
                        levels.append(((lows[j]+lows[k])/2, 0.85, "EQL"))

        return levels

    # ──────────────────────────────────────────────────────────────────────
    # STEP 3: MARKET STRUCTURE SHIFT WITH DISPLACEMENT
    # ──────────────────────────────────────────────────────────────────────
    def _detect_mss(
        self,
        df:        pd.DataFrame,
        direction: str,
        sweep:     LiquiditySweep,
        atr:       float,
    ) -> Optional[MarketStructureShift]:
        """
        After sweep, look for aggressive displacement breaking structure.
        - Direction BUY: price broke above a recent swing high aggressively
        - Direction SELL: price broke below a recent swing low aggressively
        """
        n = len(df)
        start = max(sweep.bar_index + 1, 0)
        end   = min(start + FVG_MAX_LOOKBACK, n)

        if start >= n: return None

        for i in range(start, end):
            bar = df.iloc[i]
            bar_size = bar["high"] - bar["low"]

            if direction == "BUY":
                # Looking for a strong bullish candle breaking a swing high
                body = bar["close"] - bar["open"]
                if body <= 0: continue  # must be bullish candle

                # Check if this candle breaks above recent high (pre-sweep)
                lookback_high = df["high"].iloc[max(0,sweep.bar_index-5):sweep.bar_index].max()

                if bar["close"] > lookback_high:
                    displacement = body / (atr + 1e-9)
                    energetic    = displacement >= DISPLACEMENT_MIN_ATR
                    choppy       = displacement < DISPLACEMENT_CHOPPY_MAX

                    if choppy:
                        log.debug("MSS found but choppy (disp=%.2f) — skip", displacement)
                        continue

                    return MarketStructureShift(
                        direction="BULLISH",
                        break_price=lookback_high,
                        displacement=displacement,
                        bar_index=i,
                        energetic=energetic,
                    )

            elif direction == "SELL":
                body = bar["open"] - bar["close"]
                if body <= 0: continue  # must be bearish candle

                lookback_low = df["low"].iloc[max(0,sweep.bar_index-5):sweep.bar_index].min()

                if bar["close"] < lookback_low:
                    displacement = body / (atr + 1e-9)
                    energetic    = displacement >= DISPLACEMENT_MIN_ATR
                    choppy       = displacement < DISPLACEMENT_CHOPPY_MAX

                    if choppy:
                        continue

                    return MarketStructureShift(
                        direction="BEARISH",
                        break_price=lookback_low,
                        displacement=displacement,
                        bar_index=i,
                        energetic=energetic,
                    )

        return None

    # ──────────────────────────────────────────────────────────────────────
    # STEP 4: FAIR VALUE GAP DETECTION
    # ──────────────────────────────────────────────────────────────────────
    def _find_fvg(
        self,
        df:        pd.DataFrame,
        direction: str,
        mss:       MarketStructureShift,
        atr:       float,
        pip:       float,
    ) -> Optional[FairValueGap]:
        """
        Find FVG in the displacement candles after the MSS.
        Bullish FVG: candle[i].low > candle[i-2].high (gap up)
        Bearish FVG: candle[i].high < candle[i-2].low (gap down)
        """
        n     = len(df)
        start = max(mss.bar_index - 2, 0)
        end   = min(mss.bar_index + FVG_MAX_LOOKBACK, n)

        best_fvg = None
        best_size = 0

        for i in range(start + 2, end):
            c0 = df.iloc[i - 2]   # first candle
            c1 = df.iloc[i - 1]   # middle candle (FVG body)
            c2 = df.iloc[i]       # third candle

            if direction == "BUY":
                # Bullish FVG: c2.low > c0.high
                if c2["low"] > c0["high"]:
                    fvg_top    = c2["low"]
                    fvg_bottom = c0["high"]
                    size_pips  = (fvg_top - fvg_bottom) / pip

                    if size_pips < FVG_MIN_SIZE_ATR * atr / pip:
                        continue  # FVG too small

                    if size_pips > best_size:
                        best_size = size_pips
                        best_fvg  = FairValueGap(
                            kind="bullish",
                            top=fvg_top,
                            bottom=fvg_bottom,
                            bar_index=i,
                            size_pips=size_pips,
                        )

            elif direction == "SELL":
                # Bearish FVG: c2.high < c0.low
                if c2["high"] < c0["low"]:
                    fvg_top    = c0["low"]
                    fvg_bottom = c2["high"]
                    size_pips  = (fvg_top - fvg_bottom) / pip

                    if size_pips < FVG_MIN_SIZE_ATR * atr / pip:
                        continue

                    if size_pips > best_size:
                        best_size = size_pips
                        best_fvg  = FairValueGap(
                            kind="bearish",
                            top=fvg_top,
                            bottom=fvg_bottom,
                            bar_index=i,
                            size_pips=size_pips,
                        )

        return best_fvg

    # ──────────────────────────────────────────────────────────────────────
    # STEP 5: BUILD SIGNAL
    # ──────────────────────────────────────────────────────────────────────
    def _build_signal(
        self,
        symbol:      str,
        direction:   str,
        cur_price:   float,
        fvg:         FairValueGap,
        sweep:       LiquiditySweep,
        mss:         MarketStructureShift,
        htf_strength:float,
        killzone:    str,
        atr:         float,
        pip:         float,
        point:       float,
        entry_tf:    str,
        zones:       list,
        df_htf:      pd.DataFrame,
    ) -> Optional[RomeoSignal]:

        # Entry at 50% of FVG (equilibrium)
        entry = fvg.mid

        # SL: beyond the sweep candle + buffer
        buf = _sl_buffer(symbol, point)
        if direction == "BUY":
            sl   = sweep.sweep_low - buf
        else:
            sl   = sweep.sweep_high + buf

        risk = abs(entry - sl)
        if risk <= 0 or risk > cur_price * 0.1:
            return None

        # Targets
        tp1 = entry + risk * 2.0 if direction == "BUY" else entry - risk * 2.0
        tp2 = entry + risk * 3.0 if direction == "BUY" else entry - risk * 3.0
        tp3 = entry + risk * 5.0 if direction == "BUY" else entry - risk * 5.0

        rr = abs(tp1 - entry) / risk
        if rr < MIN_RR_RATIO:
            return None

        # Draw on Liquidity target (opposing ERL)
        dol = self._find_dol(df_htf, direction)

        # Confidence score
        score = 0.0
        reasons = []

        # Killzone quality
        if killzone == "silver_bullet":
            score += 30
            reasons.append("Silver Bullet")
        elif killzone == "ny_am":
            score += 25
            reasons.append("NY AM Session")
        elif killzone == "london_open":
            score += 20
            reasons.append("London Open")

        # Sweep significance
        score += sweep.strength * 20
        reasons.append(f"{sweep.kind.replace('_',' ')}({sweep.strength:.2f})")

        # Displacement energy
        if mss.energetic:
            score += 15
            reasons.append(f"Displacement({mss.displacement:.1f}x ATR)")
        else:
            score += 8

        # FVG size (bigger = more institutional)
        score += min(fvg.size_pips / 5, 10)
        reasons.append(f"FVG({fvg.size_pips:.1f} pips)")

        # HTF strength
        score += htf_strength * 10

        # S&D Zone confluence (bonus)
        best_zone = None
        if zones:
            zone_type = "demand" if direction == "BUY" else "supply"
            nearby = [z for z in zones
                      if z.kind == zone_type
                      and abs(z.mid - entry) < atr * 3]
            if nearby:
                best_zone = max(nearby, key=lambda z: z.strength)
                score += min(best_zone.strength, 10)
                reasons.append(f"SD Zone({best_zone.origin_tf})")

        score = min(score, 100.0)

        return RomeoSignal(
            symbol=symbol,
            direction=direction,
            entry_price=round(entry, 5),
            stop_loss=round(sl, 5),
            take_profit_1=round(tp1, 5),
            take_profit_2=round(tp2, 5),
            take_profit_3=round(tp3, 5),
            rr_ratio=round(rr, 2),
            confidence=round(score, 1),
            timeframe=entry_tf,
            reason=" | ".join(reasons),
            zone=best_zone,
            fvg=fvg,
            sweep=sweep,
            mss=mss,
            killzone=killzone,
            dol_target=round(dol, 5) if dol else 0.0,
            metadata={
                "htf_strength":    htf_strength,
                "displacement":    mss.displacement,
                "fvg_size_pips":   fvg.size_pips,
                "sweep_level":     sweep.level,
                "sweep_strength":  sweep.strength,
                "killzone":        killzone,
                "dol_target":      dol or 0.0,
            }
        )

    def _find_dol(self, df_htf: pd.DataFrame, direction: str) -> Optional[float]:
        """
        Find the Draw on Liquidity — the opposing ERL price is heading to.
        BUY: target the next clean high above
        SELL: target the next clean low below
        """
        if df_htf is None or len(df_htf) < 5:
            return None
        if direction == "BUY":
            return float(df_htf["high"].tail(20).max())
        else:
            return float(df_htf["low"].tail(20).min())
