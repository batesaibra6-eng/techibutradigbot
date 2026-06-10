"""
==============================================================================
06 — TRADE LEARNING ENGINE
==============================================================================
Tracks and learns from EVERY trade outcome:

Stores per trade:
  • entry_reason, regime, session, spread, atr, news_state
  • outcome, rr_achieved, pips, duration
  • All AI features

Analytics it generates:
  • Best session per symbol
  • Best sweep type (BSL/SSL)
  • Best pair overall
  • Best regime to trade
  • Worst conditions to avoid
  • Feature importance tracking
  • Win rate by category

Also does Walk-Forward Optimization (lite):
  • Tests different AI thresholds on historical data
  • Recommends optimal threshold
"""

import json
import sqlite3
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from core.logger import get_logger

log = get_logger("trade_learning_engine")

DB_PATH = "storage/trading_bot.db"


@dataclass
class LearningInsight:
    best_session:      str
    best_pair:         str
    best_regime:       str
    best_sweep_type:   str
    worst_session:     str
    worst_pair:        str
    worst_regime:      str
    optimal_ai_score:  float
    win_rate_overall:  float
    avg_rr_achieved:   float
    total_trades:      int
    feature_importance: Dict[str, float]


class TradeLearningEngine:

    def __init__(self, db_path: str = DB_PATH) -> None:
        self._db = db_path
        self._ensure_tables()

    # ──────────────────────────────────────────────────────────────────────────
    # RECORD TRADE
    # ──────────────────────────────────────────────────────────────────────────
    def record_trade(
        self,
        ticket:       int,
        symbol:       str,
        direction:    str,
        entry_reason: str,
        regime:       str,
        session:      str,
        atr:          float,
        news_state:   str,
        ai_score:     float,
        features:     Dict,
        outcome:      str,    # "TP1"|"TP2"|"TP3"|"SL"|"BE"|"MANUAL"
        rr_achieved:  float,
        pips:         float,
        spread:       float = 0.0,
    ) -> None:
        with self._conn() as c:
            c.execute("""
            INSERT OR REPLACE INTO trade_analytics
                (ticket, symbol, direction, entry_reason, regime, session,
                 atr, news_state, ai_score, features, outcome,
                 rr_achieved, pips, spread, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                ticket, symbol, direction, entry_reason, regime, session,
                atr, news_state, ai_score, json.dumps(features), outcome,
                rr_achieved, pips, spread,
                str(datetime.utcnow()),
            ))
        log.info("Trade recorded: ticket=%d outcome=%s rr=%.2f", ticket, outcome, rr_achieved)

    # ──────────────────────────────────────────────────────────────────────────
    # GENERATE INSIGHTS
    # ──────────────────────────────────────────────────────────────────────────
    def get_insights(self) -> Optional[LearningInsight]:
        trades = self._load_trades()
        if len(trades) < 10:
            log.info("Not enough trades for insights (%d)", len(trades))
            return None

        # ── WIN RATE BY CATEGORY ─────────────────────────────────────────────
        def win_rate_by(key):
            groups = defaultdict(list)
            for t in trades:
                groups[t.get(key, "unknown")].append(
                    1 if t.get("outcome") in ("TP1","TP2","TP3") else 0
                )
            return {k: (sum(v)/len(v)*100, len(v)) for k, v in groups.items() if len(v) >= 3}

        session_wr = win_rate_by("session")
        pair_wr    = win_rate_by("symbol")
        regime_wr  = win_rate_by("regime")
        reason_wr  = win_rate_by("entry_reason")

        # Best/worst
        best_session = max(session_wr, key=lambda x: session_wr[x][0], default="london")
        worst_session= min(session_wr, key=lambda x: session_wr[x][0], default="asian")
        best_pair    = max(pair_wr,    key=lambda x: pair_wr[x][0],    default="XAUUSD")
        worst_pair   = min(pair_wr,    key=lambda x: pair_wr[x][0],    default="NZDJPY")
        best_regime  = max(regime_wr,  key=lambda x: regime_wr[x][0],  default="TRENDING_UP")
        worst_regime = min(regime_wr,  key=lambda x: regime_wr[x][0],  default="HIGH_VOLATILITY")

        # Best sweep type
        ssl_wins = sum(1 for t in trades if "SSL swept" in t.get("entry_reason","") and t.get("outcome") in ("TP1","TP2"))
        bsl_wins = sum(1 for t in trades if "BSL swept" in t.get("entry_reason","") and t.get("outcome") in ("TP1","TP2"))
        best_sweep = "SSL" if ssl_wins >= bsl_wins else "BSL"

        # Overall stats
        outcomes = [t.get("outcome") for t in trades]
        wins     = sum(1 for o in outcomes if o in ("TP1","TP2","TP3"))
        wr_overall = wins / len(trades) * 100

        rr_vals = [t.get("rr_achieved", 0) for t in trades if t.get("rr_achieved")]
        avg_rr  = float(np.mean(rr_vals)) if rr_vals else 0.0

        # Feature importance (correlation with outcome)
        feature_imp = self._feature_importance(trades)

        # Walk-forward optimal threshold
        optimal_score = self._walkforward_threshold(trades)

        insight = LearningInsight(
            best_session=best_session,
            best_pair=best_pair,
            best_regime=best_regime,
            best_sweep_type=best_sweep,
            worst_session=worst_session,
            worst_pair=worst_pair,
            worst_regime=worst_regime,
            optimal_ai_score=optimal_score,
            win_rate_overall=round(wr_overall, 1),
            avg_rr_achieved=round(avg_rr, 2),
            total_trades=len(trades),
            feature_importance=feature_imp,
        )

        log.info("Insights: best=%s/%s/%s wr=%.1f%% ai_threshold=%.1f",
                 best_session, best_pair, best_regime, wr_overall, optimal_score)
        return insight

    def format_telegram_report(self, insight: LearningInsight) -> str:
        """Format insights for Telegram."""
        fi = insight.feature_importance
        top_features = sorted(fi.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        fi_text = " | ".join([f"{k}:{v:+.2f}" for k, v in top_features])
        return (
            f"🧠 *LEARNING ENGINE REPORT*\n\n"
            f"📊 Trades Analysed: `{insight.total_trades}`\n"
            f"✅ Win Rate: `{insight.win_rate_overall}%`\n"
            f"💰 Avg RR: `{insight.avg_rr_achieved}R`\n\n"
            f"🏆 *BEST CONDITIONS*\n"
            f"Session: `{insight.best_session}`\n"
            f"Pair:    `{insight.best_pair}`\n"
            f"Regime:  `{insight.best_regime}`\n"
            f"Sweep:   `{insight.best_sweep_type}`\n\n"
            f"⚠️ *AVOID*\n"
            f"Session: `{insight.worst_session}`\n"
            f"Pair:    `{insight.worst_pair}`\n"
            f"Regime:  `{insight.worst_regime}`\n\n"
            f"🤖 Optimal AI Score: `{insight.optimal_ai_score}`\n"
            f"📈 Top Features: `{fi_text}`"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # WALK-FORWARD THRESHOLD OPTIMIZATION
    # ──────────────────────────────────────────────────────────────────────────
    def _walkforward_threshold(self, trades: List[Dict]) -> float:
        """Find AI score threshold that maximizes risk-adjusted return."""
        if len(trades) < 20:
            return 52.0

        best_score = 52.0
        best_metric = -999

        for threshold in range(40, 75, 2):
            subset = [t for t in trades if t.get("ai_score", 0) >= threshold]
            if len(subset) < 5:
                continue
            wins   = sum(1 for t in subset if t.get("outcome") in ("TP1","TP2","TP3"))
            wr     = wins / len(subset)
            rr_vals= [t.get("rr_achieved", 0) for t in subset if t.get("rr_achieved")]
            avg_rr = float(np.mean(rr_vals)) if rr_vals else 0
            # Metric: win rate × avg_rr × sqrt(trade_count)
            metric = wr * avg_rr * (len(subset) ** 0.5)
            if metric > best_metric:
                best_metric = metric
                best_score  = float(threshold)

        log.info("Walk-forward optimal threshold: %.1f", best_score)
        return best_score

    # ──────────────────────────────────────────────────────────────────────────
    # FEATURE IMPORTANCE
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _feature_importance(trades: List[Dict]) -> Dict[str, float]:
        """Correlation of each feature with win outcome."""
        importance = {}
        outcomes = np.array([1 if t.get("outcome") in ("TP1","TP2","TP3") else 0
                             for t in trades], dtype=float)
        feature_names = [
            "htf_strength", "structure_strength", "of_score",
            "zone_strength", "sweep_score", "rr_ratio",
            "volatility_norm", "confidence_raw"
        ]
        for feat in feature_names:
            vals = []
            for t in trades:
                f = t.get("features") or {}
                if isinstance(f, str):
                    try: f = json.loads(f)
                    except: f = {}
                vals.append(f.get(feat, 0))
            vals = np.array(vals, dtype=float)
            if vals.std() > 0:
                corr = float(np.corrcoef(vals, outcomes)[0, 1])
                importance[feat] = round(corr, 3)

        return dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True))

    # ──────────────────────────────────────────────────────────────────────────
    # DB HELPERS
    # ──────────────────────────────────────────────────────────────────────────
    def _ensure_tables(self) -> None:
        os.makedirs(os.path.dirname(self._db) if os.path.dirname(self._db) else ".", exist_ok=True)
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS trade_analytics (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket       INTEGER UNIQUE,
                symbol       TEXT,
                direction    TEXT,
                entry_reason TEXT,
                regime       TEXT,
                session      TEXT,
                atr          REAL,
                news_state   TEXT,
                ai_score     REAL,
                features     TEXT,
                outcome      TEXT,
                rr_achieved  REAL,
                pips         REAL,
                spread       REAL,
                created_at   TEXT
            )""")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_trades(self) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM trade_analytics").fetchall()
            return [dict(r) for r in rows]
