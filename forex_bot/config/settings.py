"""
==============================================================================
INSTITUTIONAL FOREX TRADING BOT
Configuration Settings
==============================================================================
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict

# ---------------------------------------------------------------------------
# MT5 CREDENTIALS  (override via environment variables on production)
# ---------------------------------------------------------------------------
MT5_LOGIN    = int(os.getenv("MT5_LOGIN",    "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD",     "YOUR_PASSWORD")
MT5_SERVER   = os.getenv("MT5_SERVER",       "YOUR_BROKER_SERVER")
MT5_PATH     = os.getenv("MT5_PATH",         r"C:\Program Files\MetaTrader 5\terminal64.exe")

# ---------------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID")

# ---------------------------------------------------------------------------
# TRADING SYMBOLS
# ---------------------------------------------------------------------------
SYMBOLS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY",
    "GBPJPY", "XAUUSD",
]

# ---------------------------------------------------------------------------
# TIMEFRAMES  (MT5 constants mapped by name)
# ---------------------------------------------------------------------------
TIMEFRAMES: Dict[str, int] = {
    "W1":  16408,   # mt5.TIMEFRAME_W1
    "D1":  16385,   # mt5.TIMEFRAME_D1
    "H4":  16388,   # mt5.TIMEFRAME_H4
    "H1":  16385,   # mt5.TIMEFRAME_H1  -- corrected at runtime
    "M30": 30,
    "M15": 15,
    "M5":  5,
    "M1":  1,
}

# ---------------------------------------------------------------------------
# ANALYSIS TIMEFRAME HIERARCHY
# ---------------------------------------------------------------------------
BIAS_TIMEFRAMES   = ["W1", "D1", "H4", "H1"]          # Directional bias
ENTRY_TIMEFRAMES  = ["M30", "M15", "M5"]               # Entry execution

# ---------------------------------------------------------------------------
# RISK MANAGEMENT  (Moderate profile)
# ---------------------------------------------------------------------------
RISK_PER_TRADE_PCT     = 1.0      # % of account balance per trade
MAX_DAILY_DRAWDOWN_PCT = 4.0      # % max daily drawdown before shutdown
MAX_OPEN_POSITIONS     = 3        # simultaneous open trades
MAX_TOTAL_EXPOSURE_PCT = 6.0      # % of balance max open exposure
MIN_RR_RATIO           = 1.5      # minimum risk-to-reward ratio
DEFAULT_TP1_RR         = 1.5      # TP1 at 1.5R
DEFAULT_TP2_RR         = 3.0      # TP2 at 3R
TP1_CLOSE_PCT          = 50       # close 50 % at TP1
MAGIC_NUMBER           = 88888    # MT5 magic number

# ---------------------------------------------------------------------------
# MARKET STRUCTURE
# ---------------------------------------------------------------------------
STRUCTURE_LOOKBACK      = 50      # candles to look back for structure
SWING_SENSITIVITY       = 5       # bars each side for swing point detection
EQUAL_LEVEL_TOLERANCE   = 0.0003  # 3 pips tolerance for equal highs/lows

# ---------------------------------------------------------------------------
# SUPPLY / DEMAND ZONES
# ---------------------------------------------------------------------------
ZONE_LOOKBACK           = 100     # candles back to detect zones
ZONE_MIN_STRENGTH       = 3       # minimum zone strength score to consider
ZONE_MAX_RETESTS        = 3       # zone invalidated after N retests
ZONE_EXTENSION_PIPS     = 5       # extend zone by N pips for buffer

# ---------------------------------------------------------------------------
# LIQUIDITY
# ---------------------------------------------------------------------------
LIQUIDITY_LOOKBACK      = 30      # candles for liquidity level detection
SWEEP_CONFIRMATION_BARS = 2       # bars to confirm a sweep

# ---------------------------------------------------------------------------
# ORDER FLOW
# ---------------------------------------------------------------------------
OF_LOOKBACK             = 20      # candles for order-flow calculations

# ---------------------------------------------------------------------------
# AI ENGINE
# ---------------------------------------------------------------------------
AI_MODE                 = "xgboost"       # "xgboost" | "rules"
AI_MIN_SCORE            = 55              # minimum score to trade (0-100)
AI_RETRAIN_AFTER_TRADES = 50             # retrain every N new trades
AI_SYNTHETIC_SAMPLES    = 500            # bootstrap training samples

# ---------------------------------------------------------------------------
# SESSION WINDOWS  (UTC)
# ---------------------------------------------------------------------------
SESSIONS = {
    "london":   (7,  16),
    "newyork":  (12, 21),
    "asian":    (0,   9),
    "overlap":  (12, 16),
}
TRADE_ALLOWED_SESSIONS = ["london", "newyork", "overlap"]

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
DB_PATH                 = "storage/trading_bot.db"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
LOG_DIR                 = "logs"
LOG_LEVEL               = "INFO"
LOG_MAX_BYTES           = 10 * 1024 * 1024   # 10 MB per file
LOG_BACKUP_COUNT        = 5

# ---------------------------------------------------------------------------
# BOT BEHAVIOUR
# ---------------------------------------------------------------------------
MAIN_LOOP_INTERVAL_SEC  = 60      # seconds between analysis cycles
RECONNECT_DELAY_SEC     = 30      # seconds before MT5 reconnect attempt
MAX_RECONNECT_ATTEMPTS  = 10      # maximum consecutive reconnect attempts
CANDLES_REQUIRED        = 200     # minimum candles per timeframe
