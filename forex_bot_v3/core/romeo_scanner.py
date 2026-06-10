"""
==============================================================================
ROMEO SCANNER — Full ICT Model Scanner
==============================================================================
Replaces the old scanner with the Romeo ICT approach.

Flow:
  1. Check killzone (time filter — first and most important)
  2. Determine HTF bias (D1/H4/H1)
  3. Detect liquidity sweep on entry TF
  4. Confirm energetic MSS with displacement
  5. Find FVG entry
  6. Score with S&D zones as confluence
  7. AI filter
  8. Return signal
"""

from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from config.settings import (
    CANDLES_REQUIRED, AI_MIN_SCORE,
    SESSIONS, TRADE_ALLOWED_SESSIONS,
    REGIME_ENGINE_ENABLED, NEWS_FILTER_ENABLED,
    CORRELATION_CHECK_ENABLED,
    GOLD_SYMBOL, GOLD_PRIORITY_HOURS, GOLD_PRIORITY_WINDOW,
)
from market_structure.analyzer import MarketStructureAnalyzer
from strategy.supply_demand import SupplyDemandEngine
from strategy.romeo_ict_strategy import (
    RomeoICTStrategy, RomeoSignal,
    is_in_killzone, get_current_killzone, _is_dst,
    KILLZONES_UTC, KILLZONES_UTC_DST
)

log = get_logger("core.romeo_scanner")

# Direction balance — max 2 BUY or 2 SELL simultaneously
MAX_SAME_DIRECTION = 2

# Symbols that trade 24/7
ALWAYS_ON_SYMBOLS = ["BTCUSDm","ETHUSDm","XAUUSDm","XAGUSDm"]

# AI threshold by killzone
AI_THRESHOLD_BY_KILLZONE = {
    "silver_bullet": 48,   # Highest priority window — slightly relaxed AI
    "ny_am":         50,
    "london_open":   52,
}


