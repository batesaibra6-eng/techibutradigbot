"""
==============================================================================
MARKET STRUCTURE — Analyzer
==============================================================================
Detects:
  • Swing Highs / Swing Lows
  • Higher Highs (HH), Higher Lows (HL), Lower Highs (LH), Lower Lows (LL)
  • Break of Structure (BOS)
  • Change of Character (CHOCH)
  • Internal vs External structure
  • Overall Bias: bullish | bearish | neutral
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np

from core.logger import get_logger
from config.settings import STRUCTURE_LOOKBACK, SWING_SENSITIVITY

log = get_logger("market_structure.analyzer")


@dataclass
class SwingPoint:
    index:    int
    price:    float
    kind:     str       # "high" | "low"
    bar_time: pd.Timestamp


@dataclass
class StructureEvent:
    kind:     str       # "BOS_UP" | "BOS_DOWN" | "CHOCH_UP" | "CHOCH_DOWN"
    price:    float
    bar_time: pd.Timestamp
    strength: float     # 0-1


@dataclass
class MarketStructureResult:
    bias:          str              # "bullish" | "bearish" | "neutral"
    swing_highs:   List[SwingPoint] = field(default_factory=list)
    swing_lows:    List[SwingPoint] = field(default_factory=list)
    hh_list:       List[SwingPoint] = field(default_factory=list)
    hl_list:       List[SwingPoint] = field(default_factory=list)
    lh_list:       List[SwingPoint] = field(default_factory=list)
    ll_list:       List[SwingPoint] = field(default_factory=list)
    events:        List[StructureEvent] = field(default_factory=list)
    last_bos:      Optional[StructureEvent] = None
    last_choch:    Optional[StructureEvent] = None
    strength:      float = 0.0      # 0-1 bias strength


class MarketStructureAnalyzer:
    """Performs full market structure analysis on an OHLCV DataFrame."""

    def __init__(self, sensitivity: int = SWING_SENSITIVITY) -> None:
        self.sensitivity = sensitivity

    # ------------------------------------------------------------------
    def analyze(self, df: pd.DataFrame, symbol: str = "", tf: str = "") -> MarketStructureResult:
        if df is None or len(df) < self.sensitivity * 2 + 5:
            return MarketStructureResult(bias="neutral")

        df = df.tail(STRUCTURE_LOOKBACK).copy()
        df.reset_index(drop=True, inplace=True)

        swing_highs = self._find_swings(df, "high")
        swing_lows  = self._find_swings(df, "low")

        hh, hl, lh, ll = self._classify_swings(swing_highs, swing_lows)
        events         = self._detect_bos_choch(df, swing_highs, swing_lows)
        bias, strength = self._determine_bias(hh, hl, lh, ll, events)

        last_bos   = next((e for e in reversed(events) if "BOS"   in e.kind), None)
        last_choch = next((e for e in reversed(events) if "CHOCH" in e.kind), None)

        log.debug("[%s %s] bias=%s strength=%.2f BOS=%s CHOCH=%s",
                  symbol, tf, bias, strength,
                  last_bos.kind  if last_bos   else "None",
                  last_choch.kind if last_choch else "None")

        return MarketStructureResult(
            bias=bias, strength=strength,
            swing_highs=swing_highs, swing_lows=swing_lows,
            hh_list=hh, hl_list=hl, lh_list=lh, ll_list=ll,
            events=events, last_bos=last_bos, last_choch=last_choch,
        )

    # ------------------------------------------------------------------
    # SWING DETECTION
    # ------------------------------------------------------------------
    def _find_swings(self, df: pd.DataFrame, col: str) -> List[SwingPoint]:
        swings = []
        n = len(df)
        s = self.sensitivity
        for i in range(s, n - s):
            val = df[col].iloc[i]
            window_left  = df[col].iloc[i - s: i]
            window_right = df[col].iloc[i + 1: i + s + 1]
            if col == "high":
                if val >= window_left.max() and val >= window_right.max():
                    swings.append(SwingPoint(
                        index=i, price=val, kind="high",
                        bar_time=df.index[i] if hasattr(df.index, '__iter__') else pd.Timestamp.now()
                    ))
            else:
                if val <= window_left.min() and val <= window_right.min():
                    swings.append(SwingPoint(
                        index=i, price=val, kind="low",
                        bar_time=df.index[i] if hasattr(df.index, '__iter__') else pd.Timestamp.now()
                    ))
        return swings

    # ------------------------------------------------------------------
    # HH / HL / LH / LL CLASSIFICATION
    # ------------------------------------------------------------------
    def _classify_swings(
        self,
        highs: List[SwingPoint],
        lows:  List[SwingPoint],
    ) -> Tuple[List, List, List, List]:
        hh, lh, hl, ll = [], [], [], []

        for i in range(1, len(highs)):
            if highs[i].price > highs[i - 1].price:
                hh.append(highs[i])
            else:
                lh.append(highs[i])

        for i in range(1, len(lows)):
            if lows[i].price > lows[i - 1].price:
                hl.append(lows[i])
            else:
                ll.append(lows[i])

        return hh, hl, lh, ll

    # ------------------------------------------------------------------
    # BOS / CHOCH DETECTION
    # ------------------------------------------------------------------
    def _detect_bos_choch(
        self,
        df: pd.DataFrame,
        highs: List[SwingPoint],
        lows:  List[SwingPoint],
    ) -> List[StructureEvent]:
        events = []
        if len(highs) < 2 or len(lows) < 2:
            return events

        # Last major swing points
        prev_high = highs[-2].price if len(highs) >= 2 else None
        prev_low  = lows[-2].price  if len(lows)  >= 2 else None
        last_close = df["close"].iloc[-1]

        # BOS Up: close breaks above previous swing high
        if prev_high and last_close > prev_high:
            # Distinguish BOS from CHOCH based on prior bias
            prior_bias = self._quick_bias(highs[:-1], lows[:-1])
            kind = "BOS_UP" if prior_bias == "bullish" else "CHOCH_UP"
            events.append(StructureEvent(
                kind=kind, price=prev_high,
                bar_time=df.index[-1],
                strength=min((last_close - prev_high) / (prev_high * 0.001 + 1e-9), 1.0)
            ))

        # BOS Down: close breaks below previous swing low
        if prev_low and last_close < prev_low:
            prior_bias = self._quick_bias(highs[:-1], lows[:-1])
            kind = "BOS_DOWN" if prior_bias == "bearish" else "CHOCH_DOWN"
            events.append(StructureEvent(
                kind=kind, price=prev_low,
                bar_time=df.index[-1],
                strength=min((prev_low - last_close) / (prev_low * 0.001 + 1e-9), 1.0)
            ))

        return events

    # ------------------------------------------------------------------
    # BIAS DETERMINATION
    # ------------------------------------------------------------------
    def _quick_bias(self, highs, lows) -> str:
        if not highs or not lows:
            return "neutral"
        bull = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i-1].price)
        bear = sum(1 for i in range(1, len(lows))  if lows[i].price  < lows[i-1].price)
        if bull > bear:
            return "bullish"
        if bear > bull:
            return "bearish"
        return "neutral"

    def _determine_bias(self, hh, hl, lh, ll, events) -> Tuple[str, float]:
        bull_score = len(hh) * 2 + len(hl)
        bear_score = len(lh) * 2 + len(ll)

        for e in events:
            if "UP" in e.kind:
                bull_score += 3 if "CHOCH" in e.kind else 2
            elif "DOWN" in e.kind:
                bear_score += 3 if "CHOCH" in e.kind else 2

        total = bull_score + bear_score + 1e-9
        if bull_score > bear_score:
            return "bullish", min(bull_score / total, 1.0)
        if bear_score > bull_score:
            return "bearish", min(bear_score / total, 1.0)
        return "neutral", 0.5
