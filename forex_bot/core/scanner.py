"""
==============================================================================
CORE — Multi-Timeframe Scanner
==============================================================================
Orchestrates the entire analysis pipeline for one symbol:

  1. Fetch candles for all timeframes
  2. Run Market Structure on W1, D1, H4, H1  → bias
  3. Run Supply/Demand detection on H4, H1
  4. Iterate over entry TFs (M30, M15, M5):
       a. Market Structure (entry TF)
       b. Liquidity Engine
       c. Order Flow Engine
       d. CRT + Turtle Soup signal generation
       e. AI scoring
       f. Return signal if AI score ≥ threshold
"""

from typing import Optional, Dict, List, Any
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from config.settings import (
    BIAS_TIMEFRAMES, ENTRY_TIMEFRAMES, AI_MIN_SCORE,
    SESSIONS, TRADE_ALLOWED_SESSIONS, CANDLES_REQUIRED
)
from market_structure.analyzer import MarketStructureAnalyzer, MarketStructureResult
from strategy.supply_demand import SupplyDemandEngine, Zone
from liquidity.engine import LiquidityEngine
from order_flow.engine import OrderFlowEngine
from strategy.crt_turtle_soup import CRTTurtleSoupStrategy, TradeSignal
from ai.signal_scorer import AISignalScorer

log = get_logger("core.scanner")


def _current_session() -> str:
    hour = datetime.utcnow().hour
    for name, (start, end) in SESSIONS.items():
        if start <= hour < end:
            return name
    return "other"


def _session_encoded(session: str) -> int:
    return {"asian": 0, "london": 1, "newyork": 2, "overlap": 3}.get(session, 0)


