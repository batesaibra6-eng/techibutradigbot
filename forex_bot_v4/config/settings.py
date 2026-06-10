"""
==============================================================================
INSTITUTIONAL CRT + ROMEO ICT SYSTEM — CONFIGURATION
==============================================================================
"""
import os
from typing import List, Dict

# ── MT5 ───────────────────────────────────────────────────────────────────────
MT5_LOGIN    = int(os.getenv("MT5_LOGIN",    "436005794"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD",     "1234#Dt@")
MT5_SERVER   = os.getenv("MT5_SERVER",       "Exness-MT5Trial9")
MT5_PATH     = os.getenv("MT5_PATH",         r"C:\Program Files\MetaTrader 5\terminal64.exe")

# ── TELEGRAM ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8664218080:AAFIO77O-qyEds2C2gD55Lq2hSBNeKmm6B4")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "-1003781184008")

# ── SYMBOLS ───────────────────────────────────────────────────────────────────
SYMBOLS: List[str] = [
    "EURUSDm","GBPUSDm","USDJPYm","USDCHFm","USDCADm","AUDUSDm","NZDUSDm",
    "EURJPYm","GBPJPYm","EURGBPm","EURAUDm","EURCADm",
    "GBPAUDm","GBPCADm","GBPCHFm","AUDCADm","AUDJPYm",
    "CADJPYm","CHFJPYm","NZDJPYm","EURCHFm","AUDNZDm",
    "GBPNZDm","NZDCADm","NZDCHFm",
    "XAUUSDm","XAGUSDm","BTCUSDm","ETHUSDm","USDZARm",
]

# Always-on (crypto + metals scan 24/7)
ALWAYS_ON_SYMBOLS = ["BTCUSDm","ETHUSDm","XAUUSDm","XAGUSDm"]

# ── TIMEFRAMES ────────────────────────────────────────────────────────────────
HTF_BIAS_TIMEFRAMES  = ["W1","D1","H4","H1"]   # Bias engine
EXECUTION_TIMEFRAMES = ["M5","M15","M30"]       # Entry execution
STRUCTURE_TIMEFRAMES = ["H1","H4"]              # Structure reference

# ── KILLZONES (UTC) ───────────────────────────────────────────────────────────
# Standard UTC (winter, EST = UTC-5)
KILLZONES_UTC: Dict[str, tuple] = {
    "london_open":   (7,  10),    # 02:00-05:00 EST
    "ny_am":         (13, 16),    # 08:30-11:00 EST
    "silver_bullet": (15, 16),    # 10:00-11:00 EST ← HIGHEST PRIORITY
}
# DST (summer, EDT = UTC-4)
KILLZONES_DST: Dict[str, tuple] = {
    "london_open":   (6,  9),
    "ny_am":         (12, 15),
    "silver_bullet": (14, 15),
}

# ── CRT 3-CANDLE MODEL PARAMETERS ─────────────────────────────────────────────
CRT_SWEEP_THRESHOLD_PCT    = 0.10   # Candle 2 sweeps C1 H/L by ≥10% of C1 range
CRT_SWEEP_MAX_CLOSE_PCT    = 0.15   # C2 close can't be beyond C1 by >15%
CRT_CONFIRMATION_BODY_ATR  = 0.40   # C3 body ≥ 0.40 × ATR(14)
CRT_CONFIRMATION_CLOSE_PCT = 0.60   # C3 closes in top/bottom 60% of its range

# ── LIQUIDITY SWEEP PARAMETERS ────────────────────────────────────────────────
SWEEP_WICK_MIN_PCT    = 0.50   # Wick must be ≥ 50% of candle range
SWEEP_CLOSEBACK_BARS  = 3      # Close back inside within N bars
SWEEP_LOOKBACK_BARS   = 30     # Bars to look back for sweep detection
EQUAL_LEVEL_TOLERANCE = 0.0003 # 3 pip tolerance for equal highs/lows

# ── DISPLACEMENT PARAMETERS ───────────────────────────────────────────────────
DISPLACEMENT_ATR_MULT   = 1.5   # Range > 1.5 × ATR(14)
DISPLACEMENT_CLOSE_PCT  = 0.20  # Close in top/bottom 20% of candle
DISPLACEMENT_VOL_MULT   = 1.2   # Volume > 1.2 × rolling average
DISPLACEMENT_MIN_ATR    = 0.70  # MSS displacement ≥ 0.7 × ATR

# ── MARKET STRUCTURE ──────────────────────────────────────────────────────────
SWING_PIVOT_BARS   = 5         # N-bar pivot for swing detection
BOS_LOOKBACK       = 50        # Bars to look back for structure
EMA_BIAS_PERIOD    = 50        # EMA for HTF bias
SESSION_LOOKBACK   = 48        # Bars for session H/L detection

# ── SMT DIVERGENCE ────────────────────────────────────────────────────────────
SMT_ENABLED  = True
SMT_LOOKBACK = 20
SMT_PAIRS: Dict[str, str] = {
    "EURUSDm": "GBPUSDm",
    "GBPUSDm": "EURUSDm",
    "AUDUSDm": "NZDUSDm",
    "NZDUSDm": "AUDUSDm",
    "XAUUSDm": "DXYm",
}

# ── ENTRY EXECUTION ───────────────────────────────────────────────────────────
ENTRY_FVG_50PCT         = True    # Enter at 50% of FVG (equilibrium)
ENTRY_BRIST_RETEST      = True    # OR break-and-retest
FVG_MAX_LOOKBACK        = 15      # Bars to look for FVG after displacement
FVG_MIN_SIZE_PIPS       = 2.0     # Minimum FVG size

# ── RISK MANAGEMENT ──────────────────────────────────────────────────────────
RISK_PER_TRADE_PCT       = 1.0    # Base risk per trade
RISK_MIN_PCT             = 0.25   # Minimum risk (scaling down)
RISK_MAX_PCT             = 1.0    # Maximum risk per trade
DAILY_LOSS_CAP_PCT       = 3.0    # Hard daily loss cap
WEEKLY_LOSS_CAP_PCT      = 6.0    # Weekly loss cap
MAX_OPEN_POSITIONS       = 4      # Maximum concurrent trades
MAX_CORRELATED_EXPOSURE  = 2      # Max 2 positions in same direction
EQUITY_CURVE_LOOKBACK    = 20     # Trades to evaluate equity curve
VOLATILITY_ATR_KILL      = 4.0    # Kill if ATR > 4x normal
CONSECUTIVE_LOSS_KILL    = 5      # Stop after N consecutive losses
SPREAD_MAX_PIPS          = 3.0    # Max spread for standard pairs
SL_ATR_BUFFER            = 0.5    # ATR buffer beyond sweep extreme
MIN_RR_RATIO             = 2.0    # Minimum 2R (institutional standard)
PARTIAL_CLOSE_RR         = 1.0    # Partial close at 1R
PARTIAL_CLOSE_PCT        = 50     # Close 50% at partial target
TRAILING_STRUCTURE_BASED = True   # Trail SL on structure
MAGIC_NUMBER             = 99999

# ── EQUITY TIERS ──────────────────────────────────────────────────────────────
EQUITY_TIERS = [
    (10000, 1.00), (5000, 1.00), (2000, 1.00),
    (1000,  0.80), (500,  0.60), (200,  0.40),
    (100,   0.25), (50,   0.15), (20,   0.10),
    (5,     0.05), (0,    0.025),
]
MICRO_ACCOUNT_THRESHOLD = 500

# ── AI / ML ───────────────────────────────────────────────────────────────────
AI_MODE               = "xgboost"   # "xgboost" | "rules"
AI_MIN_SCORE          = 52
AI_ROLE               = "filter"    # AI filters only, never decides entry
AI_RETRAIN_INTERVAL   = 30          # retrain every N closed trades
AI_SYNTHETIC_SAMPLES  = 600

# ── BACKTEST ──────────────────────────────────────────────────────────────────
BACKTEST_ENABLED    = True
BACKTEST_BARS       = 1000
SLIPPAGE_PIPS       = 0.5    # Slippage model
COMMISSION_PER_LOT  = 3.5    # USD per lot round trip

# ── LOGGING ───────────────────────────────────────────────────────────────────
DB_PATH          = "storage/trading_bot.db"
LOG_DIR          = "logs"
LOG_LEVEL        = "INFO"
LOG_MAX_BYTES    = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# ── BOT BEHAVIOUR ─────────────────────────────────────────────────────────────
MAIN_LOOP_INTERVAL_SEC  = 45
RECONNECT_DELAY_SEC     = 30
MAX_RECONNECT_ATTEMPTS  = 15
CANDLES_REQUIRED        = 300
MIN_BALANCE_TO_TRADE    = 5.0

# ── FEATURE FLAGS ─────────────────────────────────────────────────────────────
NEWS_FILTER_ENABLED       = True
CORRELATION_CHECK_ENABLED = True
REGIME_ENGINE_ENABLED     = True
LEARNING_ENGINE_ENABLED   = True
SMT_DIVERGENCE_ENABLED    = True
SPREAD_FILTER_ENABLED     = True
VOLATILITY_KILL_ENABLED   = True
