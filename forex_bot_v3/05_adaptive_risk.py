"""
==============================================================================
05 — ADAPTIVE RISK ENGINE
==============================================================================
Adjusts position size dynamically based on:
  • Market regime (trend = more risk, compression = less)
  • Volatility rank (high vol = less size)
  • Correlation exposure
  • Recent performance (winning streak = maintain, losing = reduce)
  • Account size (micro account protection)
  • News proximity
  • Session quality
"""

import math
from dataclasses import dataclass
from typing import Optional
from core.logger import get_logger
from config.settings import (
    RISK_PER_TRADE_PCT, MIN_LOT_SIZE,
    MICRO_ACCOUNT_THRESHOLD
)

log = get_logger("adaptive_risk")

# ── REGIME RISK MULTIPLIERS ───────────────────────────────────────────────────
REGIME_RISK = {
    "TRENDING_UP":   1.0,    # full risk
    "TRENDING_DOWN": 1.0,    # full risk
    "EXPANSION":     0.9,    # slightly less — volatile
    "RANGING":       0.8,    # less risk — choppier
    "COMPRESSION":   0.7,    # least risk — uncertain breakout direction
    "HIGH_VOLATILITY": 0.5,  # half risk — news/spike environment
    "LOW_VOLATILITY":  0.6,  # reduced — low opportunity
}

# ── SESSION RISK MULTIPLIERS ──────────────────────────────────────────────────
SESSION_RISK = {
    "overlap":  1.0,    # London/NY overlap — best liquidity
    "london":   0.95,
    "newyork":  0.95,
    "asian":    0.80,   # lower liquidity
    "other":    0.60,
}


@dataclass
class AdaptiveRiskResult:
    base_risk_pct:      float    # from settings
    adjusted_risk_pct:  float    # after all adjustments
    final_lots:         float
    risk_multiplier:    float    # 0-1 combined multiplier
    reasons:            list


class AdaptiveRiskEngine:

    def __init__(self) -> None:
        self._recent_outcomes: list = []    # "win" | "loss" last N trades
        self._max_history = 20

    def calculate(
        self,
        balance:        float,
        sl_pips:        float,
        symbol_info:    dict,
        regime:         str   = "RANGING",
        volatility_rank: float = 0.5,
        news_multiplier: float = 1.0,
        corr_multiplier: float = 1.0,
        session:         str  = "london",
    ) -> AdaptiveRiskResult:

        reasons      = []
        multipliers  = []

        # ── BASE RISK ────────────────────────────────────────────────────────
        base_risk = RISK_PER_TRADE_PCT

        # ── REGIME ADJUSTMENT ─────────────────────────────────────────────────
        regime_mult = REGIME_RISK.get(regime, 0.8)
        multipliers.append(regime_mult)
        reasons.append(f"Regime({regime})={regime_mult:.2f}")

        # ── VOLATILITY ADJUSTMENT ─────────────────────────────────────────────
        if volatility_rank > 0.85:
            vol_mult = 0.5
            reasons.append("HighVol=0.50")
        elif volatility_rank > 0.70:
            vol_mult = 0.75
            reasons.append("ElevVol=0.75")
        elif volatility_rank < 0.20:
            vol_mult = 0.70
            reasons.append("LowVol=0.70")
        else:
            vol_mult = 1.0
        multipliers.append(vol_mult)

        # ── NEWS PROXIMITY ────────────────────────────────────────────────────
        if news_multiplier < 1.0:
            multipliers.append(news_multiplier)
            reasons.append(f"News={news_multiplier:.2f}")

        # ── CORRELATION EXPOSURE ──────────────────────────────────────────────
        if corr_multiplier < 1.0:
            multipliers.append(corr_multiplier)
            reasons.append(f"Corr={corr_multiplier:.2f}")

        # ── SESSION QUALITY ───────────────────────────────────────────────────
        sess_mult = SESSION_RISK.get(session, 0.8)
        multipliers.append(sess_mult)
        if sess_mult < 1.0:
            reasons.append(f"Session({session})={sess_mult:.2f}")

        # ── STREAK ADJUSTMENT ─────────────────────────────────────────────────
        streak_mult = self._streak_multiplier()
        if streak_mult != 1.0:
            multipliers.append(streak_mult)
            reasons.append(f"Streak={streak_mult:.2f}")

        # ── MICRO ACCOUNT PROTECTION ──────────────────────────────────────────
        if balance < MICRO_ACCOUNT_THRESHOLD:
            micro_mult = max(0.5, balance / MICRO_ACCOUNT_THRESHOLD)
            multipliers.append(micro_mult)
            reasons.append(f"Micro={micro_mult:.2f}")

        # ── COMBINE ALL MULTIPLIERS ───────────────────────────────────────────
        combined = 1.0
        for m in multipliers:
            combined *= m
        combined = max(0.2, min(1.0, combined))

        adjusted_risk = base_risk * combined

        # ── CALCULATE LOTS ────────────────────────────────────────────────────
        lots = self._lots(balance, adjusted_risk, sl_pips, symbol_info)

        log.debug("AdaptiveRisk: base=%.2f%% adj=%.2f%% mult=%.3f lots=%.2f | %s",
                  base_risk, adjusted_risk, combined, lots, " | ".join(reasons))

        return AdaptiveRiskResult(
            base_risk_pct=base_risk,
            adjusted_risk_pct=round(adjusted_risk, 3),
            final_lots=lots,
            risk_multiplier=round(combined, 3),
            reasons=reasons,
        )

    def record_outcome(self, outcome: str) -> None:
        """Record 'win' or 'loss' for streak adjustment."""
        self._recent_outcomes.append(outcome)
        if len(self._recent_outcomes) > self._max_history:
            self._recent_outcomes.pop(0)

    def _streak_multiplier(self) -> float:
        """Reduce after losing streak, maintain after winning."""
        if len(self._recent_outcomes) < 3:
            return 1.0
        last3 = self._recent_outcomes[-3:]
        losses = last3.count("loss")
        if losses == 3:
            log.info("3 consecutive losses — reducing risk to 60%%")
            return 0.6
        if losses == 2:
            return 0.8
        return 1.0

    @staticmethod
    def _lots(balance: float, risk_pct: float, sl_pips: float, symbol_info: dict) -> float:
        if sl_pips <= 0 or balance <= 0:
            return MIN_LOT_SIZE
        risk_amount   = balance * risk_pct / 100
        contract_size = symbol_info.get("trade_contract_size", 100000)
        point         = symbol_info.get("point", 0.0001)
        pip_value     = point * 10 * contract_size
        lots          = risk_amount / (sl_pips * pip_value)
        vol_step      = symbol_info.get("volume_step", 0.01)
        vol_min       = symbol_info.get("volume_min",  0.01)
        vol_max       = symbol_info.get("volume_max",  100.0)
        lots          = math.floor(lots / vol_step) * vol_step
        return round(max(vol_min, min(vol_max, lots)), 2)
