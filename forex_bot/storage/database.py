"""
==============================================================================
STORAGE — SQLite Database
==============================================================================
Tables:
  • signals          — all generated signals
  • trades           — executed trades + outcomes
  • ai_training_data — feature vectors + labels for AI retraining
  • market_snapshots — structure/zone snapshots per symbol/tf
  • daily_stats      — daily performance
  • weekly_stats     — weekly performance
"""

import sqlite3
import json
import os
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from core.logger import get_logger
from config.settings import DB_PATH

log = get_logger("storage.database")


class Database:

    def __init__(self, path: str = DB_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._path = path
        self._init_tables()

    # ------------------------------------------------------------------
    # INITIALISE TABLES
    # ------------------------------------------------------------------
    def _init_tables(self) -> None:
        with self._conn() as conn:
            c = conn.cursor()
            c.executescript("""
            CREATE TABLE IF NOT EXISTS signals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT,
                direction   TEXT,
                entry_price REAL,
                stop_loss   REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                rr_ratio    REAL,
                confidence  REAL,
                ai_score    REAL,
                timeframe   TEXT,
                reason      TEXT,
                metadata    TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS trades (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket       INTEGER UNIQUE,
                signal_id    INTEGER,
                symbol       TEXT,
                direction    TEXT,
                volume       REAL,
                entry_price  REAL,
                stop_loss    REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                close_price  REAL,
                profit       REAL,
                outcome      TEXT,   -- "TP1" | "TP2" | "SL" | "MANUAL"
                open_time    TEXT,
                close_time   TEXT,
                pips         REAL,
                ai_score     REAL,
                features     TEXT,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS ai_training_data (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id  INTEGER,
                features  TEXT,
                label     INTEGER,   -- 1=win, 0=loss
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS market_snapshots (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol    TEXT,
                timeframe TEXT,
                bias      TEXT,
                strength  REAL,
                zones     TEXT,
                snapshot  TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS daily_stats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date   TEXT UNIQUE,
                total_trades INTEGER,
                wins         INTEGER,
                losses       INTEGER,
                win_rate     REAL,
                net_pnl      REAL,
                balance      REAL,
                max_drawdown REAL,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS weekly_stats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_week   TEXT UNIQUE,
                total_trades INTEGER,
                wins         INTEGER,
                losses       INTEGER,
                win_rate     REAL,
                net_pnl      REAL,
                max_drawdown REAL,
                created_at   TEXT DEFAULT (datetime('now'))
            );
            """)
        log.info("Database initialised at %s", self._path)

    # ------------------------------------------------------------------
    # CONNECTION
    # ------------------------------------------------------------------
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------------
    def save_signal(self, signal: Dict) -> int:
        sql = """
        INSERT INTO signals
            (symbol, direction, entry_price, stop_loss, take_profit_1, take_profit_2,
             rr_ratio, confidence, ai_score, timeframe, reason, metadata)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(sql, (
                signal["symbol"], signal["direction"],
                signal["entry_price"], signal["stop_loss"],
                signal["take_profit_1"], signal["take_profit_2"],
                signal["rr_ratio"], signal["confidence"],
                signal["ai_score"], signal["timeframe"],
                signal["reason"],
                json.dumps(signal.get("metadata", {})),
            ))
            return c.lastrowid

    # ------------------------------------------------------------------
    # TRADES
    # ------------------------------------------------------------------
    def save_trade(self, trade: Dict) -> int:
        sql = """
        INSERT OR REPLACE INTO trades
            (ticket, signal_id, symbol, direction, volume, entry_price,
             stop_loss, take_profit_1, take_profit_2, open_time, ai_score, features)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(sql, (
                trade["ticket"], trade.get("signal_id"),
                trade["symbol"], trade["direction"], trade["volume"],
                trade["entry_price"], trade["stop_loss"],
                trade["take_profit_1"], trade["take_profit_2"],
                str(trade.get("open_time", datetime.utcnow())),
                trade.get("ai_score", 0),
                json.dumps(trade.get("features", {})),
            ))
            return c.lastrowid

    def update_trade_close(self, ticket: int, close_price: float, profit: float,
                           outcome: str, close_time: Optional[str] = None, pips: float = 0.0) -> None:
        with self._conn() as conn:
            conn.execute("""
            UPDATE trades SET close_price=?, profit=?, outcome=?, close_time=?, pips=?
            WHERE ticket=?
            """, (close_price, profit, outcome, close_time or str(datetime.utcnow()), pips, ticket))

    def get_open_trades(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE close_price IS NULL"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_trade_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]

    def get_labelled_trades(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT features, outcome FROM trades WHERE outcome IS NOT NULL AND features IS NOT NULL"
            ).fetchall()
            result = []
            for r in rows:
                features = json.loads(r["features"] or "{}")
                label = 1 if r["outcome"] in ("TP1", "TP2") else 0
                result.append({"features": features, "outcome": label})
            return result

    # ------------------------------------------------------------------
    # AI TRAINING DATA
    # ------------------------------------------------------------------
    def save_training_sample(self, trade_id: int, features: Dict, label: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO ai_training_data (trade_id, features, label) VALUES (?,?,?)",
                (trade_id, json.dumps(features), label)
            )

    # ------------------------------------------------------------------
    # DAILY STATS
    # ------------------------------------------------------------------
    def upsert_daily_stats(self, stats: Dict) -> None:
        with self._conn() as conn:
            conn.execute("""
            INSERT INTO daily_stats
                (stat_date, total_trades, wins, losses, win_rate, net_pnl, balance, max_drawdown)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(stat_date) DO UPDATE SET
                total_trades=excluded.total_trades, wins=excluded.wins,
                losses=excluded.losses, win_rate=excluded.win_rate,
                net_pnl=excluded.net_pnl, balance=excluded.balance,
                max_drawdown=excluded.max_drawdown
            """, (
                stats["date"], stats["total_trades"], stats["wins"],
                stats["losses"], stats["win_rate"], stats["net_pnl"],
                stats["balance"], stats.get("max_drawdown", 0),
            ))

    def get_daily_stats(self, stat_date: Optional[str] = None) -> Optional[Dict]:
        d = stat_date or str(date.today())
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM daily_stats WHERE stat_date=?", (d,)
            ).fetchone()
            return dict(row) if row else None

    def get_todays_trades(self) -> List[Dict]:
        today = str(date.today())
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE DATE(open_time)=?", (today,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # MARKET SNAPSHOTS
    # ------------------------------------------------------------------
    def save_snapshot(self, symbol: str, timeframe: str, bias: str,
                      strength: float, zones: list, snapshot: Dict) -> None:
        with self._conn() as conn:
            conn.execute("""
            INSERT INTO market_snapshots (symbol, timeframe, bias, strength, zones, snapshot)
            VALUES (?,?,?,?,?,?)
            """, (symbol, timeframe, bias, strength,
                  json.dumps(zones), json.dumps(snapshot)))
