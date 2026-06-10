"""
==============================================================================
ORDER FLOW ENGINE
==============================================================================
Approximates institutional order flow from OHLCV data:
  • Volume Delta (bid vs ask pressure approximation)
  • Cumulative Volume Delta (CVD)
  • Buying / Selling Pressure
  • Absorption detection
  • Volume imbalances
  • Generates a bullish/bearish flow score (0-100)
"""

from dataclasses import dataclass
from typing import List
import pandas as pd
import numpy as np

from core.logger import get_logger
from config.settings import OF_LOOKBACK

log = get_logger("order_flow.engine")


@dataclass
class OrderFlowResult:
    flow_score:       float    # 0-100 (>50 bullish, <50 bearish)
    cvd:              float    # cumulative volume delta
    buying_pressure:  float    # 0-1
    selling_pressure: float    # 0-1
    absorption:       bool     # price not moving despite volume
    imbalance:        str      # "bullish" | "bearish" | "neutral"
    delta_trend:      str      # "rising" | "falling" | "flat"


class OrderFlowEngine:
    """
    Institutional order-flow approximation using tick-volume data.

    Since MT5 provides tick-volume (not true footprint data), we use:
      • Bullish volume  ≈ volume × (close - low) / (high - low)
      • Bearish volume  ≈ volume × (high - close) / (high - low)
    This is the 'close location value' method used by many institutional tools.
    """

    # ------------------------------------------------------------------
    def analyze(self, df: pd.DataFrame, timeframe: str = "") -> OrderFlowResult:
        if df is None or len(df) < 5:
            return OrderFlowResult(
                flow_score=50.0, cvd=0.0,
                buying_pressure=0.5, selling_pressure=0.5,
                absorption=False, imbalance="neutral", delta_trend="flat"
            )

        df = df.tail(OF_LOOKBACK).copy().reset_index(drop=True)

        bull_vol, bear_vol = self._split_volume(df)
        delta      = bull_vol - bear_vol
        cvd        = delta.cumsum().iloc[-1]
        buying_p   = float(bull_vol.sum() / (bull_vol.sum() + bear_vol.sum() + 1e-9))
        selling_p  = 1.0 - buying_p
        absorption = self._detect_absorption(df, delta)
        imbalance  = self._detect_imbalance(df, bull_vol, bear_vol)
        delta_trend = self._cvd_trend(delta)
        score      = self._compute_score(buying_p, selling_p, cvd, absorption, imbalance, delta_trend)

        log.debug("[%s] OrderFlow — score=%.1f CVD=%.0f buy=%.2f sell=%.2f imb=%s",
                  timeframe, score, cvd, buying_p, selling_p, imbalance)

        return OrderFlowResult(
            flow_score=score,
            cvd=float(cvd),
            buying_pressure=buying_p,
            selling_pressure=selling_p,
            absorption=absorption,
            imbalance=imbalance,
            delta_trend=delta_trend,
        )

    # ------------------------------------------------------------------
    # VOLUME SPLIT
    # ------------------------------------------------------------------
    @staticmethod
    def _split_volume(df: pd.DataFrame):
        high  = df["high"]
        low   = df["low"]
        close = df["close"]
        vol   = df["volume"].astype(float)
        rng   = (high - low).replace(0, np.nan).fillna(1e-9)
        clv   = (close - low) / rng          # 0 = all sell, 1 = all buy
        bull  = vol * clv
        bear  = vol * (1 - clv)
        return bull, bear

    # ------------------------------------------------------------------
    # ABSORPTION
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_absorption(df: pd.DataFrame, delta: pd.Series) -> bool:
        """High volume but price is NOT moving → absorption."""
        if len(df) < 5:
            return False
        recent_vol   = df["volume"].tail(5).mean()
        overall_vol  = df["volume"].mean()
        high_vol     = recent_vol > overall_vol * 1.3
        price_range  = (df["close"].tail(5).max() - df["close"].tail(5).min())
        avg_range    = (df["high"] - df["low"]).mean()
        small_move   = price_range < avg_range * 0.5
        return bool(high_vol and small_move)

    # ------------------------------------------------------------------
    # VOLUME IMBALANCE
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_imbalance(df: pd.DataFrame, bull_vol: pd.Series, bear_vol: pd.Series) -> str:
        total = bull_vol.sum() + bear_vol.sum()
        if total == 0:
            return "neutral"
        ratio = bull_vol.sum() / total
        if ratio > 0.6:
            return "bullish"
        if ratio < 0.4:
            return "bearish"
        return "neutral"

    # ------------------------------------------------------------------
    # CVD TREND
    # ------------------------------------------------------------------
    @staticmethod
    def _cvd_trend(delta: pd.Series) -> str:
        cvd = delta.cumsum()
        if len(cvd) < 4:
            return "flat"
        slope = np.polyfit(range(len(cvd)), cvd.values, 1)[0]
        threshold = cvd.std() * 0.1
        if slope > threshold:
            return "rising"
        if slope < -threshold:
            return "falling"
        return "flat"

    # ------------------------------------------------------------------
    # FLOW SCORE
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_score(
        buying_p: float, selling_p: float, cvd: float,
        absorption: bool, imbalance: str, delta_trend: str
    ) -> float:
        score = 50.0

        # Pressure component (±20)
        score += (buying_p - selling_p) * 20

        # CVD direction (±10)
        cvd_norm = min(max(cvd, -10000), 10000) / 10000
        score += cvd_norm * 10

        # Imbalance (±10)
        if imbalance == "bullish":
            score += 10
        elif imbalance == "bearish":
            score -= 10

        # CVD trend (±5)
        if delta_trend == "rising":
            score += 5
        elif delta_trend == "falling":
            score -= 5

        # Absorption (±5 — against the move)
        if absorption:
            score -= 5  # absorption often precedes reversal

        return max(0.0, min(100.0, round(score, 2)))
