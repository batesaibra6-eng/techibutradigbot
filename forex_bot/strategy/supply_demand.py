"""
==============================================================================
STRATEGY — Supply & Demand Zone Engine
==============================================================================
Detects institutional supply and demand zones from OHLCV data.

Zone types:
  • Rally-Base-Drop  → Supply Zone
  • Drop-Base-Rally  → Demand Zone

Each zone carries:
  • price bounds (top, bottom)
  • strength score
  • retest count
  • origin timeframe
  • freshness flag
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import numpy as np

from core.logger import get_logger
from config.settings import ZONE_LOOKBACK, ZONE_MIN_STRENGTH, ZONE_MAX_RETESTS, ZONE_EXTENSION_PIPS

log = get_logger("strategy.supply_demand")


@dataclass
class Zone:
    kind:     str       # "supply" | "demand"
    top:      float
    bottom:   float
    strength: float     # 0-10
    retests:  int = 0
    fresh:    bool = True
    origin_tf: str = ""
    bar_time: Optional[pd.Timestamp] = None

    @property
    def mid(self) -> float:
        return (self.top + self.bottom) / 2

    def contains(self, price: float) -> bool:
        return self.bottom <= price <= self.top

    def is_valid(self) -> bool:
        return self.fresh and self.retests < ZONE_MAX_RETESTS and self.strength >= ZONE_MIN_STRENGTH


class SupplyDemandEngine:
    """
    Identifies fresh institutional supply and demand zones.
    Uses a base-candle approach: small-bodied consolidation candles
    preceded and followed by strong impulse candles.
    """

    def __init__(self) -> None:
        self._zones: List[Zone] = []

    # ------------------------------------------------------------------
    def detect_zones(
        self, df: pd.DataFrame, timeframe: str = "", point: float = 0.0001
    ) -> List[Zone]:
        """
        Run zone detection on a DataFrame.  Returns all valid zones.
        """
        if df is None or len(df) < 10:
            return []

        df = df.tail(ZONE_LOOKBACK).copy().reset_index(drop=True)
        zones: List[Zone] = []

        pip_size = point * 10 if point < 0.01 else point

        for i in range(2, len(df) - 1):
            base = df.iloc[i]
            body = abs(base["close"] - base["open"])
            rng  = base["high"] - base["low"]
            if rng == 0:
                continue

            base_ratio = body / rng   # small body = consolidation

            if base_ratio > 0.4:
                continue  # not a base candle

            # --- Demand: Drop → Base → Rally ---
            if i >= 2:
                prev2 = df.iloc[i - 2]
                prev1 = df.iloc[i - 1]
                nxt   = df.iloc[i + 1] if i + 1 < len(df) else None

                # Impulse down before base
                drop_impulse = (prev1["open"] - prev1["close"]) / (prev1["high"] - prev1["low"] + 1e-9)
                # Impulse up after base
                if nxt is not None:
                    rally_impulse = (nxt["close"] - nxt["open"]) / (nxt["high"] - nxt["low"] + 1e-9)
                    if drop_impulse > 0.6 and rally_impulse > 0.5:
                        ext = ZONE_EXTENSION_PIPS * pip_size
                        z = Zone(
                            kind="demand",
                            top=base["high"] + ext,
                            bottom=base["low"] - ext,
                            strength=self._score(drop_impulse, rally_impulse, base_ratio, body, pip_size),
                            origin_tf=timeframe,
                            bar_time=df.index[i] if hasattr(df.index, 'to_list') else None,
                        )
                        zones.append(z)

            # --- Supply: Rally → Base → Drop ---
            if i >= 2:
                prev1 = df.iloc[i - 1]
                nxt   = df.iloc[i + 1] if i + 1 < len(df) else None

                rally_impulse = (prev1["close"] - prev1["open"]) / (prev1["high"] - prev1["low"] + 1e-9)
                if nxt is not None:
                    drop_impulse = (nxt["open"] - nxt["close"]) / (nxt["high"] - nxt["low"] + 1e-9)
                    if rally_impulse > 0.6 and drop_impulse > 0.5:
                        ext = ZONE_EXTENSION_PIPS * pip_size
                        z = Zone(
                            kind="supply",
                            top=base["high"] + ext,
                            bottom=base["low"] - ext,
                            strength=self._score(rally_impulse, drop_impulse, base_ratio, body, pip_size),
                            origin_tf=timeframe,
                            bar_time=df.index[i] if hasattr(df.index, 'to_list') else None,
                        )
                        zones.append(z)

        # Deduplicate overlapping zones
        zones = self._deduplicate(zones)

        # Update retest counts against latest close
        current_price = df["close"].iloc[-1]
        for z in zones:
            if z.contains(current_price):
                z.retests += 1
                if z.retests >= ZONE_MAX_RETESTS:
                    z.fresh = False

        self._zones = [z for z in zones if z.is_valid()]
        log.debug("[%s] Zones detected: %d supply, %d demand",
                  timeframe,
                  sum(1 for z in self._zones if z.kind == "supply"),
                  sum(1 for z in self._zones if z.kind == "demand"))
        return self._zones

    def get_zones_near_price(self, price: float, pips: float = 20, point: float = 0.0001) -> List[Zone]:
        """Return zones within N pips of a given price."""
        margin = pips * point * 10
        return [z for z in self._zones if abs(z.mid - price) <= margin]

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _score(
        impulse1: float, impulse2: float,
        base_ratio: float, body: float, pip_size: float
    ) -> float:
        score = 0.0
        score += impulse1 * 3   # strength of move into base
        score += impulse2 * 3   # strength of move out of base
        score += (1 - base_ratio) * 2  # tighter base = stronger
        score += min(body / pip_size, 2)  # body size in pips capped at 2
        return min(round(score, 2), 10.0)

    @staticmethod
    def _deduplicate(zones: List[Zone]) -> List[Zone]:
        """Remove zones that overlap > 70 %."""
        unique: List[Zone] = []
        for z in zones:
            overlap = False
            for u in unique:
                if z.kind != u.kind:
                    continue
                lo = max(z.bottom, u.bottom)
                hi = min(z.top, u.top)
                if hi > lo:
                    z_range = z.top - z.bottom + 1e-9
                    overlap_pct = (hi - lo) / z_range
                    if overlap_pct > 0.7:
                        # keep the stronger zone
                        if z.strength > u.strength:
                            unique.remove(u)
                            unique.append(z)
                        overlap = True
                        break
            if not overlap:
                unique.append(z)
        return unique
