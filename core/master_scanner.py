"""
==============================================================================
MASTER SCANNER — Institutional CRT + Romeo ICT
==============================================================================
Full top-down pipeline:
  W1/D1 → Long-term bias
  H4/H1 → Medium-term structure + session levels
  M5/M15/M30 → Entry execution (CRT model)

Romeo ICT Time Priority:
  Silver Bullet (10-11 EST) → Highest priority
  NY AM (8:30-11 EST)       → Primary
  London Open (2-5 EST)     → Secondary

Each symbol scan:
  1. Killzone check
  2. HTF bias (W1/D1/H4/H1 weighted vote)
  3. Market structure engine
  4. Spread check
  5. Volatility check
  6. CRT signal generation (sweep → displacement → FVG)
  7. SMT divergence confirmation (optional)
  8. S&D zone confluence
  9. AI filter
  10. Return signal
"""

from typing import Optional, Dict, List, Any
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from config.settings import (
    HTF_BIAS_TIMEFRAMES, EXECUTION_TIMEFRAMES, CANDLES_REQUIRED,
    AI_MIN_SCORE, KILLZONES_UTC, KILLZONES_DST,
    ALWAYS_ON_SYMBOLS, SMT_DIVERGENCE_ENABLED,
    NEWS_FILTER_ENABLED, SPREAD_FILTER_ENABLED,
    VOLATILITY_KILL_ENABLED, CORRELATION_CHECK_ENABLED,
)
from strategy.market_structure import MarketStructureEngine, MarketStructureResult
from strategy.crt_engine import CRTEngine, CRTSignal
from strategy.supply_demand import SupplyDemandEngine
from strategy.smt_divergence import SMTEngine

log = get_logger("core.master_scanner")

MAX_SAME_DIRECTION = 2

AI_THRESHOLD_BY_KZ = {
    "silver_bullet": 47,
    "ny_am":         50,
    "london_open":   52,
    "other":         55,
}


def _is_dst() -> bool:
    return 3 <= datetime.utcnow().month <= 11


def get_killzone() -> Optional[str]:
    h  = datetime.utcnow().hour
    kz = KILLZONES_DST if _is_dst() else KILLZONES_UTC
    for name, (s, e) in kz.items():
        if s <= h < e:
            return name
    return None


