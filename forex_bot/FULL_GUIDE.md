# INSTITUTIONAL FOREX TRADING BOT — COMPLETE GUIDE

---

## TABLE OF CONTENTS

1. [System Architecture](#1-system-architecture)
2. [Requirements](#2-requirements)
3. [Installation Guide (Windows VPS)](#3-installation-guide-windows-vps)
4. [MetaTrader 5 Setup](#4-metatrader-5-setup)
5. [Telegram Bot Setup](#5-telegram-bot-setup)
6. [Configuration](#6-configuration)
7. [Strategy Explanation](#7-strategy-explanation)
8. [AI Engine](#8-ai-engine)
9. [Risk Management](#9-risk-management)
10. [Running the Bot](#10-running-the-bot)
11. [Monitoring & Logs](#11-monitoring--logs)
12. [Troubleshooting](#12-troubleshooting)
13. [Adding New Symbols](#13-adding-new-symbols)
14. [FAQ](#14-faq)

---

## 1. SYSTEM ARCHITECTURE

```
forex_bot/
├── main.py                        ← Entry point (run this)
├── requirements.txt
├── .env.example                   ← Copy to .env and fill credentials
│
├── config/
│   └── settings.py                ← All configuration constants
│
├── core/
│   ├── logger.py                  ← Rotating log system
│   ├── scanner.py                 ← Multi-timeframe analysis orchestrator
│   ├── trade_manager.py           ← Trade execution & lifecycle management
│   └── reporting.py               ← Daily/weekly report generation
│
├── market_structure/
│   └── analyzer.py                ← HH/HL/LH/LL, BOS, CHOCH detection
│
├── strategy/
│   ├── supply_demand.py           ← Institutional zone detection
│   └── crt_turtle_soup.py        ← CRT + Turtle Soup signal logic
│
├── liquidity/
│   └── engine.py                  ← EQH/EQL, BSL/SSL, sweep detection
│
├── order_flow/
│   └── engine.py                  ← Volume delta, CVD, pressure analysis
│
├── ai/
│   └── signal_scorer.py           ← XGBoost AI scoring + retraining
│
├── risk/
│   └── manager.py                 ← Lot sizing, drawdown, exposure control
│
├── mt5/
│   └── connector.py               ← MetaTrader 5 integration layer
│
├── telegram/
│   └── notifier.py                ← Telegram Bot API notifications
│
├── storage/
│   └── database.py                ← SQLite persistence layer
│
├── logs/                          ← Auto-created log files
└── deploy/
    ├── install_vps.ps1            ← Automated Windows installer
    └── update_bot.ps1             ← Update + restart script
```

---

## 2. REQUIREMENTS

### Software
| Component | Version | Notes |
|-----------|---------|-------|
| Windows   | 10/11/Server 2019+ | VPS target OS |
| Python    | 3.11+ | Auto-installed by installer |
| MetaTrader 5 | Latest | Must be installed, logged in |
| MT5 Python pkg | 5.0.45+ | Installed via pip |

### Python Packages
```
MetaTrader5>=5.0.45
pandas>=2.0.0
numpy>=1.24.0
xgboost>=2.0.0
scikit-learn>=1.3.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### VPS Minimum Specs
| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 50 GB SSD | 100 GB SSD |
| OS | Windows Server 2019 | Windows Server 2022 |
| Internet | 100 Mbps | 1 Gbps |
| Uptime | 99.9% | 99.99% |

---

## 3. INSTALLATION GUIDE (WINDOWS VPS)

### Step 1 — Access Your VPS
Connect via Remote Desktop (RDP):
- Open **Remote Desktop Connection** on your local PC
- Enter your VPS IP address, username, and password

### Step 2 — Download the Bot
On the VPS, open PowerShell as Administrator and run:
```powershell
# Option A: Copy files via RDP clipboard/transfer
# Option B: Download from your storage (GitHub, Google Drive, etc.)

# Example with git:
git clone https://your-repo-url/forex_bot C:\ForexBot
```

Or simply copy the `forex_bot` folder to `C:\ForexBot` via RDP file transfer.

### Step 3 — Run the Auto-Installer
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
cd C:\ForexBot
.\deploy\install_vps.ps1
```

This script will:
- ✅ Install Python 3.11 (if not present)
- ✅ Create a virtual environment
- ✅ Install all Python packages
- ✅ Create `.env` from template
- ✅ Register Task Scheduler job (auto-start on boot)
- ✅ Create START/STOP/RESTART convenience scripts

### Step 4 — Configure Credentials
Edit `C:\ForexBot\.env`:
```env
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=ICMarkets-Demo01
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Step 5 — Start the Bot
```
Double-click: C:\ForexBot\START_BOT.bat
```
Or reboot the VPS — the bot starts automatically.

---

## 4. METATRADER 5 SETUP

### Install MT5
1. Download from: https://www.metatrader5.com/en/download
2. Install at: `C:\Program Files\MetaTrader 5\`
3. Open MT5 and log into your broker demo account

### Critical MT5 Settings

#### Allow Automated Trading
- MT5 Menu → **Tools** → **Options** → **Expert Advisors** tab
- ✅ Check "Allow automated trading"
- ✅ Check "Allow DLL imports"
- Click **OK**

#### Enable Python API
MT5 Python API communicates via localhost — no special firewall needed.
Just ensure MT5 terminal is running before the bot starts.

### Symbols Setup
All symbols (EURUSD, GBPJPY, XAUUSD, etc.) must be visible in MT5:
- In MT5: **View** → **Symbols** → find and drag your symbols to the **Market Watch** panel

### MT5 Server Name
Find your exact server name:
- MT5 → **File** → **Open an Account** → your broker's server names are listed
- Example: `ICMarkets-Demo01`, `Pepperstone-Demo`, `FTMO-Demo3`

---

## 5. TELEGRAM BOT SETUP

### Create Your Bot
1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Follow prompts → you get a **Bot Token** like:
   `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`

### Get Your Chat ID
1. Start a conversation with your new bot
2. Open in browser: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Send any message to your bot
4. Refresh the URL — look for `"chat":{"id":XXXXXXXXX}` — that's your Chat ID

### For a Channel
1. Add the bot as an **administrator** of your channel
2. The Chat ID for channels starts with `-100...`

### Test Your Bot
```python
# Quick test — run from Windows CMD:
python -c "
import requests
r = requests.post('https://api.telegram.org/bot<TOKEN>/sendMessage',
    json={'chat_id': '<CHAT_ID>', 'text': 'Bot test OK!'})
print(r.json())
"
```

---

## 6. CONFIGURATION

All settings in `config/settings.py`. Key parameters:

### Trading Symbols
```python
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY",
    "GBPJPY", "XAUUSD",
]
```

### Risk Parameters (Moderate Profile — Default)
```python
RISK_PER_TRADE_PCT     = 1.0    # 1% of balance per trade
MAX_DAILY_DRAWDOWN_PCT = 4.0    # Stop trading at 4% daily loss
MAX_OPEN_POSITIONS     = 3      # Maximum 3 simultaneous trades
MIN_RR_RATIO           = 1.5    # Minimum 1.5R trades only
TP1_CLOSE_PCT          = 50     # Close 50% at TP1
```

### AI Settings
```python
AI_MIN_SCORE           = 55     # Signal must score ≥55/100 to trade
AI_RETRAIN_AFTER_TRADES = 50   # Retrain AI every 50 labelled outcomes
```

### Session Control (UTC)
```python
TRADE_ALLOWED_SESSIONS = ["london", "newyork", "overlap"]
# Bot only trades during London (07:00-16:00 UTC), 
# New York (12:00-21:00 UTC), and Overlap (12:00-16:00 UTC)
```

### Main Loop Speed
```python
MAIN_LOOP_INTERVAL_SEC = 60  # Scan all symbols every 60 seconds
```

---

## 7. STRATEGY EXPLANATION

### Top-Down Analysis Framework

```
W1  (Weekly)    → Long-term directional bias
  ↓
D1  (Daily)     → Market structure + major liquidity zones
  ↓
H4  (4-Hour)    → Institutional supply/demand zones + trend confirmation
  ↓
H1  (1-Hour)    → Additional bias confirmation
  ↓
M30/M15/M5      → Entry execution timeframes
```

**Rule: Lower timeframes NEVER override higher timeframe bias.**

---

### CRT + Turtle Soup — LONG SETUP

```
✅ 1. W1/D1/H4/H1 → Bullish bias (weighted vote)
✅ 2. Price at or approaching fresh Demand Zone (H4/H1)
✅ 3. SSL swept → Price briefly breaks below recent lows (Stop Hunt)
✅ 4. Price closes BACK ABOVE the swept low (Turtle Soup reversal)
✅ 5. M30/M15/M5 market structure shifts bullish (CHOCH or BOS up)
✅ 6. Order Flow score > 55 (accumulation confirmed)
✅ 7. AI score ≥ 55/100
→ EXECUTE BUY
```

**SL:** Below demand zone bottom (+ 5 pip buffer)
**TP1:** Entry + 1.5R (close 50%, move SL to break-even)
**TP2:** Entry + 3R (full close remainder)

---

### CRT + Turtle Soup — SHORT SETUP

```
✅ 1. W1/D1/H4/H1 → Bearish bias
✅ 2. Price at or approaching fresh Supply Zone (H4/H1)
✅ 3. BSL swept → Price briefly breaks above recent highs (Stop Hunt)
✅ 4. Price closes BACK BELOW the swept high (Turtle Soup reversal)
✅ 5. M30/M15/M5 market structure shifts bearish (CHOCH or BOS down)
✅ 6. Order Flow score < 45 (distribution confirmed)
✅ 7. AI score ≥ 55/100
→ EXECUTE SELL
```

---

### Market Structure (BOS vs CHOCH)

| Event | Definition | Significance |
|-------|-----------|--------------|
| BOS Up | Close above previous swing high (in uptrend) | Continuation bullish |
| BOS Down | Close below previous swing low (in downtrend) | Continuation bearish |
| CHOCH Up | Close above swing high (WAS in downtrend) | ⚡ Reversal signal — strongest |
| CHOCH Down | Close below swing low (WAS in uptrend) | ⚡ Reversal signal — strongest |

---

### Supply & Demand Zones

**Demand Zone (Drop-Base-Rally):**
- Strong bearish impulse → small consolidation → strong bullish impulse
- Price likely to bounce here on retest

**Supply Zone (Rally-Base-Drop):**
- Strong bullish impulse → small consolidation → strong bearish impulse
- Price likely to reverse here on retest

Zone strength scoring (0-10):
- 7-10: Strong institutional zone ← primary targets
- 4-6: Moderate zone
- <4: Weak zone ← filtered out

---

### Liquidity Engine

| Level | Definition | Trading Implication |
|-------|-----------|---------------------|
| BSL (Buy-Side Liquidity) | Stops above swing highs | Price may sweep before selling |
| SSL (Sell-Side Liquidity) | Stops below swing lows | Price may sweep before buying |
| EQH (Equal Highs) | Multiple equal highs | Strong BSL pool |
| EQL (Equal Lows) | Multiple equal lows | Strong SSL pool |

**Sweep Detection:** Bot identifies when price breaks above/below these levels and then reverses — classic institutional stop-hunt pattern.

---

### Order Flow Engine

Uses **Close Location Value** method to split tick-volume:
- `Bullish Volume = Volume × (Close - Low) / (High - Low)`
- `Bearish Volume = Volume × (High - Close) / (High - Low)`

Metrics:
- **CVD (Cumulative Volume Delta):** Rising = buyers winning, Falling = sellers winning
- **Absorption:** High volume + small price move = institutional absorption
- **Flow Score:** 0-100 (>50 = bullish bias, <50 = bearish bias)

---

## 8. AI ENGINE

### XGBoost Signal Scorer

The AI learns which signal configurations lead to winning trades.

**Feature Vector (15 features):**
1. HTF bias score (-1/0/+1)
2. HTF strength (0-1)
3. Market structure strength (0-1)
4. Entry TF bias alignment (0/1)
5. Zone strength normalised (0-1)
6. Zone retest count
7. SSL swept (bool)
8. BSL swept (bool)
9. Order flow score normalised (0-1)
10. Sweep score (0-1)
11. Risk-to-reward ratio
12. Session encoded (0=Asian, 1=London, 2=NY, 3=Overlap)
13. Normalised volatility (ATR/price)
14. Rule engine confidence (0-1)
15. Zone freshness (bool)

**Bootstrap Training:**
- On first run, the bot generates 500 synthetic training samples
- Winning trades have higher feature values; losers have lower
- The XGBoost model trains on this immediately → starts scoring signals from day 1

**Continuous Learning:**
- Every closed trade (TP or SL) is labelled and stored
- After every 50 labelled trades, the model retrains
- Over time, the AI improves based on real market outcomes

**Scoring Threshold:**
- `AI_MIN_SCORE = 55` → Only signals scoring 55/100 or above are traded
- Adjust this in `config/settings.py` to be more/less selective

---

## 9. RISK MANAGEMENT

### Lot Size Calculation

```
Risk Amount = Balance × 1%
Pip Value per Lot = Pip Size × Contract Size
Lots = Risk Amount / (SL Pips × Pip Value per Lot)
```

**Example:**
- Balance: $10,000
- Risk: 1% = $100
- SL: 20 pips
- EURUSD: pip_value = $10/lot
- Lots = $100 / (20 × $10) = 0.5 lots

### Protection Layers

| Protection | Value | Action |
|-----------|-------|--------|
| Daily Drawdown | 4% | Stop ALL new trades for the day |
| Max Positions | 3 | Block new trades until one closes |
| Min RR Ratio | 1.5R | Reject signals with bad RR |
| No Duplicate Symbol | — | One trade per symbol max |
| Max Exposure | 6% | Block if total risk ≥ 6% |

### Trade Management Flow

```
Entry → Position Opens
  ↓
TP1 Hit? → Close 50% → Move SL to Break-Even
  ↓
TP2 Hit? → Close remaining 50% → Log WIN
  OR
SL Hit? → Log LOSS → Feed to AI retraining
```

---

## 10. RUNNING THE BOT

### Manual Start
```
Double-click: C:\ForexBot\START_BOT.bat
```

### Via PowerShell
```powershell
cd C:\ForexBot
.\venv\Scripts\python.exe main.py
```

### As Windows Service (Auto on Boot)
The installer registers this automatically.
To manually start/stop:
```batch
schtasks /run /tn "ForexBot"      ← Start
schtasks /end /tn "ForexBot"      ← Stop
```

### Verify It's Running
```powershell
Get-ScheduledTask -TaskName "ForexBot" | Select-Object State
# Should show: State = Running
```

---

## 11. MONITORING & LOGS

### Log Files (C:\ForexBot\logs\)

| File | Contents |
|------|---------|
| `main.log` | All bot events |
| `trades.log` | Trade execution events |
| `ai.log` | AI scoring and retraining |
| `errors.log` | Warnings and errors only |

### Telegram Notifications

You'll receive messages for:
- 🚀 Bot startup
- ℹ️ MT5 connection
- 📊 Every new trade (entry, SL, TP1, TP2, RR, AI score)
- ✅ TP1 hit + partial close
- ✅ TP2 hit (trade closed)
- ❌ SL hit
- 📅 Daily summary (trades, win rate, P&L)
- 📅 Weekly summary
- 🤖 AI model retrained
- ⚠️ Warnings and errors

### Database (C:\ForexBot\storage\trading_bot.db)
Open with: [DB Browser for SQLite](https://sqlitebrowser.org/)

Tables:
- `signals` — all generated signals (taken and rejected)
- `trades` — executed trades + outcomes
- `ai_training_data` — labelled features for AI
- `daily_stats` — daily performance
- `weekly_stats` — weekly performance

---

## 12. TROUBLESHOOTING

### MT5 Connection Failed
```
Error: mt5.initialize() failed
```
**Fix:**
1. Ensure MT5 terminal is open and logged in
2. Check `MT5_PATH` in `.env` matches your installation path
3. Ensure MT5 allows API connections: Tools → Options → Expert Advisors → ✅ Allow automated trading
4. Run Python as Administrator if needed

### XGBoost Not Installing
```
pip install xgboost
```
If fails on Windows: install Microsoft Visual C++ Redistributable from Microsoft's site.

### Telegram Messages Not Arriving
1. Verify `TELEGRAM_BOT_TOKEN` (no spaces, exact copy from BotFather)
2. Verify `TELEGRAM_CHAT_ID` (include `-100` prefix for channels)
3. Test: open `https://api.telegram.org/bot<TOKEN>/getMe` in browser
4. Ensure you've started a conversation with your bot first

### Bot Not Auto-Starting After Reboot
```powershell
# Check task is registered
Get-ScheduledTask -TaskName "ForexBot"

# Re-register if needed
cd C:\ForexBot
.\deploy\install_vps.ps1
```

### No Signals Being Generated
Common causes:
1. **Outside trading sessions** — Bot only trades London/NY/Overlap (UTC)
2. **AI score too high** — Lower `AI_MIN_SCORE` to 50 in `settings.py`
3. **HTF bias neutral** — Markets may be ranging — this is correct behaviour
4. **No valid zones** — Increase `ZONE_LOOKBACK` in `settings.py`

### High CPU Usage
- Reduce `SYMBOLS` list in `settings.py`
- Increase `MAIN_LOOP_INTERVAL_SEC` from 60 to 120

---

## 13. ADDING NEW SYMBOLS

In `config/settings.py`:
```python
SYMBOLS = [
    "EURUSD", "GBPUSD", ...,
    "BTCUSD",    # Add new symbols here
    "US30",
    "USOIL",
]
```

Requirements for new symbols:
1. Symbol must be available in your broker's MT5
2. Symbol must be added to MT5 Market Watch
3. Verify exact symbol name (some brokers use `USOILx` or `XBRUSDx`)

---

## 14. FAQ

**Q: Is this safe for a live account?**
A: Start on DEMO first. Run for at least 4-6 weeks, review all signals and performance. Only switch to live after you're satisfied with the demo results.

**Q: Does MT5 need to stay open?**
A: Yes. The Python MT5 library communicates with the MT5 terminal process. MT5 must be running on the same machine.

**Q: How does the AI improve over time?**
A: Every closed trade (TP or SL) is saved with its feature vector and outcome label. After every 50 new labelled trades, XGBoost retrains on the combined live + synthetic dataset.

**Q: Can I run multiple instances for different accounts?**
A: Yes — copy to different folders (e.g., `C:\ForexBot_Account2`), configure separate `.env` files with different MT5 credentials, and register different Task Scheduler task names.

**Q: What happens if the VPS reboots?**
A: The Task Scheduler job is set to `AtStartup` — the bot restarts automatically within 1-2 minutes of the VPS rebooting. MT5 must also be set to auto-start.

**Q: How do I update the bot?**
A: Replace the changed `.py` files and run `.\deploy\update_bot.ps1` — it stops the bot, updates dependencies, and restarts.

**Q: The bot generated 0 trades in a day — is something wrong?**
A: Not necessarily. The strategy is selective — it only enters when ALL conditions align (HTF bias + zone + liquidity sweep + structure + order flow + AI score). Zero-trade days are expected, especially during low-volatility sessions.

---

*Institutional Forex Trading Bot — Built for 24/7 production deployment on Windows VPS with MT5.*
