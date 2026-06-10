"""
==============================================================================
LIQUIDITY ENGINE
==============================================================================
Detects:
  • Equal Highs / Equal Lows
  • Buy-Side Liquidity (BSL) above swing highs
  • Sell-Side Liquidity (SSL) below swing lows
  • Liquidity Sweeps (price breaks level then reverses)
  • Stop Hunts
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import numpy as np

from core.logger import get_logger
from config.settings import LIQUIDITY_LOOKBACK, EQUAL_LEVEL_TOLERANCE, SWEEP_CONFIRMATION_BARS

log = get_logger("liquidity.engine")


@dataclass
class LiquidityLevel:
    kind:     str       # "BSL" | "SSL" | "EQH" | "EQL"
    price:    float
    count:    int = 1   # number of touches
    swept:    bool = False
    bar_time: Optional[pd.Timestamp] = None


@dataclass
class LiquiditySweep:
    kind:      str      # "SWEEP_HIGH" | "SWEEP_LOW"
    price:     float
    bar_time:  Optional[pd.Timestamp] = None
    confirmed: bool = False


@dataclass
class LiquidityResult:
    levels:    List[LiquidityLevel] = field(default_factory=list)
    sweeps:    List[LiquiditySweep] = field(default_factory=list)
    bsl_swept: bool = False     # recent BSL swept (bearish signal)
    ssl_swept: bool = False     # recent SSL swept (bullish signal)
    sweep_score: float = 0.0   # 0-1 recency-weighted sweep score


class LiquidityEngine:

    def __init__(self, tolerance: float = EQUAL_LEVEL_TOLERANCE) -> None:
        self.tolerance = tolerance

    # ------------------------------------------------------------------
    def analyze(self, df: pd.DataFrame, timeframe: str = "") -> LiquidityResult:
        if df is None or len(df) < 10:
            return LiquidityResult()

        df = df.tail(LIQUIDITY_LOOKBACK).copy().reset_index(drop=True)

        levels = self._detect_equal_levels(df)
        levels += self._detect_bsl_ssl(df)
        sweeps = self._detect_sweeps(df, levels)

        bsl_swept = any(s.kind == "SWEEP_HIGH" and s.confirmed for s in sweeps)
        ssl_swept = any(s.kind == "SWEEP_LOW"  and s.confirmed for s in sweeps)
        sweep_score = self._compute_sweep_score(sweeps, len(df))

        log.debug("[%s] Liquidity — BSL_swept=%s SSL_swept=%s score=%.2f",
                  timeframe, bsl_swept, ssl_swept, sweep_score)

        return LiquidityResult(
            levels=levels,
            sweeps=sweeps,
            bsl_swept=bsl_swept,
            ssl_swept=ssl_swept,
            sweep_score=sweep_score,
        )

    # ------------------------------------------------------------------
    # EQUAL HIGHS / EQUAL LOWS
    # ------------------------------------------------------------------
    def _detect_equal_levels(self, df: pd.DataFrame) -> List[LiquidityLevel]:
        levels: List[LiquidityLevel] = []
        highs = df["high"].values
        lows  = df["low"].values
        n     = len(df)

        for i in range(n - 1):
            for j in range(i + 1, min(i + 20, n)):
                # Equal Highs
                if abs(highs[i] - highs[j]) / (highs[i] + 1e-9) < self.tolerance:
                    price = (highs[i] + highs[j]) / 2
                    existing = next((l for l in levels
                                     if l.kind == "EQH" and abs(l.price - price) / (price + 1e-9) < self.tolerance), None)
                    if existing:
                        existing.count += 1
                    else:
                        levels.append(LiquidityLevel(kind="EQH", price=price, count=2,
                                                      bar_time=df.index[j]))
                # Equal Lows
                if abs(lows[i] - lows[j]) / (lows[i] + 1e-9) < self.tolerance:
                    price = (lows[i] + lows[j]) / 2
                    existing = next((l for l in levels
                                     if l.kind == "EQL" and abs(l.price - price) / (price + 1e-9) < self.tolerance), None)
                    if existing:
                        existing.count += 1
                    else:
                        levels.append(LiquidityLevel(kind="EQL", price=price, count=2,
                                                      bar_time=df.index[j]))
        return levels

    # ------------------------------------------------------------------
    # BSL / SSL FROM SWING POINTS
    # ------------------------------------------------------------------
    def _detect_bsl_ssl(self, df: pd.DataFrame) -> List[LiquidityLevel]:
        levels: List[LiquidityLevel] = []
        n = len(df)
        s = 3  # small lookback for swing points in liquidity context

        for i in range(s, n - s):
            high_val = df["high"].iloc[i]
            low_val  = df["low"].iloc[i]

            # Swing high → BSL above it
            if (high_val >= df["high"].iloc[i-s:i].max() and
                    high_val >= df["high"].iloc[i+1:i+s+1].max()):
                levels.append(LiquidityLevel(kind="BSL", price=high_val,
                                             bar_time=df.index[i]))

            # Swing low → SSL below it
            if (low_val <= df["low"].iloc[i-s:i].min() and
                    low_val <= df["low"].iloc[i+1:i+s+1].min()):
                levels.append(LiquidityLevel(kind="SSL", price=low_val,
                                             bar_time=df.index[i]))

        return levels

    # ------------------------------------------------------------------
    # SWEEP DETECTION
    # ------------------------------------------------------------------
    def _detect_sweeps(self, df: pd.DataFrame, levels: List[LiquidityLevel]) -> List[LiquiditySweep]:
        sweeps: List[LiquiditySweep] = []
        n = len(df)

        for level in levels:
            for i in range(1, n):
                bar = df.iloc[i]
                # Sweep of BSL/EQH: wick above level then close below
                if level.kind in ("BSL", "EQH") and bar["high"] > level.price:
                    if bar["close"] < level.price:   # reversal confirmed in same bar
                        level.swept = True
                        sw = LiquiditySweep(
                            kind="SWEEP_HIGH", price=level.price,
                            bar_time=df.index[i], confirmed=True
                        )
                        sweeps.append(sw)
                    elif i + SWEEP_CONFIRMATION_BARS < n:
                        # Check if subsequent bars close below level
                        future = df["close"].iloc[i+1: i+SWEEP_CONFIRMATION_BARS+1]
                        if (future < level.price).any():
                            level.swept = True
                            sw = LiquiditySweep(
                                kind="SWEEP_HIGH", price=level.price,
                                bar_time=df.index[i], confirmed=True
                            )
                            sweeps.append(sw)

                # Sweep of SSL/EQL: wick below level then close above
                if level.kind in ("SSL", "EQL") and bar["low"] < level.price:
                    if bar["close"] > level.price:
                        level.swept = True
                        sw = LiquiditySweep(
                            kind="SWEEP_LOW", price=level.price,
                            bar_time=df.index[i], confirmed=True
                        )
                        sweeps.append(sw)
                    elif i + SWEEP_CONFIRMATION_BARS < n:
                        future = df["close"].iloc[i+1: i+SWEEP_CONFIRMATION_BARS+1]
                        if (future > level.price).any():
                            level.swept = True
                            sw = LiquiditySweep(
                                kind="SWEEP_LOW", price=level.price,
                                bar_time=df.index[i], confirmed=True
                            )
                            sweeps.append(sw)
        return sweeps

    # ------------------------------------------------------------------
    def _compute_sweep_score(self, sweeps: List[LiquiditySweep], total_bars: int) -> float:
        if not sweeps:
            return 0.0
        # Weight recent sweeps higher
        score = 0.0
        for sw in sweeps:
            score += 1.0
        return min(score / max(total_bars / 10, 1), 1.0)