class Scanner:
    """
    Runs top-down multi-timeframe analysis for a single symbol.
    """

    def __init__(
        self,
        mt5_connector,
        ai_scorer: AISignalScorer,
    ) -> None:
        self._mt5    = mt5_connector
        self._ai     = ai_scorer
        self._ms     = MarketStructureAnalyzer()
        self._sd     = SupplyDemandEngine()
        self._liq    = LiquidityEngine()
        self._of     = OrderFlowEngine()
        self._strat  = CRTTurtleSoupStrategy()

    # ------------------------------------------------------------------
    def scan(self, symbol: str) -> Optional[TradeSignal]:
        """
        Full top-down scan.  Returns a TradeSignal or None.
        """
        session = _current_session()
        if session not in TRADE_ALLOWED_SESSIONS:
            log.debug("[%s] Outside trading session (%s) — skip.", symbol, session)
            return None

        sym_info = self._mt5.get_symbol_info(symbol)
        if sym_info is None:
            log.warning("[%s] Could not get symbol info.", symbol)
            return None
        point = sym_info["point"]

        # ── 1. HIGHER TF BIAS ─────────────────────────────────────────
        bias_results: Dict[str, MarketStructureResult] = {}
        for tf in BIAS_TIMEFRAMES:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is None or len(df) < 20:
                log.debug("[%s %s] Insufficient data.", symbol, tf)
                continue
            bias_results[tf] = self._ms.analyze(df, symbol, tf)

        htf_bias, htf_strength = self._aggregate_bias(bias_results)
        if htf_bias == "neutral":
            log.debug("[%s] HTF bias neutral — skip.", symbol)
            return None

        # ── 2. SUPPLY / DEMAND ZONES (H4 + H1) ───────────────────────
        all_zones: List[Zone] = []
        for tf in ["H4", "H1"]:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is not None:
                zones = self._sd.detect_zones(df, timeframe=tf, point=point)
                all_zones.extend(zones)

        if not all_zones:
            log.debug("[%s] No valid zones found.", symbol)
            return None

        # ── 3. ENTRY TIMEFRAME ANALYSIS ───────────────────────────────
        for entry_tf in ENTRY_TIMEFRAMES:
            df = self._mt5.get_candles(symbol, entry_tf, CANDLES_REQUIRED)
            if df is None or len(df) < 30:
                continue

            tick = self._mt5.get_tick(symbol)
            if tick is None:
                continue
            current_price = tick["bid"]

            # Market structure on entry TF
            entry_ms = self._ms.analyze(df, symbol, entry_tf)

            # Liquidity analysis
            liq = self._liq.analyze(df, entry_tf)

            # Order flow
            of = self._of.analyze(df, entry_tf)

            # Signal generation
            signal = self._strat.generate_signal(
                symbol=symbol,
                higher_tf_bias=htf_bias,
                higher_tf_strength=htf_strength,
                zones=all_zones,
                current_price=current_price,
                point=point,
                entry_structure=entry_ms,
                liquidity=liq,
                order_flow=of,
                entry_tf=entry_tf,
                entry_df=df,
            )

            if signal is None:
                continue

            # ── 4. AI SCORING ─────────────────────────────────────────
            features = self._build_features(
                signal, htf_bias, htf_strength,
                entry_ms, liq, of, session, df, point
            )
            ai_score = self._ai.score_signal(features)
            signal.ai_score = ai_score
            signal.metadata["features"] = features
            signal.metadata["session"]  = session

            if ai_score < AI_MIN_SCORE:
                log.info("[%s %s] Signal rejected by AI: score=%.1f < %.1f",
                         symbol, entry_tf, ai_score, AI_MIN_SCORE)
                continue

            log.info(
                "[%s %s] SIGNAL APPROVED: %s ai=%.1f conf=%.1f reason=%s",
                symbol, entry_tf, signal.direction,
                ai_score, signal.confidence, signal.reason
            )
            return signal

        return None

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _aggregate_bias(
        bias_results: Dict[str, MarketStructureResult]
    ):
        """Vote across higher TF results to produce a single bias."""
        scores = {"bullish": 0.0, "bearish": 0.0}
        weights = {"W1": 4, "D1": 3, "H4": 2, "H1": 1}

        for tf, res in bias_results.items():
            w = weights.get(tf, 1)
            if res.bias in scores:
                scores[res.bias] += w * res.strength

        if scores["bullish"] > scores["bearish"] * 1.2:
            strength = scores["bullish"] / (scores["bullish"] + scores["bearish"] + 1e-9)
            return "bullish", strength
        if scores["bearish"] > scores["bullish"] * 1.2:
            strength = scores["bearish"] / (scores["bullish"] + scores["bearish"] + 1e-9)
            return "bearish", strength
        return "neutral", 0.0

    @staticmethod
    def _build_features(
        signal: TradeSignal,
        htf_bias: str,
        htf_strength: float,
        entry_ms: MarketStructureResult,
        liq,
        of_result,
        session: str,
        df: pd.DataFrame,
        point: float,
    ) -> Dict[str, float]:
        """Build the 15-feature vector for AI scoring."""
        htf_bias_score = 1.0 if htf_bias == "bullish" else -1.0

        atr = (df["high"] - df["low"]).tail(14).mean()
        price = df["close"].iloc[-1]
        vol_norm = min(atr / (price + 1e-9) * 100, 1.0)

        zone = signal.zone
        return {
            "htf_bias_score":     htf_bias_score,
            "htf_strength":       htf_strength,
            "structure_strength": entry_ms.strength,
            "entry_tf_bias":      1.0 if entry_ms.bias == htf_bias else 0.0,
            "zone_strength":      zone.strength if zone else 0.0,
            "zone_retests":       zone.retests  if zone else 3,
            "ssl_swept":          liq.ssl_swept,
            "bsl_swept":          liq.bsl_swept,
            "of_score":           of_result.flow_score,
            "sweep_score":        liq.sweep_score,
            "rr_ratio":           signal.rr_ratio,
            "session_encoded":    _session_encoded(session),
            "volatility_norm":    vol_norm,
            "confidence_raw":     signal.confidence,
            "zone_freshness":     zone.fresh if zone else False,
        }
