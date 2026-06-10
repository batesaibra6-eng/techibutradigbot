"""
==============================================================================
INSTITUTIONAL FOREX TRADING BOT
Main Entry Point
==============================================================================
Autonomous 24/7 operation:
  • Connects to MT5
  • Scans all symbols on every loop
  • Executes signals that pass AI and risk filters
  • Monitors open positions (TP1, SL, break-even)
  • Sends Telegram notifications
  • Generates daily / weekly reports
  • Auto-reconnects on failure
  • Handles crashes gracefully
==============================================================================
"""

import os
import sys
import time
import signal
import traceback
from datetime import datetime

# ── Ensure package root is on path ────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.logger    import get_logger
from config         import settings
from mt5.connector  import MT5Connector
from core.scanner   import Scanner
from core.trade_manager import TradeManager
from core.reporting import ReportingEngine
from risk.manager   import RiskManager
from storage.database import Database
from telegram.notifier import TelegramNotifier
from ai.signal_scorer  import AISignalScorer

log = get_logger("main")

# ── Graceful shutdown flag ─────────────────────────────────────────────────
_RUNNING = True

def _handle_shutdown(signum, frame):
    global _RUNNING
    log.info("Shutdown signal received (%s). Stopping…", signum)
    _RUNNING = False

signal.signal(signal.SIGINT,  _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)


# ===========================================================================
class ForexBot:
    """Top-level orchestrator for the Institutional Forex Trading Bot."""

    def __init__(self) -> None:
        log.info("=" * 70)
        log.info("  INSTITUTIONAL FOREX BOT — INITIALISING")
        log.info("=" * 70)

        # Core services
        self.db       = Database()
        self.notifier = TelegramNotifier()
        self.mt5      = MT5Connector()
        self.risk     = RiskManager()
        self.ai       = AISignalScorer()

        self.scanner  = None   # built after MT5 connect
        self.trader   = None
        self.reporter = None

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Connect to MT5 and start the main loop."""
        if not self._connect_mt5():
            log.critical("Unable to connect to MT5. Exiting.")
            sys.exit(1)

        # Build scanner and trade manager after connection
        self.scanner  = Scanner(self.mt5, self.ai)
        self.trader   = TradeManager(self.mt5, self.risk, self.db, self.notifier, self.ai)
        self.reporter = ReportingEngine(self.db, self.notifier)

        # Startup notification
        acct = self.mt5.get_account_info()
        if acct:
            self.notifier.startup(acct["balance"], acct["login"])

        log.info("Bot started. Symbols: %s", settings.SYMBOLS)
        log.info("Scanning every %d seconds.", settings.MAIN_LOOP_INTERVAL_SEC)

        self._main_loop()

    # ------------------------------------------------------------------
    # MAIN LOOP
    # ------------------------------------------------------------------
    def _main_loop(self) -> None:
        global _RUNNING
        consecutive_errors = 0

        while _RUNNING:
            loop_start = time.time()

            try:
                self._cycle()
                consecutive_errors = 0

            except KeyboardInterrupt:
                log.info("KeyboardInterrupt — stopping.")
                break

            except Exception as exc:
                consecutive_errors += 1
                tb = traceback.format_exc()
                log.error("Unhandled exception in main loop:\n%s", tb)
                self.notifier.error(f"Loop error #{consecutive_errors}: {exc}")

                if consecutive_errors >= 5:
                    log.critical("Too many consecutive errors — attempting MT5 reconnect.")
                    self._reconnect_mt5()
                    consecutive_errors = 0

            # Sleep remainder of interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, settings.MAIN_LOOP_INTERVAL_SEC - elapsed)
            time.sleep(sleep_time)

        # Shutdown
        self._shutdown()

    # ------------------------------------------------------------------
    # ONE ANALYSIS CYCLE
    # ------------------------------------------------------------------
    def _cycle(self) -> None:
        if not self.mt5.is_connected():
            log.warning("MT5 not connected — attempting reconnect.")
            self._reconnect_mt5()
            return

        acct = self.mt5.get_account_info()
        if acct is None:
            return

        balance = acct["balance"]
        equity  = acct["equity"]

        # Update risk tracking
        self.risk.update_balance_tracking(balance)

        # Drawdown kill switch
        if self.risk.is_drawdown_exceeded(equity):
            log.warning("Daily drawdown limit hit — no new trades today.")
            self.notifier.warning(
                f"Daily drawdown limit reached. Balance: ${balance:.2f} | Equity: ${equity:.2f}"
            )
            # Still monitor existing positions
            self.trader.monitor_positions()
            return

        # Monitor open trades (TP1, break-even, closed detection)
        self.trader.monitor_positions()

        # Scan symbols for new signals
        open_positions = self.mt5.get_open_positions()
        open_symbols   = {p["symbol"] for p in open_positions}

        for symbol in settings.SYMBOLS:
            if symbol in open_symbols:
                log.debug("[%s] Already has open position — skip scan.", symbol)
                continue

            try:
                signal = self.scanner.scan(symbol)
                if signal is not None:
                    self.trader.execute_signal(signal)
            except Exception as e:
                log.error("[%s] Scan error: %s", symbol, e)

        # Reports (daily / weekly)
        self.reporter.check_and_send_reports(balance)

        log.debug("Cycle complete. Balance=%.2f Equity=%.2f OpenPos=%d",
                  balance, equity, len(open_positions))

    # ------------------------------------------------------------------
    # MT5 CONNECTION MANAGEMENT
    # ------------------------------------------------------------------
    def _connect_mt5(self) -> bool:
        return self.mt5.connect()

    def _reconnect_mt5(self) -> bool:
        log.info("Attempting MT5 reconnect…")
        self.mt5.disconnect()
        time.sleep(5)
        ok = self.mt5.reconnect()
        if ok:
            self.notifier.mt5_connected(settings.MT5_SERVER)
        else:
            self.notifier.error("MT5 reconnect failed — retrying next cycle.")
        return ok

    # ------------------------------------------------------------------
    # GRACEFUL SHUTDOWN
    # ------------------------------------------------------------------
    def _shutdown(self) -> None:
        log.info("Shutting down bot…")
        self.mt5.disconnect()
        log.info("MT5 disconnected.")
        log.info("Bot stopped cleanly.")


# ===========================================================================
if __name__ == "__main__":
    # Optional: load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
        log.info(".env loaded.")
    except ImportError:
        pass

    bot = ForexBot()
    bot.start()
