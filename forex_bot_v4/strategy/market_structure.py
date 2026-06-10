"""
==============================================================================
MARKET STRUCTURE ENGINE — Fully Systematic, Zero Discretion
==============================================================================
Defines structure via:
  - N-bar fractal pivot swing highs/lows
  - BOS (Break of Structure) = close beyond prior swing
  - CHoCH (Change of Character) = BOS against trend
  - Liquidity pools = equal highs/lows within pip tolerance
  - Session highs/lows (Asia/London/NY)
  - Daily/Weekly highs/lows
  - 50 EMA slope for bias
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from core.logger import get_logger
from config.settings import (
    SWING_PIVOT_BARS, BOS_LOOKBACK, EMA_BIAS_PERIOD,
    EQUAL_LEVEL_TOLERANCE, SESSION_LOOKBACK
)

log = get_logger("strategy.market_structure")


@dataclass
class SwingPoint:
    index:     int
    price:     float
    kind:      str        # "high" | "low"
    timestamp: object     # pd.Timestamp
    strength:  float = 1.0


@dataclass
class LiquidityPool:
    price:     float
    kind:      str        # "high_pool" | "low_pool"
    touches:   int = 2
    swept:     bool = False
    strength:  float = 0.5


@dataclass
class StructureEvent:
    kind:       str       # "BOS_UP"|"BOS_DOWN"|"CHOCH_UP"|"CHOCH_DOWN"
    price:      float
    bar_index:  int
    strength:   float


@dataclass
class SessionLevel:
    kind:   str           # "asia_h"|"asia_l"|"london_h"|"london_l"|"ny_h"|"ny_l"
    price:  float
    swept:  bool = False


@dataclass
class MarketStructureResult:
    # Bias
    bias:           str       # "bullish"|"bearish"|"neutral"
    bias_strength:  float     # 0-1
    ema_slope:      float     # positive=up, negative=down

    # Swings
    swing_highs:    List[SwingPoint] = field(default_factory=list)
    swing_lows:     List[SwingPoint] = field(default_factory=list)

    # Structure
    last_bos:       Optional[StructureEvent] = None
    last_choch:     Optional[StructureEvent] = None
    hh:             bool = False    # higher high formed
    hl:             bool = False    # higher low formed
    lh:             bool = False    # lower high formed
    ll:             bool = False    # lower low formed

    # Liquidity
    pools:          List[LiquidityPool] = field(default_factory=list)
    session_levels: List[SessionLevel]  = field(default_factory=list)

    # Key levels
    prev_day_high:  float = 0.0
    prev_day_low:   float = 0.0
    prev_week_high: float = 0.0
    prev_week_low:  float = 0.0


class MarketStructureEngine:
    """
    Fully systematic market structure analysis.
    All rules are strictly defined — no interpretation.
    """

    def __init__(self, pivot_bars: int = SWING_PIVOT_BARS) -> None:
        self.pivot_bars = pivot_bars

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "",
        tf: str = "",
        df_daily: pd.DataFrame = None,
        df_weekly: pd.DataFrame = None,
    ) -> MarketStructureResult:

        if df is None or len(df) < self.pivot_bars * 2 + 10:
            return MarketStructureResult(bias="neutral", bias_strength=0.0, ema_slope=0.0)

        df = df.tail(BOS_LOOKBACK).copy().reset_index(drop=True)

        # ── 1. SWING DETECTION (N-bar pivot) ─────────────────────────────
        swings_h = self._find_swings(df, "high")
        swings_l = self._find_swings(df, "low")

        # ── 2. HH/HL/LH/LL ───────────────────────────────────────────────
        hh, hl, lh, ll = self._classify(swings_h, swings_l)

        # ── 3. BOS / CHOCH ────────────────────────────────────────────────
        events = self._detect_structure_events(df, swings_h, swings_l)
        last_bos   = next((e for e in reversed(events) if "BOS"   in e.kind), None)
        last_choch = next((e for e in reversed(events) if "CHOCH" in e.kind), None)

        # ── 4. BIAS via EMA + structure ───────────────────────────────────
        ema        = df["close"].ewm(span=EMA_BIAS_PERIOD).mean()
        ema_slope  = float(ema.iloc[-1] - ema.iloc[-5]) / (ema.iloc[-5] + 1e-9) * 100
        bias, strength = self._determine_bias(hh, hl, lh, ll, events, ema_slope)

        # ── 5. LIQUIDITY POOLS ────────────────────────────────────────────
        pools = self._detect_liquidity_pools(df)

        # ── 6. SESSION LEVELS ─────────────────────────────────────────────
        session_levels = self._detect_session_levels(df)

        # ── 7. DAILY / WEEKLY H/L ─────────────────────────────────────────
        pdh = pdl = pwh = pwl = 0.0
        if df_daily is not None and len(df_daily) >= 2:
            pdh = float(df_daily["high"].iloc[-2])
            pdl = float(df_daily["low"].iloc[-2])
        if df_weekly is not None and len(df_weekly) >= 2:
            pwh = float(df_weekly["high"].iloc[-2])
            pwl = float(df_weekly["low"].iloc[-2])

        log.debug("[%s %s] bias=%s strength=%.2f ema_slope=%.4f BOS=%s",
                  symbol, tf, bias, strength, ema_slope,
                  last_bos.kind if last_bos else "None")

        return MarketStructureResult(
            bias=bias, bias_strength=strength, ema_slope=ema_slope,
            swing_highs=swings_h, swing_lows=swings_l,
            last_bos=last_bos, last_choch=last_choch,
            hh=hh, hl=hl, lh=lh, ll=ll,
            pools=pools, session_levels=session_levels,
            prev_day_high=pdh, prev_day_low=pdl,
            prev_week_high=pwh, prev_week_low=pwl,
        )

    # ──────────────────────────────────────────────────────────────────────
    def _find_swings(self, df: pd.DataFrame, col: str) -> List[SwingPoint]:
        """N-bar fractal pivot detection — strict algorithmic definition."""
        swings = []
        n = len(df)
        p = self.pivot_bars
        for i in range(p, n - p):
            val = df[col].iloc[i]
            left  = df[col].iloc[i-p:i]
            right = df[col].iloc[i+1:i+p+1]
            if col == "high":
                if val > left.max() and val > right.max():
                    swings.append(SwingPoint(
                        index=i, price=val, kind="high",
                        timestamp=df.index[i] if hasattr(df.index,'__iter__') else i
                    ))
            else:
                if val < left.min() and val < right.min():
                    swings.append(SwingPoint(
                        index=i, price=val, kind="low",
                        timestamp=df.index[i] if hasattr(df.index,'__iter__') else i
                    ))
        return swings

    def _classify(self, highs, lows) -> Tuple[bool,bool,bool,bool]:
        hh = hl = lh = ll = False
        if len(highs) >= 2:
            hh = highs[-1].price > highs[-2].price
            lh = highs[-1].price < highs[-2].price
        if len(lows) >= 2:
            hl = lows[-1].price > lows[-2].price
            ll = lows[-1].price < lows[-2].price
        return hh, hl, lh, ll

    def _detect_structure_events(
        self, df: pd.DataFrame,
        highs: List[SwingPoint],
        lows:  List[SwingPoint],
    ) -> List[StructureEvent]:
        events = []
        if len(highs) < 2 or len(lows) < 2:
            return events

        close    = df["close"].iloc[-1]
        prev_sh  = highs[-2].price
        prev_sl  = lows[-2].price

        # Quick prior bias
        prior_hh = len(highs) >= 3 and highs[-2].price > highs[-3].price
        prior_hl = len(lows)  >= 3 and lows[-2].price  > lows[-3].price
        prior_bullish = prior_hh or prior_hl

        # BOS / CHOCH UP
        if close > prev_sh:
            kind = "BOS_UP" if prior_bullish else "CHOCH_UP"
            strength = min((close - prev_sh) / (prev_sh * 0.001 + 1e-9), 1.0)
            events.append(StructureEvent(kind=kind, price=prev_sh,
                                         bar_index=len(df)-1, strength=strength))

        # BOS / CHOCH DOWN
        if close < prev_sl:
            kind = "BOS_DOWN" if not prior_bullish else "CHOCH_DOWN"
            strength = min((prev_sl - close) / (prev_sl * 0.001 + 1e-9), 1.0)
            events.append(StructureEvent(kind=kind, price=prev_sl,
                                         bar_index=len(df)-1, strength=strength))

        return events

    def _determine_bias(self, hh, hl, lh, ll, events, ema_slope) -> Tuple[str, float]:
        bull = 0.0
        bear = 0.0

        if hh: bull += 2.0
        if hl: bull += 1.5
        if lh: bear += 2.0
        if ll: bear += 1.5

        for e in events:
            if "UP"   in e.kind: bull += 3.0 if "CHOCH" in e.kind else 2.0
            if "DOWN" in e.kind: bear += 3.0 if "CHOCH" in e.kind else 2.0

        # EMA slope weight
        if ema_slope > 0.01:  bull += 1.5
        elif ema_slope < -0.01: bear += 1.5

        total = bull + bear + 1e-9
        if bull > bear * 1.1:
            return "bullish", min(bull/total, 1.0)
        if bear > bull * 1.1:
            return "bearish", min(bear/total, 1.0)
        return "neutral", 0.5

    def _detect_liquidity_pools(self, df: pd.DataFrame) -> List[LiquidityPool]:
        """Equal highs/lows = retail stop clusters = liquidity pools."""
        pools = []
        highs = df["high"].values
        lows  = df["low"].values
        n     = len(df)
        tol   = EQUAL_LEVEL_TOLERANCE

        for i in range(n-1):
            for j in range(i+1, min(i+15, n)):
                if abs(highs[i]-highs[j]) / (highs[i]+1e-9) < tol:
                    price = (highs[i]+highs[j])/2
                    existing = next((p for p in pools
                                     if p.kind=="high_pool"
                                     and abs(p.price-price)/(price+1e-9)<tol), None)
                    if existing:
                        existing.touches += 1
                        existing.strength = min(existing.touches/5, 1.0)
                    else:
                        pools.append(LiquidityPool(price=price, kind="high_pool"))

                if abs(lows[i]-lows[j]) / (lows[i]+1e-9) < tol:
                    price = (lows[i]+lows[j])/2
                    existing = next((p for p in pools
                                     if p.kind=="low_pool"
                                     and abs(p.price-price)/(price+1e-9)<tol), None)
                    if existing:
                        existing.touches += 1
                        existing.strength = min(existing.touches/5, 1.0)
                    else:
                        pools.append(LiquidityPool(price=price, kind="low_pool"))

        return pools

    def _detect_session_levels(self, df: pd.DataFrame) -> List[SessionLevel]:
        """Detect Asia/London/NY session highs/lows from timestamps."""
        levels = []
        if not hasattr(df.index, 'hour'):
            return levels
        try:
            hour = df.index.hour
            # Asia: 0-8 UTC, London: 7-16 UTC, NY: 12-21 UTC
            for session, (sh, eh) in [("asia",(0,8)),("london",(7,16)),("ny",(12,21))]:
                mask = (hour >= sh) & (hour < eh)
                sess = df[mask].tail(SESSION_LOOKBACK)
                if len(sess) > 0:
                    levels.append(SessionLevel(f"{session}_h", float(sess["high"].max())))
                    levels.append(SessionLevel(f"{session}_l", float(sess["low"].min())))
        except Exception:
            pass
        return levels
