"""
==============================================================================
RISK MANAGER
==============================================================================
Handles:
  • Dynamic lot sizing (% risk per trade)
  • Maximum daily drawdown enforcement
  • Maximum simultaneous open positions
  • Maximum total exposure control
  • RR validation
  • TP1 partial close tracking
  • Break-even SL management
"""

from typing import Optional, List, Dict
from datetime import datetime, date
import math

from core.logger import get_logger
from config.settings import (
    RISK_PER_TRADE_PCT, MAX_DAILY_DRAWDOWN_PCT, MAX_OPEN_POSITIONS,
    MAX_TOTAL_EXPOSURE_PCT, MIN_RR_RATIO, TP1_CLOSE_PCT,
    DEFAULT_TP1_RR, DEFAULT_TP2_RR, MAGIC_NUMBER
)

log = get_logger("risk.manager")


class RiskManager:

    def __init__(self) -> None:
        self._day_start_balance: float = 0.0
        self._day_start_date: Optional[date] = None
        self._daily_loss: float = 0.0

    # ------------------------------------------------------------------
    # LOT SIZING
    # ------------------------------------------------------------------
    def calculate_lot_size(
        self,
        balance: float,
        sl_pips: float,
        symbol_info: Dict,
        risk_pct: float = RISK_PER_TRADE_PCT,
    ) -> float:
        """
        Calculate lot size so that SL hit = risk_pct% of balance.

        Formula:
            risk_amount = balance * risk_pct / 100
            pip_value   = (pip_size / price) * contract_size
            lots        = risk_amount / (sl_pips * pip_value)
        """
        if sl_pips <= 0 or balance <= 0:
            return 0.0

        risk_amount   = balance * risk_pct / 100
        contract_size = symbol_info.get("trade_contract_size", 100_000)
        point         = symbol_info.get("point", 0.0001)
        pip_size      = point * 10          # 1 pip = 10 points for 5-digit brokers
        digits        = symbol_info.get("digits", 5)

        # Pip value in account currency (approximate — assumes USD-based account)
        pip_value_per_lot = pip_size * contract_size

        lots = risk_amount / (sl_pips * pip_value_per_lot)

        # Snap to broker step
        vol_step = symbol_info.get("volume_step", 0.01)
        vol_min  = symbol_info.get("volume_min",  0.01)
        vol_max  = symbol_info.get("volume_max",  100.0)

        lots = math.floor(lots / vol_step) * vol_step
        lots = max(vol_min, min(vol_max, lots))

        log.debug("Lot size: balance=%.2f risk_pct=%.1f sl_pips=%.1f → lots=%.2f",
                  balance, risk_pct, sl_pips, lots)
        return round(lots, 2)

    # ------------------------------------------------------------------
    # DRAWDOWN GUARD
    # ------------------------------------------------------------------
    def update_balance_tracking(self, current_balance: float) -> None:
        today = date.today()
        if self._day_start_date != today:
            self._day_start_balance = current_balance
            self._day_start_date    = today
            self._daily_loss        = 0.0
            log.info("New trading day. Start balance: %.2f", current_balance)

    def is_drawdown_exceeded(self, current_equity: float) -> bool:
        if self._day_start_balance <= 0:
            return False
        daily_loss_pct = (self._day_start_balance - current_equity) / self._day_start_balance * 100
        if daily_loss_pct >= MAX_DAILY_DRAWDOWN_PCT:
            log.warning("Daily drawdown exceeded: %.2f%% (max %.2f%%)",
                        daily_loss_pct, MAX_DAILY_DRAWDOWN_PCT)
            return True
        return False

    # ------------------------------------------------------------------
    # POSITION LIMITS
    # ------------------------------------------------------------------
    def can_open_new_trade(
        self,
        open_positions: List[Dict],
        symbol: str,
        balance: float,
        equity: float,
    ) -> bool:
        # Max positions
        if len(open_positions) >= MAX_OPEN_POSITIONS:
            log.info("Max open positions (%d) reached.", MAX_OPEN_POSITIONS)
            return False

        # No duplicate symbol
        open_symbols = [p["symbol"] for p in open_positions]
        if symbol in open_symbols:
            log.info("Symbol %s already has an open position.", symbol)
            return False

        # Drawdown guard
        if self.is_drawdown_exceeded(equity):
            return False

        # Total exposure
        total_profit_loss = sum(p["profit"] for p in open_positions)
        exposure_pct = abs(total_profit_loss) / (balance + 1e-9) * 100
        if exposure_pct >= MAX_TOTAL_EXPOSURE_PCT:
            log.info("Max exposure %.1f%% reached.", MAX_TOTAL_EXPOSURE_PCT)
            return False

        return True

    # ------------------------------------------------------------------
    # TP / SL UTILITIES
    # ------------------------------------------------------------------
    @staticmethod
    def sl_pips(entry: float, sl: float, point: float) -> float:
        return abs(entry - sl) / (point * 10)

    @staticmethod
    def validate_rr(entry: float, sl: float, tp: float) -> float:
        risk   = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0.0
        return reward / risk

    @staticmethod
    def break_even_sl(entry: float, direction: str, be_buffer_pips: float, point: float) -> float:
        """Return a break-even SL price."""
        buf = be_buffer_pips * point * 10
        if direction == "BUY":
            return entry + buf
        return entry - buf

    # ------------------------------------------------------------------
    # PARTIAL CLOSE VOLUME
    # ------------------------------------------------------------------
    @staticmethod
    def tp1_close_volume(original_volume: float, vol_step: float) -> float:
        """Volume to close at TP1 (50%)."""
        half = original_volume * TP1_CLOSE_PCT / 100
        half = math.floor(half / vol_step) * vol_step
        return max(half, vol_step)
