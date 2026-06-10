# ==============================================================================
# FOREX BOT V2 — FULL UPDATE SCRIPT
# Run this on your VPS PowerShell as Administrator
# ==============================================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  FOREX BOT V2 — APPLYING ALL UPGRADES" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Stop old bot
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Write-Host "[1/8] Old bot stopped." -ForegroundColor Yellow

# ── SETTINGS.PY ──────────────────────────────────────────────────────────────
@'
import os
from typing import List, Dict

MT5_LOGIN    = int(os.getenv("MT5_LOGIN",    "436005794"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD",     "1234#Dt@")
MT5_SERVER   = os.getenv("MT5_SERVER",       "Exness-MT5Trial9")
MT5_PATH     = os.getenv("MT5_PATH",         r"C:\Program Files\MetaTrader 5\terminal64.exe")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8664218080:AAFIO77O-qyEds2C2gD55Lq2hSBNeKmm6B4")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "-1003781184008")

# ── 24 PAIRS ─────────────────────────────────────────────────────────────────
SYMBOLS: List[str] = [
    # Majors
    "EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
    # Crosses
    "EURJPY","GBPJPY","EURGBP","EURAUD","EURCAD",
    "GBPAUD","GBPCAD","GBPCHF","AUDCAD","AUDJPY",
    "CADJPY","CHFJPY","NZDJPY",
    # Metals
    "XAUUSD","XAGUSD",
    # Crypto
    "BTCUSD","ETHUSD",
]

# ── GOLD SPECIAL SESSIONS (UTC) ───────────────────────────────────────────────
GOLD_SYMBOL          = "XAUUSD"
GOLD_PRIORITY_HOURS  = [5, 8]   # 5AM and 8AM UTC — critical gold setups
GOLD_PRIORITY_WINDOW = 2        # ±2 hours around those times

# ── TIMEFRAMES ───────────────────────────────────────────────────────────────
BIAS_TIMEFRAMES   = ["W1", "D1", "H4", "H1"]
ENTRY_TIMEFRAMES  = ["H4", "H1", "M30", "M15", "M5"]   # Added H4 and H1 entries

# ── RISK — MICRO ACCOUNT FRIENDLY ─────────────────────────────────────────────
RISK_PER_TRADE_PCT        = 1.0
MAX_DAILY_DRAWDOWN_PCT    = 4.0
MAX_OPEN_POSITIONS        = 5
MAX_TOTAL_EXPOSURE_PCT    = 8.0
MIN_RR_RATIO              = 1.5
DEFAULT_TP1_RR            = 1.5
DEFAULT_TP2_RR            = 3.0
TP1_CLOSE_PCT             = 50
MAGIC_NUMBER              = 88888

# Micro account settings (auto-detected)
MICRO_ACCOUNT_THRESHOLD   = 500    # accounts below $500 use micro settings
MICRO_RISK_PCT            = 1.0    # same % but lot size floored to minimum
MIN_LOT_SIZE              = 0.01   # absolute minimum

# ── TRAILING STOP ─────────────────────────────────────────────────────────────
TRAILING_STOP_ENABLED     = True
TRAILING_STOP_ACTIVATION  = 1.0    # activate after 1R profit
TRAILING_STOP_DISTANCE    = 0.5    # trail by 0.5R

# ── STRUCTURE ─────────────────────────────────────────────────────────────────
STRUCTURE_LOOKBACK        = 50
SWING_SENSITIVITY         = 5
EQUAL_LEVEL_TOLERANCE     = 0.0003
ZONE_LOOKBACK             = 100
ZONE_MIN_STRENGTH         = 2      # lowered from 3 for more signals
ZONE_MAX_RETESTS          = 3
ZONE_EXTENSION_PIPS       = 5
LIQUIDITY_LOOKBACK        = 30
SWEEP_CONFIRMATION_BARS   = 2
OF_LOOKBACK               = 20

# ── AI ────────────────────────────────────────────────────────────────────────
AI_MODE                   = "xgboost"
AI_MIN_SCORE              = 52     # slightly relaxed for more signals
AI_RETRAIN_AFTER_TRADES   = 30    # retrain faster
AI_SYNTHETIC_SAMPLES      = 500

# ── SESSIONS ──────────────────────────────────────────────────────────────────
SESSIONS = {
    "london":  (7, 16),
    "newyork": (12, 21),
    "asian":   (0,  9),
    "overlap": (12, 16),
}
TRADE_ALLOWED_SESSIONS = ["london", "newyork", "overlap", "asian"]

# ── BACKTEST ──────────────────────────────────────────────────────────────────
BACKTEST_ENABLED          = True
BACKTEST_LOOKBACK_BARS    = 500    # bars to backtest on startup

# ── MISC ──────────────────────────────────────────────────────────────────────
DB_PATH                   = "storage/trading_bot.db"
LOG_DIR                   = "logs"
LOG_LEVEL                 = "INFO"
LOG_MAX_BYTES             = 10 * 1024 * 1024
LOG_BACKUP_COUNT          = 5
MAIN_LOOP_INTERVAL_SEC    = 45     # faster scanning
RECONNECT_DELAY_SEC       = 30
MAX_RECONNECT_ATTEMPTS    = 10
CANDLES_REQUIRED          = 300
'@ | Out-File -FilePath "C:\ForexBot\config\settings.py" -Encoding UTF8
Write-Host "[2/8] settings.py updated — 24 pairs!" -ForegroundColor Green

# ── TRAILING STOP MODULE ──────────────────────────────────────────────────────
@'
"""
Trailing Stop Manager
Activates after TRAILING_STOP_ACTIVATION R profit
Trails price by TRAILING_STOP_DISTANCE R
"""
from core.logger import get_logger
from config.settings import TRAILING_STOP_ENABLED, TRAILING_STOP_ACTIVATION, TRAILING_STOP_DISTANCE

log = get_logger("risk.trailing_stop")

class TrailingStopManager:

    def __init__(self, mt5_connector):
        self._mt5 = mt5_connector
        self._peaks = {}   # ticket -> best price seen

    def update(self, positions):
        if not TRAILING_STOP_ENABLED:
            return
        for pos in positions:
            ticket    = pos["ticket"]
            direction = pos["type"]
            entry     = pos["open_price"]
            current   = pos["current_price"]
            sl        = pos["sl"]
            sym_info  = self._mt5.get_symbol_info(pos["symbol"])
            if sym_info is None:
                continue
            point = sym_info["point"]
            risk  = abs(entry - sl) if sl else 0
            if risk == 0:
                continue

            profit_r = (current - entry) / risk if direction == "BUY" else (entry - current) / risk

            # Only activate trailing after ACTIVATION threshold
            if profit_r < TRAILING_STOP_ACTIVATION:
                continue

            # Track peak price
            if ticket not in self._peaks:
                self._peaks[ticket] = current
            else:
                if direction == "BUY":
                    self._peaks[ticket] = max(self._peaks[ticket], current)
                else:
                    self._peaks[ticket] = min(self._peaks[ticket], current)

            peak = self._peaks[ticket]

            # Calculate new trailing SL
            trail_distance = risk * TRAILING_STOP_DISTANCE
            if direction == "BUY":
                new_sl = round(peak - trail_distance, sym_info["digits"])
                if new_sl > sl + point:
                    self._mt5.modify_position(ticket, sl=new_sl)
                    log.info("Trailing SL updated: ticket=%d new_sl=%.5f peak=%.5f",
                             ticket, new_sl, peak)
            else:
                new_sl = round(peak + trail_distance, sym_info["digits"])
                if new_sl < sl - point:
                    self._mt5.modify_position(ticket, sl=new_sl)
                    log.info("Trailing SL updated: ticket=%d new_sl=%.5f peak=%.5f",
                             ticket, new_sl, peak)

    def remove(self, ticket):
        self._peaks.pop(ticket, None)
'@ | Out-File -FilePath "C:\ForexBot\risk\trailing_stop.py" -Encoding UTF8
Write-Host "[3/8] trailing_stop.py written!" -ForegroundColor Green

# ── BACKTEST MODULE ───────────────────────────────────────────────────────────
@'
"""
Backtesting Engine
Runs strategy logic on historical bars before live trading
Reports win rate, RR, and signal quality
"""
import pandas as pd
import numpy as np
from datetime import datetime
from core.logger import get_logger
from config.settings import BACKTEST_LOOKBACK_BARS

log = get_logger("core.backtest")

class BacktestEngine:

    def __init__(self, mt5_connector, scanner):
        self._mt5     = mt5_connector
        self._scanner = scanner

    def run(self, symbols, timeframe="H1", notifier=None):
        log.info("Starting backtest on %d symbols TF=%s bars=%d",
                 len(symbols), timeframe, BACKTEST_LOOKBACK_BARS)
        results = []
        for symbol in symbols:
            try:
                result = self._backtest_symbol(symbol, timeframe)
                if result:
                    results.append(result)
            except Exception as e:
                log.error("[%s] Backtest error: %s", symbol, e)

        if not results:
            log.info("No backtest results.")
            return {}

        total   = sum(r["total"] for r in results)
        wins    = sum(r["wins"]  for r in results)
        losses  = sum(r["losses"] for r in results)
        avg_rr  = np.mean([r["avg_rr"] for r in results if r["avg_rr"] > 0])
        win_rate = wins / total * 100 if total > 0 else 0

        summary = {
            "symbols_tested": len(results),
            "total_signals":  total,
            "wins":           wins,
            "losses":         losses,
            "win_rate":       round(win_rate, 1),
            "avg_rr":         round(float(avg_rr), 2),
            "best_symbol":    max(results, key=lambda x: x["win_rate"])["symbol"] if results else "N/A",
        }

        log.info("Backtest complete: %s", summary)

        if notifier:
            msg = (
                f"📊 *BACKTEST RESULTS*\n\n"
                f"Symbols: `{summary['symbols_tested']}`\n"
                f"Signals: `{summary['total_signals']}`\n"
                f"Win Rate: `{summary['win_rate']}%`\n"
                f"Avg RR: `{summary['avg_rr']}R`\n"
                f"Best: `{summary['best_symbol']}`"
            )
            notifier._send(msg)

        return summary

    def _backtest_symbol(self, symbol, timeframe):
        df = self._mt5.get_candles(symbol, timeframe, BACKTEST_LOOKBACK_BARS)
        if df is None or len(df) < 50:
            return None

        sym_info = self._mt5.get_symbol_info(symbol)
        if not sym_info:
            return None

        point = sym_info["point"]
        signals_found = 0
        wins = 0
        losses = 0
        rr_list = []

        # Slide window through historical bars
        window = 100
        for i in range(window, len(df) - 20):
            slice_df = df.iloc[i-window:i].copy()

            # Quick structure check
            close = slice_df["close"].values
            highs = slice_df["high"].values
            lows  = slice_df["low"].values

            # Detect simple swing setup
            recent_high = highs[-20:].max()
            recent_low  = lows[-20:].min()
            current     = close[-1]
            atr         = (slice_df["high"] - slice_df["low"]).tail(14).mean()

            if atr == 0:
                continue

            # Check for bullish setup (price near recent low with bounce)
            near_low   = current < recent_low + atr * 2
            bouncing   = close[-1] > close[-3]   # simple momentum check
            swept_low  = lows[-5:].min() < recent_low and close[-1] > recent_low

            # Check for bearish setup
            near_high  = current > recent_high - atr * 2
            dropping   = close[-1] < close[-3]
            swept_high = highs[-5:].max() > recent_high and close[-1] < recent_high

            direction = None
            if near_low and bouncing and swept_low:
                direction = "BUY"
            elif near_high and dropping and swept_high:
                direction = "SELL"

            if direction is None:
                continue

            signals_found += 1

            # Simulate trade outcome
            entry = current
            sl    = recent_low - atr * 0.5 if direction == "BUY" else recent_high + atr * 0.5
            risk  = abs(entry - sl)
            if risk == 0:
                continue

            tp1   = entry + risk * 1.5 if direction == "BUY" else entry - risk * 1.5
            tp2   = entry + risk * 3.0 if direction == "BUY" else entry - risk * 3.0

            # Check future bars for outcome
            future = df.iloc[i:i+20]
            outcome = None
            for _, bar in future.iterrows():
                if direction == "BUY":
                    if bar["low"] <= sl:
                        outcome = "SL"
                        break
                    if bar["high"] >= tp1:
                        outcome = "TP1"
                        break
                else:
                    if bar["high"] >= sl:
                        outcome = "SL"
                        break
                    if bar["low"] <= tp1:
                        outcome = "TP1"
                        break

            if outcome == "TP1":
                wins += 1
                rr_list.append(1.5)
            elif outcome == "SL":
                losses += 1
                rr_list.append(-1.0)

        total    = wins + losses
        win_rate = wins / total * 100 if total > 0 else 0
        avg_rr   = np.mean(rr_list) if rr_list else 0

        log.info("[%s] BT: signals=%d wins=%d losses=%d wr=%.1f%% rr=%.2f",
                 symbol, signals_found, wins, losses, win_rate, avg_rr)

        return {
            "symbol":   symbol,
            "total":    total,
            "wins":     wins,
            "losses":   losses,
            "win_rate": win_rate,
            "avg_rr":   avg_rr,
        }
'@ | Out-File -FilePath "C:\ForexBot\core\backtest.py" -Encoding UTF8
Write-Host "[4/8] backtest.py written!" -ForegroundColor Green

# ── UPDATED TRADE MANAGER WITH TRAILING STOP ─────────────────────────────────
@'
from typing import Optional, Dict, List
from datetime import datetime
from core.logger import get_logger
from config.settings import AI_RETRAIN_AFTER_TRADES
from risk.trailing_stop import TrailingStopManager

log = get_logger("core.trade_manager")

class TradeManager:
    def __init__(self, mt5, risk, database, notifier, ai):
        self._mt5=mt5; self._risk=risk; self._db=database; self._tg=notifier; self._ai=ai
        self._active={}; self._tp1_done=set(); self._retrain_counter=0
        self._trailing = TrailingStopManager(mt5)
        self._restore()

    def execute_signal(self, signal):
        sym_info = self._mt5.get_symbol_info(signal.symbol)
        if sym_info is None: return False
        balance = self._mt5.get_balance()
        equity  = self._mt5.get_equity()
        open_pos = self._mt5.get_open_positions()
        if not self._risk.can_open_new_trade(open_pos, signal.symbol, balance, equity): return False
        self._risk.update_balance_tracking(balance)
        sl_pips = self._risk.sl_pips(signal.entry_price, signal.stop_loss, sym_info["point"])
        volume  = self._risk.calculate_lot_size(balance, sl_pips, sym_info)
        if volume <= 0: return False
        result = self._mt5.place_order(signal.symbol, signal.direction, volume,
                                       signal.stop_loss, signal.take_profit_2, "FXBot-CRT")
        if result is None:
            self._tg.error(f"Order failed: {signal.symbol} {signal.direction}")
            return False
        ticket = result["ticket"]
        signal_id = self._db.save_signal(signal.to_dict())
        trade = {
            "ticket": ticket, "signal_id": signal_id,
            "symbol": signal.symbol, "direction": signal.direction,
            "volume": volume, "entry_price": result["price"],
            "stop_loss": signal.stop_loss,
            "take_profit_1": signal.take_profit_1,
            "take_profit_2": signal.take_profit_2,
            "open_time": datetime.utcnow(),
            "ai_score": signal.ai_score,
            "features": signal.metadata.get("features", {}),
        }
        self._db.save_trade(trade)
        self._active[ticket] = trade
        sig_dict = signal.to_dict()
        sig_dict["entry_price"] = result["price"]
        self._tg.new_trade(sig_dict)
        log.info("Trade executed: %s %s ticket=%d lots=%.2f ai=%.1f",
                 signal.direction, signal.symbol, ticket, volume, signal.ai_score)
        return True

    def monitor_positions(self):
        open_pos = self._mt5.get_open_positions()
        live_tickets = {p["ticket"] for p in open_pos}
        for ticket in list(self._active.keys()):
            if ticket not in live_tickets:
                self._handle_closed(ticket)
        for pos in open_pos:
            if pos["ticket"] in self._active:
                self._check_tp1(pos)
        # Update trailing stops
        self._trailing.update(open_pos)

    def _check_tp1(self, pos):
        ticket = pos["ticket"]
        if ticket in self._tp1_done: return
        trade = self._active.get(ticket, {})
        tp1 = trade.get("take_profit_1", 0)
        if not tp1: return
        direction = pos["type"]
        current = pos["current_price"]
        hit = (direction=="BUY" and current>=tp1) or (direction=="SELL" and current<=tp1)
        if not hit: return
        sym_info = self._mt5.get_symbol_info(pos["symbol"])
        if sym_info is None: return
        vol_step = sym_info.get("volume_step", 0.01)
        close_vol = self._risk.tp1_close_volume(pos["volume"], vol_step)
        if self._mt5.close_position(ticket, volume=close_vol):
            self._tp1_done.add(ticket)
            be_sl = self._risk.break_even_sl(trade["entry_price"], direction, 2, sym_info["point"])
            self._mt5.modify_position(ticket, sl=be_sl)
            self._tg.tp_hit(ticket, pos["symbol"], 1, pos["profit"])
            log.info("TP1 hit + BE SL set: ticket=%d", ticket)

    def _handle_closed(self, ticket):
        trade = self._active.pop(ticket, {})
        if not trade: return
        self._trailing.remove(ticket)
        history = self._mt5.get_trade_history(days=1)
        deal = next((d for d in history if d["ticket"]==ticket), None)
        profit = deal["profit"] if deal else 0.0
        close_price = deal["price"] if deal else 0.0
        outcome = "TP1" if profit >= 0 else "SL"
        entry = trade.get("entry_price", close_price)
        direction = trade.get("direction", "BUY")
        pips = (close_price-entry)/(0.0001*10) if direction=="BUY" else (entry-close_price)/(0.0001*10)
        self._db.update_trade_close(ticket, close_price, profit, outcome, pips=pips)
        label = 1 if outcome in ("TP1","TP2") else 0
        self._db.save_training_sample(ticket, trade.get("features",{}), label)
        self._retrain_counter += 1
        if outcome == "SL": self._tg.sl_hit(ticket, trade.get("symbol",""), profit)
        else: self._tg.trade_closed(ticket, trade.get("symbol",""), profit, pips)
        log.info("Trade closed: ticket=%d outcome=%s profit=%.2f pips=%.1f",
                 ticket, outcome, profit, pips)
        if self._retrain_counter >= AI_RETRAIN_AFTER_TRADES:
            trades = self._db.get_labelled_trades()
            if len(trades) >= 20:
                ok = self._ai.retrain(trades)
                if ok:
                    acc = sum(1 for t in trades if t["outcome"]==1)/len(trades)*100
                    self._tg.ai_retrained(len(trades), acc)
            self._retrain_counter = 0

    def _restore(self):
        for t in self._db.get_open_trades():
            self._active[t["ticket"]] = t
'@ | Out-File -FilePath "C:\ForexBot\core\trade_manager.py" -Encoding UTF8
Write-Host "[5/8] trade_manager.py updated with trailing stop!" -ForegroundColor Green

# ── UPDATED SCANNER WITH GOLD SESSIONS + H4/H1 ENTRIES ───────────────────────
@'
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime
from core.logger import get_logger
from config.settings import (
    BIAS_TIMEFRAMES, ENTRY_TIMEFRAMES, AI_MIN_SCORE,
    SESSIONS, TRADE_ALLOWED_SESSIONS, CANDLES_REQUIRED,
    GOLD_SYMBOL, GOLD_PRIORITY_HOURS, GOLD_PRIORITY_WINDOW
)
from market_structure.analyzer import MarketStructureAnalyzer
from strategy.supply_demand import SupplyDemandEngine
from liquidity.engine import LiquidityEngine
from order_flow.engine import OrderFlowEngine
from strategy.crt_turtle_soup import CRTTurtleSoupStrategy

log = get_logger("core.scanner")

def _session():
    h = datetime.utcnow().hour
    for name, (s, e) in SESSIONS.items():
        if s <= h < e: return name
    return "other"

def _session_enc(s): return {"asian":0,"london":1,"newyork":2,"overlap":3}.get(s,0)

def _is_gold_priority_time():
    """Check if current time is near 5AM or 8AM UTC gold setup windows."""
    h = datetime.utcnow().hour
    for ph in GOLD_PRIORITY_HOURS:
        if abs(h - ph) <= GOLD_PRIORITY_WINDOW:
            return True
    return False

def _get_entry_timeframes(symbol):
    """
    Return entry timeframes based on symbol.
    Gold gets priority at special hours.
    H4/H1 included when they align.
    """
    if symbol == GOLD_SYMBOL and _is_gold_priority_time():
        log.info("[XAUUSD] GOLD PRIORITY TIME — expanding entry TFs")
        return ["H4", "H1", "M30", "M15", "M5"]
    return ENTRY_TIMEFRAMES

class Scanner:
    def __init__(self, mt5, ai):
        self._mt5=mt5; self._ai=ai
        self._ms=MarketStructureAnalyzer()
        self._sd=SupplyDemandEngine()
        self._liq=LiquidityEngine()
        self._of=OrderFlowEngine()
        self._strat=CRTTurtleSoupStrategy()

    def scan(self, symbol):
        session = _session()

        # Gold is allowed all sessions during priority hours
        if symbol == GOLD_SYMBOL and _is_gold_priority_time():
            pass   # always scan gold at priority times
        elif session not in TRADE_ALLOWED_SESSIONS:
            return None

        sym_info = self._mt5.get_symbol_info(symbol)
        if sym_info is None: return None
        point = sym_info["point"]

        # Higher TF bias
        bias_results = {}
        for tf in BIAS_TIMEFRAMES:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is not None and len(df) >= 20:
                bias_results[tf] = self._ms.analyze(df, symbol, tf)
        htf_bias, htf_strength = self._agg_bias(bias_results)
        if htf_bias == "neutral": return None

        # Zones from H4 + H1
        all_zones = []
        for tf in ["H4","H1"]:
            df = self._mt5.get_candles(symbol, tf, CANDLES_REQUIRED)
            if df is not None:
                all_zones.extend(self._sd.detect_zones(df, timeframe=tf, point=point))
        if not all_zones: return None

        # Entry timeframes — dynamic per symbol
        entry_tfs = _get_entry_timeframes(symbol)

        for entry_tf in entry_tfs:
            df = self._mt5.get_candles(symbol, entry_tf, CANDLES_REQUIRED)
            if df is None or len(df) < 30: continue
            tick = self._mt5.get_tick(symbol)
            if tick is None: continue
            current_price = tick["bid"]

            entry_ms = self._ms.analyze(df, symbol, entry_tf)
            liq      = self._liq.analyze(df, entry_tf)
            of_res   = self._of.analyze(df, entry_tf)

            # H4/H1 require stronger alignment
            if entry_tf in ("H4","H1"):
                if htf_strength < 0.6:
                    log.debug("[%s %s] HTF strength %.2f too low for H4/H1 entry",
                              symbol, entry_tf, htf_strength)
                    continue
                if entry_ms.bias != htf_bias:
                    log.debug("[%s %s] Entry TF bias mismatch — skip", symbol, entry_tf)
                    continue

            signal = self._strat.generate_signal(
                symbol=symbol,
                higher_tf_bias=htf_bias,
                higher_tf_strength=htf_strength,
                zones=all_zones,
                current_price=current_price,
                point=point,
                entry_structure=entry_ms,
                liquidity=liq,
                order_flow=of_res,
                entry_tf=entry_tf,
                entry_df=df,
            )
            if signal is None: continue

            # Build AI features
            atr = (df["high"]-df["low"]).tail(14).mean()
            is_gold_priority = (symbol == GOLD_SYMBOL and _is_gold_priority_time())
            features = {
                "htf_bias_score":    1.0 if htf_bias=="bullish" else -1.0,
                "htf_strength":      htf_strength,
                "structure_strength":entry_ms.strength,
                "entry_tf_bias":     1.0 if entry_ms.bias==htf_bias else 0.0,
                "zone_strength":     signal.zone.strength if signal.zone else 0.0,
                "zone_retests":      signal.zone.retests  if signal.zone else 3,
                "ssl_swept":         liq.ssl_swept,
                "bsl_swept":         liq.bsl_swept,
                "of_score":          of_res.flow_score,
                "sweep_score":       liq.sweep_score,
                "rr_ratio":          signal.rr_ratio,
                "session_encoded":   _session_enc(session),
                "volatility_norm":   min(atr/(current_price+1e-9)*100, 1.0),
                "confidence_raw":    signal.confidence,
                "zone_freshness":    signal.zone.fresh if signal.zone else False,
            }

            ai_score = self._ai.score_signal(features)
            signal.ai_score = ai_score
            signal.metadata["features"] = features
            signal.metadata["session"] = session
            signal.metadata["gold_priority"] = is_gold_priority

            # Gold priority slightly lowers AI threshold
            threshold = AI_MIN_SCORE - 3 if is_gold_priority else AI_MIN_SCORE

            if ai_score < threshold:
                log.info("[%s %s] Rejected AI=%.1f threshold=%.1f",
                         symbol, entry_tf, ai_score, threshold)
                continue

            log.info("[%s %s] SIGNAL APPROVED: %s ai=%.1f conf=%.1f gold_priority=%s",
                     symbol, entry_tf, signal.direction,
                     ai_score, signal.confidence, is_gold_priority)
            return signal

        return None

    @staticmethod
    def _agg_bias(bias_results):
        scores = {"bullish":0.0,"bearish":0.0}
        weights = {"W1":4,"D1":3,"H4":2,"H1":1}
        for tf, res in bias_results.items():
            w = weights.get(tf,1)
            if res.bias in scores:
                scores[res.bias] += w * res.strength
        if scores["bullish"] > scores["bearish"]*1.2:
            s = scores["bullish"]/(scores["bullish"]+scores["bearish"]+1e-9)
            return "bullish", s
        if scores["bearish"] > scores["bullish"]*1.2:
            s = scores["bearish"]/(scores["bullish"]+scores["bearish"]+1e-9)
            return "bearish", s
        return "neutral", 0.0
'@ | Out-File -FilePath "C:\ForexBot\core\scanner.py" -Encoding UTF8
Write-Host "[6/8] scanner.py updated with gold sessions + H4/H1 entries!" -ForegroundColor Green

# ── UPDATED MAIN.PY WITH BACKTEST ON STARTUP ──────────────────────────────────
@'
import os, sys, time, signal, traceback
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.logger import get_logger
from config import settings
from mt5.connector import MT5Connector
from core.scanner import Scanner
from core.trade_manager import TradeManager
from core.reporting import ReportingEngine
from core.backtest import BacktestEngine
from risk.manager import RiskManager
from storage.database import Database
from telegram.notifier import TelegramNotifier
from ai.signal_scorer import AISignalScorer

log = get_logger("main")
_RUNNING = True

def _stop(s,f):
    global _RUNNING
    log.info("Shutdown signal %s", s)
    _RUNNING = False

signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

class ForexBot:
    def __init__(self):
        log.info("="*60)
        log.info("  INSTITUTIONAL FOREX BOT V2 - STARTING")
        log.info("  Pairs: %d | Trailing Stop: ON | Backtest: ON", len(settings.SYMBOLS))
        log.info("="*60)
        self.db=Database()
        self.notifier=TelegramNotifier()
        self.mt5=MT5Connector()
        self.risk=RiskManager()
        self.ai=AISignalScorer()
        self.scanner=None; self.trader=None; self.reporter=None; self.backtester=None

    def start(self):
        if not self.mt5.connect():
            log.critical("Cannot connect to MT5. Exiting.")
            sys.exit(1)

        self.scanner    = Scanner(self.mt5, self.ai)
        self.trader     = TradeManager(self.mt5, self.risk, self.db, self.notifier, self.ai)
        self.reporter   = ReportingEngine(self.db, self.notifier)
        self.backtester = BacktestEngine(self.mt5, self.scanner)

        acct = self.mt5.get_account_info()
        if acct:
            balance = acct["balance"]
            is_micro = balance < settings.MICRO_ACCOUNT_THRESHOLD
            self.notifier.startup_v2(acct["balance"], acct["login"],
                                     len(settings.SYMBOLS), is_micro)

        # Run backtest on startup
        if settings.BACKTEST_ENABLED:
            log.info("Running startup backtest...")
            try:
                bt_results = self.backtester.run(
                    settings.SYMBOLS[:5],  # backtest first 5 symbols
                    timeframe="H1",
                    notifier=self.notifier
                )
                log.info("Backtest summary: %s", bt_results)
            except Exception as e:
                log.error("Backtest failed: %s", e)

        log.info("Bot scanning %d pairs every %ds",
                 len(settings.SYMBOLS), settings.MAIN_LOOP_INTERVAL_SEC)
        self._loop()

    def _loop(self):
        global _RUNNING
        errors = 0
        while _RUNNING:
            t0 = time.time()
            try:
                self._cycle()
                errors = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                errors += 1
                log.error("Loop error:\n%s", traceback.format_exc())
                self.notifier.error(f"Loop error #{errors}: {e}")
                if errors >= 5:
                    self.mt5.disconnect()
                    time.sleep(5)
                    self.mt5.reconnect()
                    errors = 0
            time.sleep(max(0, settings.MAIN_LOOP_INTERVAL_SEC - (time.time()-t0)))
        self.mt5.disconnect()
        log.info("Bot stopped.")

    def _cycle(self):
        if not self.mt5.is_connected():
            self.mt5.reconnect()
            return
        acct = self.mt5.get_account_info()
        if not acct: return

        balance = acct["balance"]
        equity  = acct["equity"]
        self.risk.update_balance_tracking(balance)

        if self.risk.is_drawdown_exceeded(equity):
            self.notifier.warning(f"Daily drawdown limit hit. Equity: ${equity:.2f}")
            self.trader.monitor_positions()
            return

        self.trader.monitor_positions()

        open_pos  = self.mt5.get_open_positions()
        open_syms = {p["symbol"] for p in open_pos}

        for symbol in settings.SYMBOLS:
            if symbol in open_syms: continue
            try:
                signal = self.scanner.scan(symbol)
                if signal:
                    self.trader.execute_signal(signal)
            except Exception as e:
                log.error("[%s] Scan error: %s", symbol, e)

        self.reporter.check_and_send_reports(balance)

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except: pass
    ForexBot().start()
'@ | Out-File -FilePath "C:\ForexBot\main.py" -Encoding UTF8
Write-Host "[7/8] main.py updated with backtest on startup!" -ForegroundColor Green

# ── UPDATE TELEGRAM NOTIFIER WITH V2 STARTUP ──────────────────────────────────
@'
import threading, time, requests
from datetime import datetime
from core.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = get_logger("telegram.notifier")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

class TelegramNotifier:
    def __init__(self):
        self._enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN")

    def startup_v2(self, balance, account, pairs, is_micro):
        micro_tag = " | 🔬 MICRO MODE" if is_micro else ""
        self._send(
            f"🚀 *FOREX BOT V2 STARTED*{micro_tag}\n\n"
            f"Account: `{account}`\n"
            f"Balance: `${balance:,.2f}`\n"
            f"Pairs Scanning: `{pairs}`\n"
            f"Trailing Stop: `✅ ON`\n"
            f"Gold Priority: `✅ 5AM & 8AM UTC`\n"
            f"Backtest: `✅ Running on startup`\n"
            f"Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            f"Status: _All systems operational_ 🛡️"
        )

    def startup(self, balance, account):
        self.startup_v2(balance, account, 24, balance < 500)

    def mt5_connected(self, server):
        self._send(f"ℹ️ *MT5 Connected*\nServer: `{server}`")

    def new_trade(self, s):
        icon = "📈" if s["direction"] == "BUY" else "📉"
        gold_tag = " 🥇" if s.get("symbol") == "XAUUSD" else ""
        self._send(
            f"{icon}📊 *NEW TRADE SIGNAL*{gold_tag}\n\n"
            f"Symbol:    `{s['symbol']}`\n"
            f"Direction: `{s['direction']}`\n"
            f"Entry:     `{s.get('entry_price',0):.5f}`\n"
            f"SL:        `{s.get('stop_loss',0):.5f}`\n"
            f"TP1:       `{s.get('take_profit_1',0):.5f}`\n"
            f"TP2:       `{s.get('take_profit_2',0):.5f}`\n"
            f"RR:        `{s.get('rr_ratio',0):.1f}R`\n"
            f"AI Score:  `{s.get('ai_score',0):.1f}/100`\n"
            f"Reason:    _{s.get('reason','')}_\n"
            f"TF:        `{s.get('timeframe','')}`\n"
            f"Time:      `{datetime.utcnow().strftime('%H:%M:%S')} UTC`"
        )

    def trade_closed(self, ticket, symbol, profit, pips):
        icon = "✅" if profit >= 0 else "❌"
        self._send(
            f"{icon} *TRADE CLOSED*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"P&L:    `${profit:+.2f}`\n"
            f"Pips:   `{pips:+.1f}`"
        )

    def tp_hit(self, ticket, symbol, tp_level, profit):
        self._send(
            f"💰🔥 *TP{tp_level} HIT — Partial Close*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"Profit: `${profit:+.2f}`\n"
            f"SL moved to Break-Even ✅"
        )

    def sl_hit(self, ticket, symbol, loss):
        self._send(
            f"💀 *SL HIT*\n\n"
            f"Ticket: `#{ticket}`\n"
            f"Symbol: `{symbol}`\n"
            f"Loss:   `${loss:+.2f}`"
        )

    def trailing_stop_update(self, ticket, symbol, new_sl):
        self._send(f"🔄 *TRAILING SL UPDATED*\nTicket: `#{ticket}`\nSymbol: `{symbol}`\nNew SL: `{new_sl:.5f}`")

    def daily_summary(self, s):
        self._send(
            f"📅 *DAILY SUMMARY*\n\n"
            f"Date:     `{s.get('date','')}`\n"
            f"Trades:   `{s.get('total_trades',0)}`\n"
            f"Wins:     `{s.get('wins',0)}` ✅\n"
            f"Losses:   `{s.get('losses',0)}` ❌\n"
            f"Win Rate: `{s.get('win_rate',0):.1f}%`\n"
            f"Net P&L:  `${s.get('net_pnl',0):+.2f}`\n"
            f"Balance:  `${s.get('balance',0):,.2f}`"
        )

    def weekly_summary(self, s):
        self._send(
            f"📅 *WEEKLY SUMMARY*\n\n"
            f"Week:     `{s.get('week','')}`\n"
            f"Trades:   `{s.get('total_trades',0)}`\n"
            f"Win Rate: `{s.get('win_rate',0):.1f}%`\n"
            f"Net P&L:  `${s.get('net_pnl',0):+.2f}`"
        )

    def ai_retrained(self, samples, accuracy):
        self._send(f"🤖 *AI RETRAINED*\nSamples: `{samples}`\nAccuracy: `{accuracy:.1f}%`")

    def error(self, message):
        self._send(f"⚠️ *ERROR*\n`{message}`")

    def warning(self, message):
        self._send(f"⚠️ *WARNING*\n_{message}_")

    def _send(self, text):
        if not self._enabled:
            log.debug("Telegram stub: %s", text[:60])
            return
        threading.Thread(target=self._post, args=(text,), daemon=True).start()

    def _post(self, text, retries=3):
        for attempt in range(retries):
            try:
                r = requests.post(
                    API_URL,
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
                    timeout=10
                )
                if r.status_code == 200: return
            except Exception as e:
                log.warning("Telegram attempt %d failed: %s", attempt+1, e)
            time.sleep(2 ** attempt)
'@ | Out-File -FilePath "C:\ForexBot\telegram\notifier.py" -Encoding UTF8
Write-Host "[8/8] notifier.py updated with V2 startup + gold tags!" -ForegroundColor Green

# ── START BOT ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Starting ForexBot V2..." -ForegroundColor Cyan
Start-Process -FilePath "C:\Program Files\Python311\python.exe" -ArgumentList "C:\ForexBot\main.py" -WorkingDirectory "C:\ForexBot" -WindowStyle Normal
Start-Sleep -Seconds 12
Get-Content "C:\ForexBot\logs\main.log" -Tail 20

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  FOREX BOT V2 FULLY UPGRADED AND RUNNING!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEW FEATURES:" -ForegroundColor Cyan
Write-Host "  24 pairs (+ BTCUSD + ETHUSD)" -ForegroundColor White
Write-Host "  Trailing Stop (activates at 1R profit)" -ForegroundColor White
Write-Host "  Gold priority at 5AM and 8AM UTC" -ForegroundColor White
Write-Host "  H4 + H1 entry timeframes when aligned" -ForegroundColor White
Write-Host "  Backtest runs on startup" -ForegroundColor White
Write-Host "  Micro account support ($10+)" -ForegroundColor White
Write-Host "  Faster scanning every 45 seconds" -ForegroundColor White
Write-Host "  Better Telegram signals with more detail" -ForegroundColor White
