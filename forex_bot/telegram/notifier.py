"""
==============================================================================
TELEGRAM NOTIFIER
==============================================================================
Sends structured messages to a Telegram chat via Bot API.
Non-blocking — sends in a background thread to avoid slowing the main loop.
"""

import threading
import time
import requests
from datetime import datetime
from typing import Optional, Dict

from core.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = get_logger("telegram.notifier")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Emoji constants
E = {
    "rocket":   "🚀", "trade":    "📊", "win":      "✅",
    "loss":     "❌", "warn":     "⚠️", "info":     "ℹ️",
    "money":    "💰", "ai":       "🤖", "down":     "📉",
    "up":       "📈", "clock":    "🕐", "fire":     "🔥",
    "skull":    "💀", "shield":   "🛡️", "calendar": "📅",
}


class TelegramNotifier:

    def __init__(self) -> None:
        self._enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN")
        if not self._enabled:
            log.warning("Telegram token not configured — notifications disabled.")

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def startup(self, balance: float, account: int) -> None:
        msg = (
            f"{E['rocket']} *FOREX BOT STARTED*\n\n"
            f"Account: `{account}`\n"
            f"Balance: `${balance:,.2f}`\n"
            f"Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            f"Status: _All systems operational_ {E['shield']}"
        )
        self._send(msg)

    def mt5_connected(self, server: str) -> None:
        self._send(f"{E['info']} *MT5 Connected*\nServer: `{server}`")

    def new_trade(self, signal: Dict) -> None:
        d = signal["direction"]
        icon = E["up"] if d == "BUY" else E["down"]
        msg = (
            f"{icon}{E['trade']} *NEW TRADE*\n\n"
            f"Symbol:    `{signal['symbol']}`\n"
            f"Direction: `{d}`\n"
            f"Entry:     `{signal.get('entry_price', 0):.5f}`\n"
            f"SL:        `{signal.get('stop_loss', 0):.5f}`\n"
            f"TP1:       `{signal.get('take_profit_1', 0):.5f}`\n"
            f"TP2:       `{signal.get('take_profit_2', 0):.5f}`\n"
            f"RR:        `{signal.get('rr_ratio', 0):.1f}R`\n"
            f"AI Score:  `{signal.get('ai_score', 0):.1f}/100`\n"
            f"Reason:    _{signal.get('reason', '')}_\n"
            f"TF:        `{signal.get('timeframe', '')}`"
        )
        self._send(msg)

    def trade_closed(self, ticket: int, symbol: str, profit: float, pips: float) -> None:
        icon = E["win"] if profit >= 0 else E["loss"]
        msg = (
            f"{icon} *TRADE CLOSED*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"P&L:    `${profit:+.2f}`\n"
            f"Pips:   `{pips:+.1f}`"
        )
        self._send(msg)

    def tp_hit(self, ticket: int, symbol: str, tp_level: int, profit: float) -> None:
        msg = (
            f"{E['money']}{E['fire']} *TP{tp_level} HIT*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"Profit: `${profit:+.2f}`"
        )
        self._send(msg)

    def sl_hit(self, ticket: int, symbol: str, loss: float) -> None:
        msg = (
            f"{E['skull']} *SL HIT*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"Loss:   `${loss:+.2f}`"
        )
        self._send(msg)

    def daily_summary(self, stats: Dict) -> None:
        msg = (
            f"{E['calendar']} *DAILY SUMMARY*\n\n"
            f"Date:    `{stats.get('date', '')}`\n"
            f"Trades:  `{stats.get('total_trades', 0)}`\n"
            f"Wins:    `{stats.get('wins', 0)}` {E['win']}\n"
            f"Losses:  `{stats.get('losses', 0)}` {E['loss']}\n"
            f"Win Rate:`{stats.get('win_rate', 0):.1f}%`\n"
            f"Net P&L: `${stats.get('net_pnl', 0):+.2f}`\n"
            f"Balance: `${stats.get('balance', 0):,.2f}`"
        )
        self._send(msg)

    def weekly_summary(self, stats: Dict) -> None:
        msg = (
            f"{E['calendar']} *WEEKLY SUMMARY*\n\n"
            f"Week:     `{stats.get('week', '')}`\n"
            f"Trades:   `{stats.get('total_trades', 0)}`\n"
            f"Win Rate: `{stats.get('win_rate', 0):.1f}%`\n"
            f"Net P&L:  `${stats.get('net_pnl', 0):+.2f}`\n"
            f"Drawdown: `{stats.get('max_drawdown', 0):.2f}%`"
        )
        self._send(msg)

    def ai_retrained(self, samples: int, accuracy: float) -> None:
        self._send(
            f"{E['ai']} *AI MODEL RETRAINED*\n"
            f"Samples: `{samples}`\nAccuracy: `{accuracy:.1f}%`"
        )

    def error(self, message: str) -> None:
        self._send(f"{E['warn']} *ERROR*\n`{message}`")

    def warning(self, message: str) -> None:
        self._send(f"{E['warn']} *WARNING*\n_{message}_")

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------
    def _send(self, text: str) -> None:
        if not self._enabled:
            log.debug("Telegram [stub]: %s", text[:80])
            return
        threading.Thread(target=self._post, args=(text,), daemon=True).start()

    def _post(self, text: str, retries: int = 3) -> None:
        payload = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "Markdown",
        }
        for attempt in range(retries):
            try:
                r = requests.post(API_URL, json=payload, timeout=10)
                if r.status_code == 200:
                    return
                log.warning("Telegram API %d: %s", r.status_code, r.text[:100])
            except Exception as e:
                log.warning("Telegram send attempt %d failed: %s", attempt + 1, e)
            time.sleep(2 ** attempt)