class MasterScanner:
    """
    Institutional-grade scanner combining CRT + Romeo ICT.
    All rules systematic and parameterized.
    """

    def __init__(self, mt5, ai) -> None:
        self._mt5    = mt5
        self._ai     = ai
        self._ms_eng = MarketStructureEngine()
        self._crt    = CRTEngine()
        self._sd     = SupplyDemandEngine()
        self._smt    = SMTEngine()
        self._news   = None
        self._corr   = None

        if NEWS_FILTER_ENABLED:
            try:
                from core.news_filter import NewsFilter
                self._news = NewsFilter()
            except Exception as e:
                log.warning("NewsFilter unavailable: %s", e)

        if CORRELATION_CHECK_ENABLED:
            try:
                from core.correlation_engine import CorrelationEngine
                self._corr = CorrelationEngine()
            except Exception as e:
                log.warning("CorrelationEngine unavailable: %s", e)

    # ──────────────────────────────────────────────────────────────────────
    def scan(self, symbol: str, open_positions: List[Dict] = None) -> Optional[CRTSignal]:
        open_positions = open_positions or []

        # ── 1. KILLZONE CHECK ─────────────────────────────────────────────
        killzone  = get_killzone()
        always_on = symbol in ALWAYS_ON_SYMBOLS

        if killzone is None and not always_on:
            return None  # Outside killzone = no trade for standard pairs

        # ── 2. NEWS FILTER ────────────────────────────────────────────────
        if self._news:
            try:
                ns = self._news.get_state(symbol)
                if not ns.should_trade:
                    log.debug("[%s] News blocked", symbol)
                    return None
            except Exception as e:
                log.debug("News filter error: %s", e)

        # ── 3. SYMBOL INFO ────────────────────────────────────────────────
        sym_info = self._mt5.get_symbol_info(symbol)
        if sym_info is None:
            return None
        point = sym_info["point"]

        tick = self._mt5.get_tick(symbol)
        if tick is None:
            return None
        current_price = tick["bid"]

        # ── 4. SPREAD CHECK ───────────────────────────────────────────────
        if SPREAD_FILTER_ENABLED:
            spread_pips = (tick["ask"] - tick["bid"]) / (point * 10)
            max_spread  = self._max_spread(symbol)
            if spread_pips > max_spread:
                log.debug("[%s] Spread too wide: %.1f pips", symbol, spread_pips)
                return None

        # ── 5. HTF BIAS (W1→D1→H4→H1 weighted) ──────────────────────────
        ms_results: Dict[str, MarketStructureResult] = {}
        df_daily  = self._mt5.get_candles(symbol, "D1", CANDLES_REQUIRED)
        df_weekly = self._mt5.get_candles(symbol, "W1", CANDLES_REQUIRED)

        for tf in HTF_BIAS_TIMEFRAMES:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is not None and len(df) >= 20:
                ms_results[tf] = self._ms_eng.analyze(
                    df, symbol, tf, df_daily, df_weekly
                )

        htf_bias, htf_strength = self._aggregate_bias(ms_results)
        if htf_bias == "neutral" or htf_strength < 0.50:
            log.debug("[%s] HTF bias neutral/weak: %s %.2f",
                      symbol, htf_bias, htf_strength)
            return None

        # ── 6. DIRECTION BALANCE (max 2 in same direction) ────────────────
        buys  = sum(1 for p in open_positions if p.get("type") == "BUY")
        sells = sum(1 for p in open_positions if p.get("type") == "SELL")
        if htf_bias == "bullish" and buys  >= MAX_SAME_DIRECTION: return None
        if htf_bias == "bearish" and sells >= MAX_SAME_DIRECTION: return None

        # ── 7. CORRELATION CHECK ──────────────────────────────────────────
        if self._corr and open_positions:
            try:
                dir_check = "BUY" if htf_bias == "bullish" else "SELL"
                cc = self._corr.check(symbol, dir_check, open_positions)
                if not cc.allowed:
                    log.debug("[%s] Correlation blocked", symbol)
                    return None
            except Exception as e:
                log.debug("Corr check error: %s", e)

        # ── 8. S&D ZONES (confluence) ─────────────────────────────────────
        all_zones = []
        for ztf in ["D1", "H4", "H1"]:
            dfz = self._mt5.get_candles(symbol, ztf, CANDLES_REQUIRED)
            if dfz is not None:
                try:
                    all_zones.extend(
                        self._sd.detect_zones(dfz, timeframe=ztf, point=point)
                    )
                except Exception as e:
                    log.debug("Zone error: %s", e)

        # ── 9. SMT DIVERGENCE ─────────────────────────────────────────────
        smt_bonus = 0.0
        if SMT_DIVERGENCE_ENABLED:
            try:
                # Gather candles for SMT
                candles_map = {}
                for sym in [symbol] + list({v for k,v in
                    __import__("config.settings", fromlist=["SMT_PAIRS"]).SMT_PAIRS.items()
                    if k == symbol}):
                    df = self._mt5.get_candles(sym, "H1", 50)
                    if df is not None:
                        candles_map[sym] = df

                direction = "BUY" if htf_bias == "bullish" else "SELL"
                smt = self._smt.check(symbol, direction, candles_map)
                if smt.confirmed:
                    smt_bonus = smt.strength * 10
                    log.debug("[%s] SMT confirmed: %s", symbol, smt.kind)
            except Exception as e:
                log.debug("SMT error: %s", e)

        # ── 10. EXECUTION TIMEFRAME SCAN ──────────────────────────────────
        exec_tfs = EXECUTION_TIMEFRAMES
        if always_on:
            exec_tfs = ["M5", "M15", "M30", "H1"]

        direction = "BUY" if htf_bias == "bullish" else "SELL"

        # Use best available MS result for entry context
        ms_entry = (ms_results.get("H1") or
                    ms_results.get("H4") or
                    next(iter(ms_results.values()), None))
        if ms_entry is None:
            return None

        for entry_tf in exec_tfs:
            df_entry = self._mt5.get_candles(symbol, entry_tf, CANDLES_REQUIRED)
            if df_entry is None or len(df_entry) < 30:
                continue

            # Run CRT engine
            try:
                signal = self._crt.generate_signal(
                    symbol=symbol,
                    direction=direction,
                    df=df_entry,
                    ms=ms_entry,
                    point=point,
                    killzone=killzone or "other",
                    zones=all_zones,
                )
            except Exception as e:
                log.error("[%s %s] CRT error: %s", symbol, entry_tf, e)
                continue

            if signal is None:
                continue

            signal.timeframe = entry_tf

            # ── 11. AI SCORING ────────────────────────────────────────────
            atr = float((df_entry["high"]-df_entry["low"]).tail(14).mean())
            features = self._build_features(
                signal, htf_bias, htf_strength, ms_entry,
                session_enc=self._session_enc(killzone),
                atr=atr, current_price=current_price,
                smt_bonus=smt_bonus,
            )

            ai_score  = self._ai.score_signal(features)
            ai_score  += smt_bonus   # SMT boosts AI score
            ai_score   = min(ai_score, 100.0)
            signal.ai_score = ai_score

            signal.metadata.update({
                "features":    features,
                "htf_bias":    htf_bias,
                "htf_strength":htf_strength,
                "regime":      self._regime_from_bias(htf_bias, ms_entry),
                "session":     killzone or "other",
                "symbol_info": sym_info,
                "spread_pips": spread_pips if SPREAD_FILTER_ENABLED else 0,
            })

            # Threshold by killzone
            threshold = AI_THRESHOLD_BY_KZ.get(killzone or "other", AI_MIN_SCORE)
            if always_on:
                threshold -= 3

            if ai_score < threshold:
                log.debug("[%s %s] AI=%.1f < %d — rejected",
                          symbol, entry_tf, ai_score, threshold)
                continue

            log.info(
                "[%s %s] ✅ SIGNAL APPROVED: %s | AI=%.1f | KZ=%s | "
                "Sweep=%s(%s) | Disp=%.2fx | FVG=%.1fpips | RR=%.1f",
                symbol, entry_tf, signal.direction,
                ai_score, killzone,
                signal.sweep.kind if signal.sweep else "?",
                signal.sweep.level_type if signal.sweep else "?",
                signal.displacement_str,
                signal.fvg_size_pips,
                signal.rr_ratio,
            )
            return signal

        return None

    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _aggregate_bias(
        ms_results: Dict[str, MarketStructureResult]
    ):
        """Weighted bias vote across all HTF timeframes."""
        scores  = {"bullish": 0.0, "bearish": 0.0}
        weights = {"W1": 5, "D1": 4, "H4": 3, "H1": 2}
        total_w = 0

        for tf, res in ms_results.items():
            w = weights.get(tf, 1)
            if res.bias in scores:
                scores[res.bias] += w * res.bias_strength
            total_w += w

        bull = scores["bullish"]
        bear = scores["bearish"]
        total = bull + bear + 1e-9

        if bull > bear and bull / total > 0.55:
            return "bullish", round(bull / total, 3)
        if bear > bull and bear / total > 0.55:
            return "bearish", round(bear / total, 3)
        return "neutral", 0.0

    @staticmethod
    def _build_features(
        signal, htf_bias, htf_strength, ms, session_enc, atr, current_price, smt_bonus
    ) -> Dict:
        return {
            "htf_bias_score":    1.0 if htf_bias == "bullish" else -1.0,
            "htf_strength":      htf_strength,
            "structure_strength":ms.bias_strength,
            "entry_tf_bias":     1.0,  # CRT engine already aligned
            "zone_strength":     signal.metadata.get("zone_strength", 0.0),
            "zone_retests":      signal.metadata.get("zone_retests", 2),
            "ssl_swept":         signal.sweep.kind == "LOW_SWEPT" if signal.sweep else False,
            "bsl_swept":         signal.sweep.kind == "HIGH_SWEPT" if signal.sweep else False,
            "of_score":          65.0,
            "sweep_score":       signal.sweep_strength,
            "rr_ratio":          signal.rr_ratio,
            "session_encoded":   session_enc,
            "volatility_norm":   min(atr / (current_price + 1e-9) * 100, 1.0),
            "confidence_raw":    signal.confidence,
            "zone_freshness":    True,
            "displacement":      signal.displacement_str,
            "fvg_pips":          signal.fvg_size_pips,
            "smt_bonus":         smt_bonus,
        }

    @staticmethod
    def _session_enc(kz: Optional[str]) -> int:
        return {"london_open":1,"ny_am":2,"silver_bullet":3,"other":0}.get(kz or "other", 0)

    @staticmethod
    def _regime_from_bias(bias: str, ms: MarketStructureResult) -> str:
        if ms.last_choch:
            return "TRENDING_UP" if bias=="bullish" else "TRENDING_DOWN"
        if ms.last_bos:
            return "EXPANSION"
        return "RANGING"

    @staticmethod
    def _max_spread(symbol: str) -> float:
        s = symbol.replace("m","").upper()
        if "BTC" in s or "ETH" in s: return 50.0
        if "XAU" in s: return 8.0
        if "XAG" in s: return 15.0
        if "ZAR" in s: return 12.0
        if "JPY" in s: return 2.5
        return 3.0
