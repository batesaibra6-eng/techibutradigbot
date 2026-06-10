"""
==============================================================================
01 — REGIME ENGINE
==============================================================================
Detects market regime per symbol:
  TRENDING_UP / TRENDING_DOWN / RANGING / EXPANSION / COMPRESSION
  HIGH_VOLATILITY / LOW_VOLATILITY

Uses:
  • ADX (trend strength)
  • ATR Percentile (volatility rank)
  • Hurst Exponent (mean-reversion vs trending)
  • Realized Volatility
  • Price structure (HH/HL vs LH/LL)

Outputs:
  • regime: str
  • trend_strength: 0-1
  • volatility_rank: 0-1 (percentile)
  • is_tradeable: bool
  • adx: float
  • atr: float
  • hurst: float
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from core.logger import get_logger

log = get_logger("regime_engine")

# ── REGIME CONSTANTS ──────────────────────────────────────────────────────────
REGIME_TRENDING_UP   = "TRENDING_UP"
REGIME_TRENDING_DOWN = "TRENDING_DOWN"
REGIME_RANGING       = "RANGING"
REGIME_EXPANSION     = "EXPANSION"
REGIME_COMPRESSION   = "COMPRESSION"
REGIME_HIGH_VOL      = "HIGH_VOLATILITY"
REGIME_LOW_VOL       = "LOW_VOLATILITY"

ADX_TREND_THRESHOLD  = 25     # ADX > 25 = trending
ADX_STRONG_THRESHOLD = 40     # ADX > 40 = strong trend
ATR_HIGH_PERCENTILE  = 75     # above 75th percentile = high vol
ATR_LOW_PERCENTILE   = 25     # below 25th percentile = low vol
HURST_TRENDING       = 0.55   # H > 0.55 = trending (persistent)
HURST_RANGING        = 0.45   # H < 0.45 = mean-reverting


@dataclass
class RegimeResult:
    regime:          str
    trend_strength:  float    # 0-1
    volatility_rank: float    # 0-1 (ATR percentile)
    adx:             float
    atr:             float
    atr_pct:         float    # ATR as % of price
    hurst:           float
    realized_vol:    float    # annualised
    is_tradeable:    bool
    notes:           str = ""


class RegimeEngine:
    """Classifies market regime from OHLCV data."""

    def analyze(self, df: pd.DataFrame, symbol: str = "") -> RegimeResult:
        if df is None or len(df) < 30:
            return RegimeResult(
                regime=REGIME_RANGING, trend_strength=0.5,
                volatility_rank=0.5, adx=20.0, atr=0.0,
                atr_pct=0.0, hurst=0.5, realized_vol=0.0,
                is_tradeable=True, notes="Insufficient data"
            )

        df = df.copy().reset_index(drop=True)

        # ── INDICATORS ────────────────────────────────────────────────────────
        adx_val      = self._adx(df)
        atr_val      = self._atr(df)
        atr_pct      = atr_val / (df["close"].iloc[-1] + 1e-9) * 100
        atr_rank     = self._atr_percentile(df)
        hurst_val    = self._hurst(df["close"].values[-50:])
        realized_vol = self._realized_vol(df)
        trend_dir    = self._trend_direction(df)

        # ── REGIME CLASSIFICATION ─────────────────────────────────────────────
        regime, trend_strength = self._classify(
            adx_val, atr_rank, hurst_val, trend_dir
        )

        # ── TRADEABILITY ──────────────────────────────────────────────────────
        is_tradeable = True
        notes = []

        # Don't trade extremely low volatility (dead market)
        if atr_rank < 0.1:
            is_tradeable = False
            notes.append("ATR too low")

        # Don't trade insane volatility (news spike)
        if atr_rank > 0.97:
            is_tradeable = False
            notes.append("ATR spike — possible news")

        log.debug("[%s] Regime=%s ADX=%.1f ATR_rank=%.2f Hurst=%.2f Tradeable=%s",
                  symbol, regime, adx_val, atr_rank, hurst_val, is_tradeable)

        return RegimeResult(
            regime=regime,
            trend_strength=trend_strength,
            volatility_rank=atr_rank,
            adx=adx_val,
            atr=atr_val,
            atr_pct=atr_pct,
            hurst=hurst_val,
            realized_vol=realized_vol,
            is_tradeable=is_tradeable,
            notes=" | ".join(notes),
        )

    # ──────────────────────────────────────────────────────────────────────────
    # INDICATOR CALCULATIONS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> float:
        high  = df["high"]
        low   = df["low"]
        close = df["close"].shift(1)
        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low  - close).abs(),
        ], axis=1).max(axis=1)
        return float(tr.rolling(period).mean().iloc[-1])

    @staticmethod
    def _atr_percentile(df: pd.DataFrame, period: int = 14, lookback: int = 100) -> float:
        """ATR percentile rank over lookback window — 0-1."""
        high  = df["high"]
        low   = df["low"]
        close = df["close"].shift(1)
        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low  - close).abs(),
        ], axis=1).max(axis=1)
        atr_series = tr.rolling(period).mean().dropna().tail(lookback)
        if len(atr_series) < 2:
            return 0.5
        current_atr = atr_series.iloc[-1]
        rank = (atr_series < current_atr).sum() / len(atr_series)
        return float(rank)

    @staticmethod
    def _adx(df: pd.DataFrame, period: int = 14) -> float:
        """Average Directional Index."""
        high  = df["high"].values
        low   = df["low"].values
        close = df["close"].values
        n     = len(df)

        plus_dm  = np.zeros(n)
        minus_dm = np.zeros(n)
        tr_arr   = np.zeros(n)

        for i in range(1, n):
            h_diff = high[i]  - high[i-1]
            l_diff = low[i-1] - low[i]
            plus_dm[i]  = h_diff if h_diff > l_diff and h_diff > 0 else 0
            minus_dm[i] = l_diff if l_diff > h_diff and l_diff > 0 else 0
            tr_arr[i]   = max(high[i]-low[i],
                              abs(high[i]-close[i-1]),
                              abs(low[i]-close[i-1]))

        def smooth(arr, p):
            s = np.zeros(len(arr))
            s[p] = arr[1:p+1].sum()
            for i in range(p+1, len(arr)):
                s[i] = s[i-1] - s[i-1]/p + arr[i]
            return s

        tr_s  = smooth(tr_arr,   period)
        pdm_s = smooth(plus_dm,  period)
        mdm_s = smooth(minus_dm, period)

        with np.errstate(divide='ignore', invalid='ignore'):
            pdi = np.where(tr_s > 0, 100 * pdm_s / tr_s, 0)
            mdi = np.where(tr_s > 0, 100 * mdm_s / tr_s, 0)
            dx  = np.where((pdi+mdi) > 0, 100 * np.abs(pdi-mdi)/(pdi+mdi), 0)

        adx_series = pd.Series(dx).rolling(period).mean()
        return float(adx_series.iloc[-1]) if not np.isnan(adx_series.iloc[-1]) else 20.0

    @staticmethod
    def _hurst(prices: np.ndarray) -> float:
        """
        Hurst Exponent via R/S analysis.
        H > 0.5 → trending (persistent)
        H < 0.5 → mean-reverting
        H ≈ 0.5 → random walk
        """
        n = len(prices)
        if n < 20:
            return 0.5
        try:
            lags   = range(2, min(20, n // 2))
            tau    = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]
            tau    = [t for t in tau if t > 0]
            if len(tau) < 3:
                return 0.5
            reg    = np.polyfit(np.log(list(lags)[:len(tau)]),
                                np.log(tau), 1)
            return float(np.clip(reg[0], 0.0, 1.0))
        except Exception:
            return 0.5

    @staticmethod
    def _realized_vol(df: pd.DataFrame, period: int = 20) -> float:
        """Annualised realised volatility from log returns."""
        log_ret = np.log(df["close"] / df["close"].shift(1)).dropna()
        if len(log_ret) < period:
            return 0.0
        return float(log_ret.tail(period).std() * np.sqrt(252) * 100)

    @staticmethod
    def _trend_direction(df: pd.DataFrame) -> str:
        """Simple EMA crossover trend direction."""
        close = df["close"]
        if len(close) < 50:
            return "neutral"
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        if ema20 > ema50 * 1.001:
            return "up"
        if ema20 < ema50 * 0.999:
            return "down"
        return "neutral"

    def _classify(self, adx, atr_rank, hurst, trend_dir):
        """Classify regime and return (regime_str, trend_strength 0-1)."""
        trend_strength = min(adx / 50.0, 1.0)

        # Volatility extremes override
        if atr_rank > 0.90:
            return REGIME_HIGH_VOL, trend_strength
        if atr_rank < 0.15:
            return REGIME_LOW_VOL, 0.1

        # Trending regime
        if adx > ADX_TREND_THRESHOLD and hurst > HURST_TRENDING:
            if trend_dir == "up":
                return REGIME_TRENDING_UP, trend_strength
            if trend_dir == "down":
                return REGIME_TRENDING_DOWN, trend_strength

        # Expansion — high ATR + moderate ADX
        if atr_rank > ATR_HIGH_PERCENTILE / 100 and adx > 20:
            return REGIME_EXPANSION, trend_strength * 0.8

        # Compression — low ATR (squeeze before breakout)
        if atr_rank < ATR_LOW_PERCENTILE / 100:
            return REGIME_COMPRESSION, 0.3

        # Ranging — mean reverting
        return REGIME_RANGING, 0.3
