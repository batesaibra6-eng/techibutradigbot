"""
==============================================================================
STRATEGY — CRT + Turtle Soup Signal Generator
==============================================================================
Implements the full CRT (Candle Range Theory) + Turtle Soup strategy:

LONG SETUP:
  1. Higher TF bias is bullish
  2. Price near a fresh demand zone
  3. Liquidity sweep below recent lows (SSL swept)
  4. Turtle Soup reversal (close back above swept low)
  5. Market structure shifts bullish (BOS / CHOCH UP)
  6. Entry confirmation on M5/M15/M30
  7. Order flow bullish

SHORT SETUP:
  Mirror of above — bearish bias, supply zone, BSL swept, CHOCH/BOS down
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from market_structure.analyzer import MarketStructureResult
from strategy.supply_demand import Zone
from liquidity.engine import LiquidityResult
from order_flow.engine import OrderFlowResult
from config.settings import MIN_RR_RATIO

log = get_logger("strategy.crt_turtle_soup")


@dataclass
class TradeSignal:
    symbol:           str
    direction:        str           # "BUY" | "SELL"
    entry_price:      float
    stop_loss:        float
    take_profit_1:    float
    take_profit_2:    float
    rr_ratio:         float
    confidence:       float         # 0-100 (from rule engine)
    ai_score:         float = 0.0   # filled by AI engine
    timeframe:        str = ""
    signal_time:      datetime = field(default_factory=datetime.utcnow)
    reason:           str = ""
    zone:             Optional[Zone] = None
    metadata:         Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
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


class CRTTurtleSoupStrategy:
    """
    Generates BUY / SELL signals using the CRT + Turtle Soup framework.
    Requires multi-timeframe inputs assembled by the core scanner.
    """

    # ------------------------------------------------------------------
    def generate_signal(
        self,
        symbol: str,
        # Higher TF analysis
        higher_tf_bias:   str,          # "bullish" | "bearish" | "neutral"
        higher_tf_strength: float,      # 0-1
        # Zone
        zones: List[Zone],
        current_price: float,
        point: float,
        # Entry TF analysis
        entry_structure:  MarketStructureResult,
        liquidity:        LiquidityResult,
        order_flow:       OrderFlowResult,
        entry_tf:         str,
        # Price data for SL/TP calculation
        entry_df:         pd.DataFrame,
    ) -> Optional[TradeSignal]:
        """
        Evaluate all conditions and return a TradeSignal if all layers align.
        Returns None if conditions are not met.
        """
        if higher_tf_bias == "neutral" or higher_tf_strength < 0.3:
            return None

        # ---- Find relevant zone ----------------------------------------
        pip = point * 10
        nearby_zones = [z for z in zones if abs(z.mid - current_price) < 50 * pip]
        if not nearby_zones:
            return None

        # ---- LONG SETUP ------------------------------------------------
        if higher_tf_bias == "bullish":
            demand_zones = [z for z in nearby_zones if z.kind == "demand" and z.contains(current_price)]
            if not demand_zones:
                # Price approaching demand from above (within 10 pips)
                demand_zones = [z for z in nearby_zones
                                if z.kind == "demand" and current_price - z.top < 10 * pip]
            if demand_zones:
                signal = self._build_long(
                    symbol, current_price, demand_zones[0],
                    higher_tf_strength, entry_structure,
                    liquidity, order_flow, entry_tf, entry_df, point
                )
                return signal

        # ---- SHORT SETUP -----------------------------------------------
        if higher_tf_bias == "bearish":
            supply_zones = [z for z in nearby_zones if z.kind == "supply" and z.contains(current_price)]
            if not supply_zones:
                supply_zones = [z for z in nearby_zones
                                if z.kind == "supply" and z.bottom - current_price < 10 * pip]
            if supply_zones:
                signal = self._build_short(
                    symbol, current_price, supply_zones[0],
                    higher_tf_strength, entry_structure,
                    liquidity, order_flow, entry_tf, entry_df, point
                )
                return signal

        return None

    # ------------------------------------------------------------------
    # BUILD LONG SIGNAL
    # ------------------------------------------------------------------
    def _build_long(
        self, symbol, price, zone, htf_strength,
        structure, liquidity, order_flow, tf, df, point
    ) -> Optional[TradeSignal]:
        conditions = []
        score = 0.0

        # 1. SSL swept (liquidity sweep below lows)
        if liquidity.ssl_swept:
            score += 25
            conditions.append("SSL swept")
        else:
            return None   # mandatory for CRT+TS long

        # 2. Structure shift UP
        if structure.last_choch and "UP" in structure.last_choch.kind:
            score += 20
            conditions.append("CHOCH_UP")
        elif structure.last_bos and "UP" in structure.last_bos.kind:
            score += 15
            conditions.append("BOS_UP")
        else:
            return None   # mandatory

        # 3. Order flow bullish
        if order_flow.flow_score > 55:
            score += 15
            conditions.append("OF bullish")

        # 4. HTF strength
        score += htf_strength * 20

        # 5. Zone strength
        score += min(zone.strength, 10) * 2   # max 20

        # 6. Demand zone bonus
        if zone.retests == 0:
            score += 10
            conditions.append("Fresh zone")

        # ---- SL / TP ----
        sl = zone.bottom - 5 * point * 10
        risk = price - sl
        if risk <= 0:
            return None

        tp1 = price + risk * 1.5
        tp2 = price + risk * 3.0
        rr  = (tp1 - price) / risk

        if rr < MIN_RR_RATIO:
            return None

        return TradeSignal(
            symbol=symbol, direction="BUY",
            entry_price=price, stop_loss=sl,
            take_profit_1=tp1, take_profit_2=tp2,
            rr_ratio=rr, confidence=min(score, 100),
            timeframe=tf,
            reason=" | ".join(conditions),
            zone=zone,
            metadata={
                "htf_strength": htf_strength,
                "of_score": order_flow.flow_score,
                "zone_strength": zone.strength,
                "sweep_score": liquidity.sweep_score,
            }
        )

    # ------------------------------------------------------------------
    # BUILD SHORT SIGNAL
    # ------------------------------------------------------------------
    def _build_short(
        self, symbol, price, zone, htf_strength,
        structure, liquidity, order_flow, tf, df, point
    ) -> Optional[TradeSignal]:
        conditions = []
        score = 0.0

        if liquidity.bsl_swept:
            score += 25
            conditions.append("BSL swept")
        else:
            return None

        if structure.last_choch and "DOWN" in structure.last_choch.kind:
            score += 20
            conditions.append("CHOCH_DOWN")
        elif structure.last_bos and "DOWN" in structure.last_bos.kind:
            score += 15
            conditions.append("BOS_DOWN")
        else:
            return None

        if order_flow.flow_score < 45:
            score += 15
            conditions.append("OF bearish")

        score += htf_strength * 20
        score += min(zone.strength, 10) * 2

        if zone.retests == 0:
            score += 10
            conditions.append("Fresh zone")

        sl  = zone.top + 5 * point * 10
        risk = sl - price
        if risk <= 0:
            return None

        tp1 = price - risk * 1.5
        tp2 = price - risk * 3.0
        rr  = (price - tp1) / risk

        if rr < MIN_RR_RATIO:
            return None

        return TradeSignal(
            symbol=symbol, direction="SELL",
            entry_price=price, stop_loss=sl,
            take_profit_1=tp1, take_profit_2=tp2,
            rr_ratio=rr, confidence=min(score, 100),
            timeframe=tf,
            reason=" | ".join(conditions),
            zone=zone,
            metadata={
                "htf_strength": htf_strength,
                "of_score": order_flow.flow_score,
                "zone_strength": zone.strength,
                "sweep_score": liquidity.sweep_score,
            }
        )
