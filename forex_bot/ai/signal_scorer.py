"""
==============================================================================
AI ENGINE — XGBoost Signal Scorer
==============================================================================
Responsibilities:
  1. Score every signal 0-100 using XGBoost
  2. Fall back to rule-based scoring if model not trained yet
  3. Learn from TP / SL outcomes stored in the database
  4. Retrain automatically after every N new labelled trades
  5. Bootstrap with synthetic data to start immediately

Feature vector (15 features):
  [0]  htf_bias_score          (0=neutral, 1=bullish, -1=bearish)
  [1]  htf_strength            (0-1)
  [2]  structure_strength      (0-1)
  [3]  entry_tf_bias_score     (0-1)
  [4]  zone_strength           (0-10 → normalised 0-1)
  [5]  zone_retests            (0-3+)
  [6]  ssl_swept               (bool)
  [7]  bsl_swept               (bool)
  [8]  of_score                (0-100 → normalised 0-1)
  [9]  sweep_score             (0-1)
  [10] rr_ratio                (1.0 - 5.0+)
  [11] session_encoded         (0=asian, 1=london, 2=ny, 3=overlap)
  [12] volatility_norm         (ATR / price → 0-1)
  [13] confidence_raw          (rule engine confidence 0-100 → 0-1)
  [14] zone_freshness          (1=fresh, 0=retested)
"""

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.logger import get_logger
from config.settings import (
    AI_MODE, AI_MIN_SCORE, AI_RETRAIN_AFTER_TRADES,
    AI_SYNTHETIC_SAMPLES
)

log = get_logger("ai.signal_scorer")

MODEL_PATH = "storage/ai_model.pkl"

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    log.warning("XGBoost not installed — rule-based fallback will be used.")


def _build_synthetic_data(n: int = 500):
    """
    Generate synthetic training data to bootstrap the model.
    Winning trades have higher feature values; losers have lower.
    """
    rng = np.random.default_rng(42)

    winners = n // 2
    losers  = n - winners

    def gen(label: int, count: int):
        if label == 1:   # winners
            rows = np.column_stack([
                rng.choice([1], count),               # htf_bias: bullish=1
                rng.uniform(0.6, 1.0,  count),        # htf_strength
                rng.uniform(0.6, 1.0,  count),        # structure_strength
                rng.uniform(0.5, 1.0,  count),        # entry_tf_bias
                rng.uniform(0.6, 1.0,  count),        # zone_strength (norm)
                rng.integers(0, 2,     count),        # zone_retests
                rng.integers(1, 2,     count),        # ssl_swept
                rng.integers(0, 2,     count),        # bsl_swept
                rng.uniform(0.6, 1.0,  count),        # of_score (norm)
                rng.uniform(0.5, 1.0,  count),        # sweep_score
                rng.uniform(1.5, 4.0,  count),        # rr_ratio
                rng.integers(1, 4,     count),        # session
                rng.uniform(0.0, 0.5,  count),        # volatility
                rng.uniform(0.65,1.0,  count),        # confidence
                rng.integers(1, 2,     count),        # freshness
            ])
        else:            # losers
            rows = np.column_stack([
                rng.choice([0, -1], count),
                rng.uniform(0.1, 0.5,  count),
                rng.uniform(0.1, 0.5,  count),
                rng.uniform(0.0, 0.5,  count),
                rng.uniform(0.0, 0.5,  count),
                rng.integers(2, 4,     count),
                rng.integers(0, 2,     count),
                rng.integers(0, 2,     count),
                rng.uniform(0.0, 0.5,  count),
                rng.uniform(0.0, 0.4,  count),
                rng.uniform(1.0, 2.0,  count),
                rng.integers(0, 4,     count),
                rng.uniform(0.5, 1.0,  count),
                rng.uniform(0.0, 0.5,  count),
                rng.integers(0, 2,     count),
            ])
        labels = np.full(count, label, dtype=int)
        return rows, labels

    X_win, y_win = gen(1, winners)
    X_los, y_los = gen(0, losers)
    X = np.vstack([X_win, X_los])
    y = np.concatenate([y_win, y_los])
    shuffle = rng.permutation(len(y))
    return X[shuffle], y[shuffle]