class RomeoScanner:
    """
    Full Romeo ICT scanner.
    Uses RomeoICTStrategy as the signal engine.
    """

    def __init__(self, mt5, ai):
        self._mt5    = mt5
        self._ai     = ai
        self._ms     = MarketStructureAnalyzer()
        self._sd     = SupplyDemandEngine()
        self._romeo  = RomeoICTStrategy()
        self._regime = None
        self._news   = None
        self._corr   = None

        if REGIME_ENGINE_ENABLED:
            try:
                from core.regime_engine import RegimeEngine
                self._regime = RegimeEngine()
            except Exception as e:
                log.warning("RegimeEngine: %s", e)

        if NEWS_FILTER_ENABLED:
            try:
                from core.news_filter import NewsFilter
                self._news = NewsFilter()
            except Exception as e:
                log.warning("NewsFilter: %s", e)

        if CORRELATION_CHECK_ENABLED:
            try:
                from core.correlation_engine import CorrelationEngine
                self._corr = CorrelationEngine()
            except Exception as e:
                log.warning("CorrelationEngine: %s", e)

    def scan(self, symbol: str,
             open_positions: List[Dict] = None) -> Optional[RomeoSignal]:

        open_positions = open_positions or []

        # ── KILLZONE CHECK — #1 PRIORITY ────────────────────────────────
        # Always-on symbols (crypto/gold) can trade outside killzone
        # but signals DURING killzone get higher confidence
        killzone = get_current_killzone()
        is_always_on = symbol in ALWAYS_ON_SYMBOLS

        if killzone is None and not is_always_on:
            # Outside killzone and not a 24/7 symbol
            return None

        # ── NEWS FILTER ─────────────────────────────────────────────────
        if self._news:
            try:
                ns = self._news.get_state(symbol)
                if not ns.should_trade:
                    log.debug("[%s] News block: %s", symbol, ns.state)
                    return None
            except: pass

        # ── SYMBOL INFO ─────────────────────────────────────────────────
        sym_info = self._mt5.get_symbol_info(symbol)
        if sym_info is None: return None
        point = sym_info["point"]

        tick = self._mt5.get_tick(symbol)
        if tick is None: return None
        current_price = tick["bid"]

        # ── HTF BIAS (D1 → H4 → H1) ────────────────────────────────────
        bias_results = {}
        htf_frames   = ["D1","H4","H1"]
        for tf in htf_frames:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is not None and len(df) >= 20:
                bias_results[tf] = self._ms.analyze(df, symbol, tf)

        htf_bias, htf_strength = self._agg_bias(bias_results)
        if htf_bias == "neutral" or htf_strength < 0.50:
            return None

        # ── DIRECTION BALANCE ────────────────────────────────────────────
        buys  = sum(1 for p in open_positions if p.get("type")=="BUY")
        sells = sum(1 for p in open_positions if p.get("type")=="SELL")
        if htf_bias=="bullish"  and buys  >= MAX_SAME_DIRECTION: return None
        if htf_bias=="bearish"  and sells >= MAX_SAME_DIRECTION: return None

        # ── CORRELATION CHECK ────────────────────────────────────────────
        if self._corr and open_positions:
            try:
                dir_check = "BUY" if htf_bias=="bullish" else "SELL"
                cc = self._corr.check(symbol, dir_check, open_positions)
                if not cc.allowed: return None
            except: pass

        # ── HTF DATA FOR CONTEXT ─────────────────────────────────────────
        df_h1  = self._mt5.get_candles(symbol, "H1", CANDLES_REQUIRED)
        df_h4  = self._mt5.get_candles(symbol, "H4", CANDLES_REQUIRED)
        df_htf = df_h4 if df_h4 is not None else df_h1

        # ── S&D ZONES (confluence only) ──────────────────────────────────
        all_zones = []
        for ztf in ["D1","H4","H1"]:
            df_z = self._mt5.get_candles(symbol, ztf, CANDLES_REQUIRED)
            if df_z is not None:
                try:
                    all_zones.extend(
                        self._sd.detect_zones(df_z, timeframe=ztf, point=point)
                    )
                except: pass

        # ── ENTRY TIMEFRAME SCAN ─────────────────────────────────────────
        # Romeo uses M5/M15 primarily, M30/H1 for wider setups
        entry_tfs = ["M5","M15","M30"]
        if is_always_on:
            entry_tfs = ["M5","M15","M30","H1"]

        for entry_tf in entry_tfs:
            df_entry = self._mt5.get_candles(symbol, entry_tf, CANDLES_REQUIRED)
            if df_entry is None or len(df_entry) < 30: continue

            # Run Romeo ICT strategy
            try:
                signal = self._romeo.generate_signal(
                    symbol=symbol,
                    higher_tf_bias=htf_bias,
                    higher_tf_strength=htf_strength,
                    current_price=current_price,
                    point=point,
                    df_htf=df_htf,
                    df_entry=df_entry,
                    entry_tf=entry_tf,
                    zones=all_zones,
                )
            except Exception as e:
                log.error("[%s %s] Romeo signal error: %s", symbol, entry_tf, e)
                continue

            if signal is None: continue

            # ── AI SCORING ───────────────────────────────────────────────
            atr = float((df_entry["high"]-df_entry["low"]).tail(14).mean())
            features = {
                "htf_bias_score":    1.0 if htf_bias=="bullish" else -1.0,
                "htf_strength":      htf_strength,
                "structure_strength":0.8,   # Romeo always has MSS
                "entry_tf_bias":     1.0,
                "zone_strength":     signal.zone.strength if signal.zone else 0.0,
                "zone_retests":      signal.zone.retests  if signal.zone else 2,
                "ssl_swept":         signal.sweep.kind=="LOW_SWEPT",
                "bsl_swept":         signal.sweep.kind=="HIGH_SWEPT",
                "of_score":          65.0,  # Romeo entries are high quality
                "sweep_score":       signal.sweep.strength,
                "rr_ratio":          signal.rr_ratio,
                "session_encoded":   self._session_enc(killzone or "other"),
                "volatility_norm":   min(atr/(current_price+1e-9)*100, 1.0),
                "confidence_raw":    signal.confidence,
                "zone_freshness":    signal.zone.fresh if signal.zone else True,
            }

            ai_score = self._ai.score_signal(features)
            signal.ai_score = ai_score
            signal.metadata["features"] = features
            signal.metadata["htf_bias"] = htf_bias
            signal.metadata["regime"]   = "TRENDING_UP" if htf_bias=="bullish" else "TRENDING_DOWN"
            signal.metadata["session"]  = killzone or "other"

            # Threshold by killzone
            threshold = AI_THRESHOLD_BY_KILLZONE.get(killzone or "other", AI_MIN_SCORE)
            if is_always_on: threshold -= 3

            if ai_score < threshold:
                log.debug("[%s %s] AI=%.1f < %d — skip",
                          symbol, entry_tf, ai_score, threshold)
                continue

            log.info(
                "[%s %s] ✅ ROMEO APPROVED: %s | AI=%.1f | KZ=%s | "
                "Sweep=%s | Disp=%.2fx | FVG=%.1fpips",
                symbol, entry_tf, signal.direction,
                ai_score, killzone,
                signal.sweep.kind,
                signal.mss.displacement,
                signal.fvg.size_pips,
            )
            return signal

        return None

    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _agg_bias(bias_results: Dict) -> tuple:
        scores  = {"bullish":0.0,"bearish":0.0}
        weights = {"D1":4,"H4":3,"H1":2}
        for tf,res in bias_results.items():
            w = weights.get(tf,1)
            if res.bias in scores:
                scores[res.bias] += w * res.strength
        bull  = scores["bullish"]
        bear  = scores["bearish"]
        total = bull + bear + 1e-9
        if bull > bear and bull/total > 0.55:
            return "bullish", round(bull/total, 3)
        if bear > bull and bear/total > 0.55:
            return "bearish", round(bear/total, 3)
        return "neutral", 0.0

    @staticmethod
    def _session_enc(kz: str) -> int:
        return {"london_open":1,"ny_am":2,"silver_bullet":3,"other":0}.get(kz, 0)
