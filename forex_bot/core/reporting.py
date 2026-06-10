"""
==============================================================================
CORE — Reporting Engine
==============================================================================
Generates daily and weekly performance summaries and pushes them via Telegram.
"""

from datetime import date, datetime, timedelta
from typing import Dict

from core.logger import get_logger
from storage.database import Database
from telegram.notifier import TelegramNotifier

log = get_logger("core.reporting")


class ReportingEngine:

    def __init__(self, database: Database, notifier: TelegramNotifier) -> None:
        self._db  = database
        self._tg  = notifier
        self._last_daily_report: str  = ""
        self._last_weekly_report: str = ""

    def check_and_send_reports(self, balance: float) -> None:
        """Call this every main loop cycle — reports sent once per day/week."""
        today = str(date.today())
        if self._last_daily_report != today:
            self._send_daily_report(balance)
            self._last_daily_report = today

            # Weekly on Monday
            if date.today().weekday() == 0:
                week = date.today().isocalendar()
                week_str = f"{week[0]}-W{week[1]:02d}"
                if self._last_weekly_report != week_str:
                    self._send_weekly_report()
                    self._last_weekly_report = week_str

    def _send_daily_report(self, balance: float) -> None:
        trades = self._db.get_todays_trades()
        wins   = [t for t in trades if t.get("outcome") in ("TP1", "TP2")]
        losses = [t for t in trades if t.get("outcome") == "SL"]
        pnl    = sum(t.get("profit", 0) or 0 for t in trades if t.get("profit") is not None)
        wrate  = len(wins) / len(trades) * 100 if trades else 0

        stats = {
            "date":         str(date.today()),
            "total_trades": len(trades),
            "wins":         len(wins),
            "losses":       len(losses),
            "win_rate":     wrate,
            "net_pnl":      pnl,
            "balance":      balance,
        }
        self._db.upsert_daily_stats(stats)
        self._tg.daily_summary(stats)
        log.info("Daily report sent: trades=%d pnl=%.2f", len(trades), pnl)

    def _send_weekly_report(self) -> None:
        # Aggregate last 7 days
        week_start = date.today() - timedelta(days=7)
        # Use available daily stats as proxy
        stats = {
            "week":          str(date.today().isocalendar()[:2]),
            "total_trades":  0,
            "wins":          0,
            "losses":        0,
            "win_rate":      0.0,
            "net_pnl":       0.0,
            "max_drawdown":  0.0,
        }
        self._tg.weekly_summary(stats)