class AISignalScorer:

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._trained = False
        self._load_or_bootstrap()

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def _load_or_bootstrap(self) -> None:
        if not XGB_AVAILABLE:
            log.info("XGBoost unavailable — using rule-based scoring only.")
            return

        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self._model = pickle.load(f)
                self._trained = True
                log.info("AI model loaded from %s", MODEL_PATH)
                return
            except Exception as e:
                log.warning("Failed to load model: %s — will retrain.", e)

        # Bootstrap with synthetic data
        log.info("Bootstrapping AI model with %d synthetic samples…", AI_SYNTHETIC_SAMPLES)
        X, y = _build_synthetic_data(AI_SYNTHETIC_SAMPLES)
        self._train_model(X, y)

    def _train_model(self, X: np.ndarray, y: np.ndarray) -> None:
        if not XGB_AVAILABLE:
            return
        try:
            model = XGBClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X, y)
            self._model = model
            self._trained = True
            os.makedirs("storage", exist_ok=True)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(model, f)
            log.info("AI model trained and saved. Samples=%d", len(y))
        except Exception as e:
            log.error("Model training failed: %s", e)

    # ------------------------------------------------------------------
    # SCORING
    # ------------------------------------------------------------------
    def score_signal(self, features: Dict[str, float]) -> float:
        """
        Score a signal using XGBoost or rule-based fallback.
        Returns a score 0-100.
        """
        vec = self._build_feature_vector(features)

        if self._trained and self._model is not None:
            try:
                prob = self._model.predict_proba([vec])[0][1]
                score = float(prob * 100)
                log.debug("AI score: %.1f (prob=%.3f)", score, prob)
                return round(score, 2)
            except Exception as e:
                log.warning("XGBoost prediction failed: %s — using rule fallback", e)

        return self._rule_based_score(features)

    @staticmethod
    def _build_feature_vector(f: Dict[str, float]) -> List[float]:
        return [
            f.get("htf_bias_score",      0.0),
            f.get("htf_strength",        0.0),
            f.get("structure_strength",  0.0),
            f.get("entry_tf_bias",       0.0),
            f.get("zone_strength",       0.0) / 10,
            f.get("zone_retests",        0.0),
            float(f.get("ssl_swept",     False)),
            float(f.get("bsl_swept",     False)),
            f.get("of_score",            50.0) / 100,
            f.get("sweep_score",         0.0),
            f.get("rr_ratio",            1.5),
            f.get("session_encoded",     0.0),
            f.get("volatility_norm",     0.0),
            f.get("confidence_raw",      0.0) / 100,
            float(f.get("zone_freshness", True)),
        ]

    @staticmethod
    def _rule_based_score(f: Dict[str, float]) -> float:
        """Fallback scoring when XGBoost is unavailable."""
        score = 0.0
        score += f.get("htf_strength",       0.0) * 20
        score += f.get("structure_strength", 0.0) * 15
        score += float(f.get("ssl_swept", False)) * 15
        score += float(f.get("bsl_swept", False)) * 15
        score += (f.get("of_score", 50) - 50) / 50 * 10
        score += min(f.get("zone_strength", 0) / 10, 1) * 10
        score += float(f.get("zone_freshness", True)) * 5
        score += min(f.get("rr_ratio", 1.5) / 3, 1) * 10
        score += f.get("confidence_raw", 0) / 100 * 15
        return max(0.0, min(100.0, round(score, 2)))

    # ------------------------------------------------------------------
    # RETRAINING
    # ------------------------------------------------------------------
    def retrain(self, trades: List[Dict]) -> bool:
        """
        Retrain from labelled trade outcomes.
        trades: list of dicts with 'features' (dict) and 'outcome' (1/0)
        """
        if not XGB_AVAILABLE or len(trades) < 20:
            log.info("Insufficient data for retraining (%d trades).", len(trades))
            return False

        try:
            # Merge live data with synthetic bootstrap
            X_syn, y_syn = _build_synthetic_data(min(AI_SYNTHETIC_SAMPLES, 200))
            rows = []
            labels = []
            for t in trades:
                vec = self._build_feature_vector(t.get("features", {}))
                rows.append(vec)
                labels.append(int(t.get("outcome", 0)))

            X_live = np.array(rows)
            y_live = np.array(labels)

            X = np.vstack([X_syn, X_live])
            y = np.concatenate([y_syn, y_live])

            self._train_model(X, y)
            log.info("AI model retrained with %d live + %d synthetic samples.",
                     len(y_live), len(y_syn))
            return True
        except Exception as e:
            log.error("Retraining failed: %s", e)
            return False
