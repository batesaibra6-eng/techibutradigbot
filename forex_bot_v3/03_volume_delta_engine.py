"""
==============================================================================
03 — ENHANCED VOLUME DELTA ENGINE
==============================================================================
Improvements over V2:
  • Relative Volume (RVOL) — current vol vs average
  • Volume Imbalance detection
  • Delta divergence (price up but delta falling = weakness)
  • Volume profile approximation (high volume nodes)
  • Generates enhanced flow score with more context
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from core.logger import get_logger

log = get_logger("volume_delta_engine")


@dataclass
class VolumeDeltaResult:
    flow_score:       float   # 0-100
    cvd:              float   # cumulative volume delta
    buying_pressure:  float   # 0-1
    selling_pressure: float   # 0-1
    rvol:             float   # relative volume (1.0 = average)
    delta_divergence: bool    # price direction ≠ delta direction
    imbalance:        str     # "bullish" | "bearish" | "neutral"
    delta_trend:      str     # "rising" | "falling" | "flat"
    absorption:       bool    # high vol + small move
    high_vol_node:    float   # price level with most volume (approx)
    volume_strength:  str     # "strong" | "average" | "weak"


class VolumeDeltaEngine:

    def analyze(self, df: pd.DataFrame, timeframe: str = "") -> VolumeDeltaResult:
        if df is None or len(df) < 10:
            return VolumeDeltaResult(
                flow_score=50.0, cvd=0.0, buying_pressure=0.5,
                selling_pressure=0.5, rvol=1.0, delta_divergence=False,
                imbalance="neutral", delta_trend="flat",
                absorption=False, high_vol_node=0.0, volume_strength="average"
            )

        df = df.copy().reset_index(drop=True)
        lookback = min(20, len(df))
        recent = df.tail(lookback)

        # ── VOLUME SPLIT (CLV method) ────────────────────────────────────────
        rng  = (recent["high"] - recent["low"]).replace(0, 1e-9)
        clv  = (recent["close"] - recent["low"]) / rng
        vol  = recent["volume"].astype(float)
        bull = vol * clv
        bear = vol * (1 - clv)
        delta = bull - bear

        # ── CORE METRICS ─────────────────────────────────────────────────────
        total_vol    = bull.sum() + bear.sum()
        buying_p     = float(bull.sum() / (total_vol + 1e-9))
        selling_p    = 1.0 - buying_p
        cvd          = float(delta.cumsum().iloc[-1])

        # ── RELATIVE VOLUME ───────────────────────────────────────────────────
        avg_vol = df["volume"].mean()
        current_vol = df["volume"].iloc[-1]
        rvol = float(current_vol / (avg_vol + 1e-9))

        # ── DELTA TREND ───────────────────────────────────────────────────────
        cvd_series = delta.cumsum()
        if len(cvd_series) >= 4:
            slope = np.polyfit(range(len(cvd_series)), cvd_series.values, 1)[0]
            thresh = cvd_series.std() * 0.1 if cvd_series.std() > 0 else 0.001
            delta_trend = "rising" if slope > thresh else ("falling" if slope < -thresh else "flat")
        else:
            delta_trend = "flat"

        # ── IMBALANCE ─────────────────────────────────────────────────────────
        imbalance = "bullish" if buying_p > 0.62 else ("bearish" if buying_p < 0.38 else "neutral")

        # ── DELTA DIVERGENCE ─────────────────────────────────────────────────
        price_direction = "up" if recent["close"].iloc[-1] > recent["close"].iloc[0] else "down"
        delta_divergence = (
            (price_direction == "up"   and delta_trend == "falling") or
            (price_direction == "down" and delta_trend == "rising")
        )

        # ── ABSORPTION ───────────────────────────────────────────────────────
        recent_vol_avg = vol.mean()
        high_vol  = vol.iloc[-1] > recent_vol_avg * 1.5
        small_rng = float(rng.iloc[-1]) < float(rng.mean()) * 0.4
        absorption = bool(high_vol and small_rng)

        # ── HIGH VOLUME NODE ─────────────────────────────────────────────────
        # Approximate: find price level with highest volume
        price_bins = pd.cut(df["close"], bins=10)
        vol_by_level = df.groupby(price_bins, observed=True)["volume"].sum()
        if not vol_by_level.empty:
            max_level = vol_by_level.idxmax()
            high_vol_node = float(max_level.mid) if hasattr(max_level, 'mid') else 0.0
        else:
            high_vol_node = float(df["close"].mean())

        # ── VOLUME STRENGTH ───────────────────────────────────────────────────
        volume_strength = "strong" if rvol > 1.5 else ("weak" if rvol < 0.5 else "average")

        # ── FLOW SCORE ────────────────────────────────────────────────────────
        score = 50.0
        score += (buying_p - selling_p) * 25
        score += min(max(cvd, -50000), 50000) / 50000 * 10
        score += 10 if imbalance == "bullish" else (-10 if imbalance == "bearish" else 0)
        score += 5  if delta_trend == "rising" else (-5 if delta_trend == "falling" else 0)
        score -= 8  if delta_divergence else 0
        score -= 5  if absorption else 0
        score += 3  if rvol > 1.5 else 0    # high volume confirms move

        score = max(0.0, min(100.0, round(score, 2)))

        return VolumeDeltaResult(
            flow_score=score,
            cvd=cvd,
            buying_pressure=buying_p,
            selling_pressure=selling_p,
            rvol=rvol,
            delta_divergence=delta_divergence,
            imbalance=imbalance,
            delta_trend=delta_trend,
            absorption=absorption,
            high_vol_node=high_vol_node,
            volume_strength=volume_strength,
        )
