"""
==============================================================================
CORE — Trade Manager
==============================================================================
Manages the lifecycle of all open trades:
  • Execute new signals
  • Monitor open positions (TP1, TP2, SL, break-even)
  • Partial close at TP1
  • Trailing SL management (optional)
  • Log outcomes to database
  • Trigger Telegram notifications
  • Feed outcome data back to AI retraining queue
"""

from typing import Optional, Dict, List, Any
from datetime import datetime

from core.logger import get_logger
from config.settings import (
    RISK_PER_TRADE_PCT, DEFAULT_TP1_RR, DEFAULT_TP2_RR,
    AI_RETRAIN_AFTER_TRADES, SYMBOLS
)
from risk.manager import RiskManager
from storage.database import Database
from telegram.notifier import TelegramNotifier
from ai.signal_scorer import AISignalScorer
from strategy.crt_turtle_soup import TradeSignal

log = get_logger("core.trade_manager")


class TradeManager:

    def __init__(
        self,
        mt5_connector,
        risk_manager:  RiskManager,
        database:      Database,
        notifier:      TelegramNotifier,
        ai_scorer:     AISignalScorer,
    ) -> None:
        self._mt5     = mt5_connector
        self._risk    = risk_manager
        self._db      = database
        self._tg      = notifier
        self._ai      = ai_scorer

        # {ticket: trade_dict}  — in-memory tracking
        self._active: Dict[int, Dict] = {}
        self._tp1_done: set = set()   # tickets where TP1 partial close is done
        self._retrain_counter = 0

        # Restore from DB on startup
        self._restore_open_trades()

    # ------------------------------------------------------------------
    # EXECUTE SIGNAL
    # ------------------------------------------------------------------
    def execute_signal(self, signal: TradeSignal) -> bool:
        sym_info = self._mt5.get_symbol_info(signal.symbol)
        if sym_info is None:
            log.error("Cannot execute: symbol info unavailable for %s", signal.symbol)
            return False

        balance = self._mt5.get_balance()
        equity  = self._mt5.get_equity()
        open_positions = self._mt5.get_open_positions()

        # Risk gate
        if not self._risk.can_open_new_trade(open_positions, signal.symbol, balance, equity):
            log.info("Risk gate blocked trade for %s.", signal.symbol)
            return False

        self._risk.update_balance_tracking(balance)

        # Lot size
        sl_pips = self._risk.sl_pips(signal.entry_price, signal.stop_loss, sym_info["point"])
        volume  = self._risk.calculate_lot_size(balance, sl_pips, sym_info)
        if volume <= 0:
            log.error("Calculated lot size is 0 — aborting.")
            return False

        # Place order
        result = self._mt5.place_order(
            symbol=signal.symbol,
            order_type=signal.direction,
            volume=volume,
            sl=signal.stop_loss,
            tp=signal.take_profit_2,   # MT5 TP set to TP2; TP1 handled manually
            comment="FXBot-CRT",
        )
        if result is None:
            log.error("Order placement failed for %s.", signal.symbol)
            self._tg.error(f"Order failed: {signal.symbol} {signal.direction}")
            return False

        ticket = result["ticket"]

        # Save signal to DB
        signal_id = self._db.save_signal(signal.to_dict())

        # Save trade to DB
        trade_record = {
            "ticket":        ticket,
            "signal_id":     signal_id,
            "symbol":        signal.symbol,
            "direction":     signal.direction,
            "volume":        volume,
            "entry_price":   result["price"],
            "stop_loss":     signal.stop_loss,
            "take_profit_1": signal.take_profit_1,
            "take_profit_2": signal.take_profit_2,
            "open_time":     datetime.utcnow(),
            "ai_score":      signal.ai_score,
            "features":      signal.metadata.get("features", {}),
        }
        self._db.save_trade(trade_record)

        # In-memory tracking
        self._active[ticket] = trade_record

        # Telegram
        sig_dict = signal.to_dict()
        sig_dict["entry_price"] = result["price"]
        sig_dict["ai_score"]    = signal.ai_score
        self._tg.new_trade(sig_dict)

        log.info("Trade executed: %s %s ticket=%d lots=%.2f",
                 signal.direction, signal.symbol, ticket, volume)
        return True

    # ------------------------------------------------------------------
    # MONITOR OPEN POSITIONS
    # ------------------------------------------------------------------
    def monitor_positions(self) -> None:
        """Called every main loop cycle — checks TP1, SL, break-even."""
        open_positions = self._mt5.get_open_positions()
        live_tickets   = {p["ticket"] for p in open_positions}

        # Detect closed positions
        for ticket in list(self._active.keys()):
            if ticket not in live_tickets:
                self._handle_closed_position(ticket, open_positions)

        # Check TP1 for live positions
        for pos in open_positions:
            ticket = pos["ticket"]
            if ticket not in self._active:
                continue
            self._check_tp1(pos)

    # ------------------------------------------------------------------
    # TP1 PARTIAL CLOSE
    # ------------------------------------------------------------------
    def _check_tp1(self, pos: Dict) -> None:
        ticket  = pos["ticket"]
        if ticket in self._tp1_done:
            return

        trade   = self._active.get(ticket, {})
        tp1     = trade.get("take_profit_1", 0)
        if tp1 == 0:
            return

        current = pos["current_price"]
        direction = pos["type"]

        tp1_hit = (
            (direction == "BUY"  and current >= tp1) or
            (direction == "SELL" and current <= tp1)
        )
        if not tp1_hit:
            return

        sym_info = self._mt5.get_symbol_info(pos["symbol"])
        if sym_info is None:
            return

        vol_step = sym_info.get("volume_step", 0.01)
        close_vol = self._risk.tp1_close_volume(pos["volume"], vol_step)

        log.info("TP1 hit for ticket %d — partial close %.2f lots", ticket, close_vol)
        if self._mt5.close_position(ticket, volume=close_vol):
            self._tp1_done.add(ticket)
            # Move SL to break-even
            be_sl = self._risk.break_even_sl(
                trade["entry_price"], direction, be_buffer_pips=2,
                point=sym_info["point"]
            )
            self._mt5.modify_position(ticket, sl=be_sl)
            self._tg.tp_hit(ticket, pos["symbol"], 1, pos["profit"])

    # ------------------------------------------------------------------
    # HANDLE CLOSED POSITION
    # ------------------------------------------------------------------
    def _handle_closed_position(self, ticket: int, open_positions: List[Dict]) -> None:
        trade = self._active.pop(ticket, {})
        if not trade:
            return

        # Get deal history
        history = self._mt5.get_trade_history(days=1)
        deal = next((d for d in history if d["ticket"] == ticket), None)

        profit = deal["profit"] if deal else 0.0
        close_price = deal["price"] if deal else 0.0

        # Determine outcome
        tp1 = trade.get("take_profit_1", 0)
        tp2 = trade.get("take_profit_2", 0)
        sl  = trade.get("stop_loss", 0)
        direction = trade.get("direction", "BUY")

        if close_price and tp2:
            if direction == "BUY":
                outcome = "TP2" if close_price >= tp2 * 0.999 else ("TP1" if close_price >= tp1 * 0.999 else "SL")
            else:
                outcome = "TP2" if close_price <= tp2 * 1.001 else ("TP1" if close_price <= tp1 * 1.001 else "SL")
        elif profit >= 0:
            outcome = "TP1"
        else:
            outcome = "SL"

        # Pips
        entry = trade.get("entry_price", close_price)
        pips  = (close_price - entry) / (0.0001 * 10) if direction == "BUY" \
                else (entry - close_price) / (0.0001 * 10)

        # Update DB
        self._db.update_trade_close(ticket, close_price, profit, outcome, pips=pips)

        # Feed AI
        label = 1 if outcome in ("TP1", "TP2") else 0
        features = trade.get("features", {})
        self._db.save_training_sample(ticket, features, label)
        self._retrain_counter += 1

        # Telegram
        if outcome == "SL":
            self._tg.sl_hit(ticket, trade.get("symbol", ""), profit)
        else:
            self._tg.trade_closed(ticket, trade.get("symbol", ""), profit, pips)

        log.info("Trade closed: ticket=%d outcome=%s profit=%.2f pips=%.1f",
                 ticket, outcome, profit, pips)

        # Periodic AI retraining
        if self._retrain_counter >= AI_RETRAIN_AFTER_TRADES:
            self._trigger_retraining()
            self._retrain_counter = 0

    # ------------------------------------------------------------------
    # AI RETRAINING
    # ------------------------------------------------------------------
    def _trigger_retraining(self) -> None:
        log.info("Triggering AI retraining…")
        trades = self._db.get_labelled_trades()
        if len(trades) < 20:
            log.info("Too few trades for retraining (%d).", len(trades))
            return
        success = self._ai.retrain(trades)
        if success:
            acc = sum(1 for t in trades if t["outcome"] == 1) / len(trades) * 100
            self._tg.ai_retrained(len(trades), acc)

    # ------------------------------------------------------------------
    # RESTORE FROM DB
    # ------------------------------------------------------------------
    def _restore_open_trades(self) -> None:
        open_db = self._db.get_open_trades()
        for t in open_db:
            self._active[t["ticket"]] = t
        if open_db:
            log.info("Restored %d open trade(s) from database.", len(open_db))
