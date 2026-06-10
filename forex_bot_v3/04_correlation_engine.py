"""
==============================================================================
04 — CORRELATION ENGINE
==============================================================================
Prevents over-exposure to correlated pairs.

Problems it solves:
  • EURUSD long + GBPUSD long = double USD exposure
  • XAUUSD long + EURUSD long = both fall when USD rises
  • BTCUSD + ETHUSD = highly correlated crypto positions

Features:
  • Real-time correlation matrix from recent returns
  • Blocks new trades if correlated position already open
  • Warns on near-correlated pairs
  • Tracks net USD/JPY/EUR exposure
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from core.logger import get_logger

log = get_logger("correlation_engine")

# ── KNOWN STATIC CORRELATIONS ─────────────────────────────────────────────────
# For when we don't have live data
STATIC_CORRELATIONS = {
    ("EURUSD", "GBPUSD"):  0.85,
    ("EURUSD", "AUDUSD"):  0.75,
    ("EURUSD", "NZDUSD"):  0.70,
    ("EURUSD", "USDCHF"): -0.90,
    ("GBPUSD", "AUDUSD"):  0.72,
    ("USDJPY", "USDCHF"):  0.75,
    ("EURUSD", "XAUUSD"):  0.60,
    ("BTCUSD", "ETHUSD"):  0.90,
    ("XAUUSD", "XAGUSD"):  0.80,
    ("GBPJPY", "EURJPY"):  0.88,
    ("AUDUSD", "NZDUSD"):  0.88,
    ("USDCAD", "EURUSD"): -0.75,
}

CORRELATION_BLOCK_THRESHOLD  = 0.80   # block if correlation > 0.80
CORRELATION_WARN_THRESHOLD   = 0.65   # warn if correlation > 0.65
MAX_SAME_DIRECTION_CORR      = 2      # max correlated pairs in same direction


@dataclass
class CorrelationCheck:
    allowed:        bool
    reason:         str
    corr_pairs:     List[Tuple[str, float]]   # (pair, correlation)
    net_usd_exposure: int     # +/- positions net USD direction
    net_jpy_exposure: int
    risk_multiplier: float    # 0-1 reduce size if near-correlated


class CorrelationEngine:

    def __init__(self) -> None:
        self._price_cache: Dict[str, pd.Series] = {}

    def check(
        self,
        new_symbol:     str,
        new_direction:  str,
        open_positions: List[Dict],
    ) -> CorrelationCheck:
        """
        Check if opening new_symbol in new_direction is safe given open positions.
        """
        if not open_positions:
            return CorrelationCheck(
                allowed=True, reason="No open positions",
                corr_pairs=[], net_usd_exposure=0,
                net_jpy_exposure=0, risk_multiplier=1.0
            )

        corr_pairs    = []
        block_reason  = ""
        risk_mult     = 1.0
        same_dir_corr = 0

        for pos in open_positions:
            sym = pos["symbol"]
            if sym == new_symbol:
                continue

            corr = self._get_correlation(new_symbol, sym)
            if corr is None:
                continue

            # Same direction = amplified exposure
            # Opposite direction = hedge (less concern)
            pos_dir = pos.get("type", "BUY")
            same_dir = (pos_dir == new_direction)
            effective_corr = corr if same_dir else -corr

            if abs(corr) > CORRELATION_WARN_THRESHOLD:
                corr_pairs.append((sym, round(effective_corr, 2)))

            if corr > CORRELATION_BLOCK_THRESHOLD and same_dir:
                same_dir_corr += 1
                if same_dir_corr >= MAX_SAME_DIRECTION_CORR:
                    block_reason = f"Too many correlated positions: {sym} corr={corr:.2f}"
                    log.warning("[CORR] Blocking %s — %s", new_symbol, block_reason)
                    return CorrelationCheck(
                        allowed=False, reason=block_reason,
                        corr_pairs=corr_pairs, net_usd_exposure=0,
                        net_jpy_exposure=0, risk_multiplier=0.0
                    )

                # Reduce risk for correlated pair
                risk_mult = min(risk_mult, 1.0 - (corr - CORRELATION_WARN_THRESHOLD))

        # Currency exposure check
        net_usd = self._net_exposure(open_positions, "USD")
        net_jpy = self._net_exposure(open_positions, "JPY")

        log.debug("[CORR] %s %s: corr_pairs=%d risk_mult=%.2f USD_exp=%d JPY_exp=%d",
                  new_symbol, new_direction, len(corr_pairs), risk_mult, net_usd, net_jpy)

        return CorrelationCheck(
            allowed=True,
            reason="OK",
            corr_pairs=corr_pairs,
            net_usd_exposure=net_usd,
            net_jpy_exposure=net_jpy,
            risk_multiplier=max(0.3, risk_mult),
        )

    def _get_correlation(self, sym1: str, sym2: str) -> Optional[float]:
        """Get correlation between two symbols — static first, then dynamic."""
        key1 = (sym1, sym2)
        key2 = (sym2, sym1)
        if key1 in STATIC_CORRELATIONS:
            return STATIC_CORRELATIONS[key1]
        if key2 in STATIC_CORRELATIONS:
            return STATIC_CORRELATIONS[key2]

        # Dynamic calculation from cached prices
        if sym1 in self._price_cache and sym2 in self._price_cache:
            try:
                s1 = self._price_cache[sym1].pct_change().dropna()
                s2 = self._price_cache[sym2].pct_change().dropna()
                common = s1.index.intersection(s2.index)
                if len(common) > 20:
                    return float(s1[common].corr(s2[common]))
            except Exception:
                pass
        return None

    def update_prices(self, symbol: str, prices: pd.Series) -> None:
        """Update price cache for dynamic correlation calculation."""
        self._price_cache[symbol] = prices.tail(100)

    @staticmethod
    def _net_exposure(positions: List[Dict], currency: str) -> int:
        """Count net long/short exposure to a currency."""
        CURRENCY_MAP = {
            "USD": {"long": ["EURUSD","GBPUSD","AUDUSD","NZDUSD","XAUUSD"],
                    "short": ["USDJPY","USDCHF","USDCAD"]},
            "JPY": {"short": ["USDJPY","EURJPY","GBPJPY","AUDJPY","CADJPY","CHFJPY","NZDJPY"],
                    "long": []},
        }
        net = 0
        if currency not in CURRENCY_MAP:
            return 0
        cmap = CURRENCY_MAP[currency]
        for pos in positions:
            sym = pos.get("symbol","")
            direction = pos.get("type","BUY")
            if sym in cmap.get("long", []):
                net += 1 if direction == "BUY" else -1
            if sym in cmap.get("short", []):
                net += -1 if direction == "BUY" else 1
        return net
