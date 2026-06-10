# ==============================================================================
# INSTITUTIONAL CRT BOT V4 — COMPLETE SINGLE PASTE
# Copy EVERYTHING below and paste in PowerShell as Administrator
# ==============================================================================

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

New-Item -ItemType Directory -Force -Path C:\ForexBot\config        | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\core          | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\strategy      | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\risk          | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\ai            | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\mt5           | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\telegram      | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\storage       | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\logs          | Out-Null

Write-Host "Directories created." -ForegroundColor Green

# ── __init__.py files ─────────────────────────────────────────────────────────
"" | Out-File "C:\ForexBot\config\__init__.py"   -Encoding UTF8
"from .settings import *" | Out-File "C:\ForexBot\config\__init__.py" -Encoding UTF8
"" | Out-File "C:\ForexBot\core\__init__.py"     -Encoding UTF8
"" | Out-File "C:\ForexBot\strategy\__init__.py" -Encoding UTF8
"" | Out-File "C:\ForexBot\risk\__init__.py"     -Encoding UTF8
"" | Out-File "C:\ForexBot\ai\__init__.py"       -Encoding UTF8
"" | Out-File "C:\ForexBot\mt5\__init__.py"      -Encoding UTF8
"" | Out-File "C:\ForexBot\telegram\__init__.py" -Encoding UTF8
"" | Out-File "C:\ForexBot\storage\__init__.py"  -Encoding UTF8

# ==============================================================================
# FILE 1 — config/settings.py
# ==============================================================================
@'
import os
from typing import List, Dict

MT5_LOGIN    = int(os.getenv("MT5_LOGIN",    "436005794"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD",     "1234#Dt@")
MT5_SERVER   = os.getenv("MT5_SERVER",       "Exness-MT5Trial9")
MT5_PATH     = os.getenv("MT5_PATH",         r"C:\Program Files\MetaTrader 5\terminal64.exe")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8664218080:AAFIO77O-qyEds2C2gD55Lq2hSBNeKmm6B4")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "-1003781184008")

SYMBOLS: List[str] = [
    "EURUSDm","GBPUSDm","USDJPYm","USDCHFm","USDCADm","AUDUSDm","NZDUSDm",
    "EURJPYm","GBPJPYm","EURGBPm","EURAUDm","EURCADm",
    "GBPAUDm","GBPCADm","GBPCHFm","AUDCADm","AUDJPYm",
    "CADJPYm","CHFJPYm","NZDJPYm","EURCHFm","AUDNZDm",
    "GBPNZDm","NZDCADm","NZDCHFm",
    "XAUUSDm","XAGUSDm","BTCUSDm","ETHUSDm","USDZARm",
]
ALWAYS_ON_SYMBOLS = ["BTCUSDm","ETHUSDm","XAUUSDm","XAGUSDm"]

HTF_BIAS_TIMEFRAMES  = ["W1","D1","H4","H1"]
EXECUTION_TIMEFRAMES = ["M5","M15","M30"]
STRUCTURE_TIMEFRAMES = ["H1","H4"]

KILLZONES_UTC: Dict[str,tuple] = {
    "london_open":   (7,  10),
    "ny_am":         (13, 16),
    "silver_bullet": (15, 16),
}
KILLZONES_DST: Dict[str,tuple] = {
    "london_open":   (6,  9),
    "ny_am":         (12, 15),
    "silver_bullet": (14, 15),
}

CRT_SWEEP_THRESHOLD_PCT    = 0.10
CRT_SWEEP_MAX_CLOSE_PCT    = 0.15
CRT_CONFIRMATION_BODY_ATR  = 0.40
CRT_CONFIRMATION_CLOSE_PCT = 0.60
DISPLACEMENT_ATR_MULT      = 1.5
DISPLACEMENT_CLOSE_PCT     = 0.20
DISPLACEMENT_VOL_MULT      = 1.2
SWEEP_WICK_MIN_PCT         = 0.50
SWEEP_LOOKBACK_BARS        = 30
FVG_MAX_LOOKBACK           = 15
FVG_MIN_SIZE_PIPS          = 2.0
SWING_PIVOT_BARS           = 5
BOS_LOOKBACK               = 50
EMA_BIAS_PERIOD            = 50
SESSION_LOOKBACK           = 48
EQUAL_LEVEL_TOLERANCE      = 0.0003
SL_ATR_BUFFER              = 0.5

SMT_ENABLED  = True
SMT_LOOKBACK = 20
SMT_PAIRS: Dict[str,str] = {
    "EURUSDm":"GBPUSDm","GBPUSDm":"EURUSDm",
    "AUDUSDm":"NZDUSDm","NZDUSDm":"AUDUSDm",
}

RISK_PER_TRADE_PCT      = 1.0
RISK_MIN_PCT            = 0.25
RISK_MAX_PCT            = 1.0
DAILY_LOSS_CAP_PCT      = 3.0
WEEKLY_LOSS_CAP_PCT     = 6.0
MAX_OPEN_POSITIONS      = 4
MAX_CORRELATED_EXPOSURE = 2
EQUITY_CURVE_LOOKBACK   = 20
VOLATILITY_ATR_KILL     = 4.0
CONSECUTIVE_LOSS_KILL   = 5
SPREAD_MAX_PIPS         = 3.0
MIN_RR_RATIO            = 2.0
PARTIAL_CLOSE_RR        = 1.0
PARTIAL_CLOSE_PCT       = 50
MAGIC_NUMBER            = 99999
SLIPPAGE_PIPS           = 0.5
COMMISSION_PER_LOT      = 3.5

EQUITY_TIERS = [
    (10000,1.00),(5000,1.00),(2000,1.00),(1000,0.80),
    (500,0.60),(200,0.40),(100,0.25),(50,0.15),
    (20,0.10),(5,0.05),(0,0.025),
]
MICRO_ACCOUNT_THRESHOLD = 500

AI_MODE             = "xgboost"
AI_MIN_SCORE        = 52
AI_RETRAIN_INTERVAL = 30
AI_SYNTHETIC_SAMPLES= 600

DB_PATH          = "storage/trading_bot.db"
LOG_DIR          = "logs"
LOG_LEVEL        = "INFO"
LOG_MAX_BYTES    = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

MAIN_LOOP_INTERVAL_SEC  = 45
RECONNECT_DELAY_SEC     = 30
MAX_RECONNECT_ATTEMPTS  = 15
CANDLES_REQUIRED        = 300
MIN_BALANCE_TO_TRADE    = 5.0

NEWS_FILTER_ENABLED       = True
CORRELATION_CHECK_ENABLED = True
REGIME_ENGINE_ENABLED     = True
LEARNING_ENGINE_ENABLED   = True
SMT_DIVERGENCE_ENABLED    = True
SPREAD_FILTER_ENABLED     = True
VOLATILITY_KILL_ENABLED   = True
'@ | Out-File -FilePath "C:\ForexBot\config\settings.py" -Encoding UTF8
Write-Host "[1/13] settings.py" -ForegroundColor Green

# ==============================================================================
# FILE 2 — core/logger.py
# ==============================================================================
@'
import logging, os
from logging.handlers import RotatingFileHandler
from config.settings import LOG_DIR, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT

os.makedirs(LOG_DIR, exist_ok=True)
_FMT = "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
_DFMT = "%Y-%m-%d %H:%M:%S"

def _build():
    root = logging.getLogger("forex_bot")
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    if root.handlers: return root
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(_FMT, _DFMT))
    root.addHandler(ch)
    for name, path in [("main","logs/main.log"),("trades","logs/trades.log"),
                        ("ai","logs/ai.log"),("errors","logs/errors.log")]:
        fh = RotatingFileHandler(path, maxBytes=LOG_MAX_BYTES,
                                  backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_FMT, _DFMT))
        if name == "errors": fh.setLevel(logging.WARNING)
        root.addHandler(fh)
    return root

_build()

def get_logger(name):
    return logging.getLogger(f"forex_bot.{name}")
'@ | Out-File -FilePath "C:\ForexBot\core\logger.py" -Encoding UTF8
Write-Host "[2/13] logger.py" -ForegroundColor Green

# ==============================================================================
# FILE 3 — strategy/market_structure.py
# ==============================================================================
@'
import numpy as np, pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from core.logger import get_logger
from config.settings import SWING_PIVOT_BARS,BOS_LOOKBACK,EMA_BIAS_PERIOD,EQUAL_LEVEL_TOLERANCE,SESSION_LOOKBACK

log = get_logger("strategy.market_structure")

@dataclass
class SwingPoint:
    index:int; price:float; kind:str; timestamp:object; strength:float=1.0

@dataclass
class LiquidityPool:
    price:float; kind:str; touches:int=2; swept:bool=False; strength:float=0.5

@dataclass
class StructureEvent:
    kind:str; price:float; bar_index:int; strength:float

@dataclass
class SessionLevel:
    kind:str; price:float; swept:bool=False

@dataclass
class MarketStructureResult:
    bias:str; bias_strength:float; ema_slope:float
    swing_highs:List[SwingPoint]=field(default_factory=list)
    swing_lows:List[SwingPoint]=field(default_factory=list)
    last_bos:Optional[StructureEvent]=None
    last_choch:Optional[StructureEvent]=None
    hh:bool=False; hl:bool=False; lh:bool=False; ll:bool=False
    pools:List[LiquidityPool]=field(default_factory=list)
    session_levels:List[SessionLevel]=field(default_factory=list)
    prev_day_high:float=0.0; prev_day_low:float=0.0
    prev_week_high:float=0.0; prev_week_low:float=0.0

class MarketStructureEngine:
    def __init__(self,pivot_bars=SWING_PIVOT_BARS): self.pivot_bars=pivot_bars

    def analyze(self,df,symbol="",tf="",df_daily=None,df_weekly=None):
        if df is None or len(df)<self.pivot_bars*2+10:
            return MarketStructureResult(bias="neutral",bias_strength=0.0,ema_slope=0.0)
        df=df.tail(BOS_LOOKBACK).copy().reset_index(drop=True)
        sh=self._swings(df,"high"); sl=self._swings(df,"low")
        hh,hl,lh,ll=self._classify(sh,sl)
        events=self._events(df,sh,sl)
        lb=next((e for e in reversed(events) if "BOS" in e.kind),None)
        lc=next((e for e in reversed(events) if "CHOCH" in e.kind),None)
        ema=df["close"].ewm(span=EMA_BIAS_PERIOD).mean()
        ema_slope=float(ema.iloc[-1]-ema.iloc[-5])/(ema.iloc[-5]+1e-9)*100
        bias,strength=self._bias(hh,hl,lh,ll,events,ema_slope)
        pools=self._pools(df); sess=self._session(df)
        pdh=pdl=pwh=pwl=0.0
        if df_daily is not None and len(df_daily)>=2:
            pdh=float(df_daily["high"].iloc[-2]); pdl=float(df_daily["low"].iloc[-2])
        if df_weekly is not None and len(df_weekly)>=2:
            pwh=float(df_weekly["high"].iloc[-2]); pwl=float(df_weekly["low"].iloc[-2])
        return MarketStructureResult(bias=bias,bias_strength=strength,ema_slope=ema_slope,
            swing_highs=sh,swing_lows=sl,last_bos=lb,last_choch=lc,
            hh=hh,hl=hl,lh=lh,ll=ll,pools=pools,session_levels=sess,
            prev_day_high=pdh,prev_day_low=pdl,prev_week_high=pwh,prev_week_low=pwl)

    def _swings(self,df,col):
        swings=[]; n=len(df); p=self.pivot_bars
        for i in range(p,n-p):
            val=df[col].iloc[i]; L=df[col].iloc[i-p:i]; R=df[col].iloc[i+1:i+p+1]
            if col=="high" and val>L.max() and val>R.max():
                swings.append(SwingPoint(i,val,"high",df.index[i] if hasattr(df.index,"__iter__") else i))
            elif col=="low" and val<L.min() and val<R.min():
                swings.append(SwingPoint(i,val,"low",df.index[i] if hasattr(df.index,"__iter__") else i))
        return swings

    def _classify(self,h,l):
        hh=hl=lh=ll=False
        if len(h)>=2: hh=h[-1].price>h[-2].price; lh=h[-1].price<h[-2].price
        if len(l)>=2: hl=l[-1].price>l[-2].price; ll=l[-1].price<l[-2].price
        return hh,hl,lh,ll

    def _events(self,df,h,l):
        events=[]
        if len(h)<2 or len(l)<2: return events
        close=df["close"].iloc[-1]; ph=h[-2].price; pl=l[-2].price
        pb=len(h)>=3 and h[-2].price>h[-3].price
        if close>ph:
            k="BOS_UP" if pb else "CHOCH_UP"
            events.append(StructureEvent(k,ph,len(df)-1,min((close-ph)/(ph*0.001+1e-9),1.0)))
        if close<pl:
            k="BOS_DOWN" if not pb else "CHOCH_DOWN"
            events.append(StructureEvent(k,pl,len(df)-1,min((pl-close)/(pl*0.001+1e-9),1.0)))
        return events

    def _bias(self,hh,hl,lh,ll,events,ema_slope):
        bull=bear=0.0
        if hh: bull+=2
        if hl: bull+=1.5
        if lh: bear+=2
        if ll: bear+=1.5
        for e in events:
            if "UP"   in e.kind: bull+=3 if "CHOCH" in e.kind else 2
            if "DOWN" in e.kind: bear+=3 if "CHOCH" in e.kind else 2
        if ema_slope>0.01: bull+=1.5
        elif ema_slope<-0.01: bear+=1.5
        t=bull+bear+1e-9
        if bull>bear*1.1: return "bullish",min(bull/t,1.0)
        if bear>bull*1.1: return "bearish",min(bear/t,1.0)
        return "neutral",0.5

    def _pools(self,df):
        pools=[]; h=df["high"].values; l=df["low"].values; n=len(df); tol=EQUAL_LEVEL_TOLERANCE
        for i in range(n-1):
            for j in range(i+1,min(i+15,n)):
                if abs(h[i]-h[j])/(h[i]+1e-9)<tol:
                    p=(h[i]+h[j])/2
                    ex=next((x for x in pools if x.kind=="high_pool" and abs(x.price-p)/(p+1e-9)<tol),None)
                    if ex: ex.touches+=1; ex.strength=min(ex.touches/5,1.0)
                    else: pools.append(LiquidityPool(p,"high_pool"))
                if abs(l[i]-l[j])/(l[i]+1e-9)<tol:
                    p=(l[i]+l[j])/2
                    ex=next((x for x in pools if x.kind=="low_pool" and abs(x.price-p)/(p+1e-9)<tol),None)
                    if ex: ex.touches+=1; ex.strength=min(ex.touches/5,1.0)
                    else: pools.append(LiquidityPool(p,"low_pool"))
        return pools

    def _session(self,df):
        levels=[]
        try:
            if not hasattr(df.index,"hour"): return levels
            hour=df.index.hour
            for sess,(sh,eh) in [("asia",(0,8)),("london",(7,16)),("ny",(12,21))]:
                mask=(hour>=sh)&(hour<eh); s=df[mask].tail(SESSION_LOOKBACK)
                if len(s)>0:
                    levels.append(SessionLevel(f"{sess}_h",float(s["high"].max())))
                    levels.append(SessionLevel(f"{sess}_l",float(s["low"].min())))
        except: pass
        return levels
'@ | Out-File -FilePath "C:\ForexBot\strategy\market_structure.py" -Encoding UTF8
Write-Host "[3/13] market_structure.py" -ForegroundColor Green

# ==============================================================================
# FILE 4 — strategy/crt_engine.py
# ==============================================================================
@'
import numpy as np, pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.logger import get_logger
from config.settings import (CRT_SWEEP_THRESHOLD_PCT,CRT_SWEEP_MAX_CLOSE_PCT,
    CRT_CONFIRMATION_BODY_ATR,CRT_CONFIRMATION_CLOSE_PCT,DISPLACEMENT_ATR_MULT,
    DISPLACEMENT_CLOSE_PCT,FVG_MAX_LOOKBACK,FVG_MIN_SIZE_PIPS,
    MIN_RR_RATIO,SL_ATR_BUFFER,SWEEP_WICK_MIN_PCT,SWEEP_LOOKBACK_BARS)

log = get_logger("strategy.crt_engine")

@dataclass
class LiquiditySweep:
    kind:str; swept_level:float; sweep_high:float; sweep_low:float
    sweep_close:float; bar_index:int; wick_pct:float; level_type:str; strength:float

@dataclass
class DisplacementCandle:
    direction:str; bar_index:int; body_atr:float
    close_pct:float; volume_ratio:float; is_valid:bool

@dataclass
class FairValueGap:
    kind:str; top:float; bottom:float; mid:float; size_pips:float; bar_index:int; filled:bool=False

@dataclass
class CRTSignal:
    symbol:str; direction:str; entry_price:float; entry_top:float; entry_bottom:float
    stop_loss:float; sl_pips:float; take_profit_1:float; take_profit_2:float
    take_profit_3:float; dol_target:float; rr_ratio:float; confidence:float
    ai_score:float=0.0; displacement_str:float=0.0; fvg_size_pips:float=0.0
    sweep_strength:float=0.0; timeframe:str=""; killzone:str=""
    signal_time:datetime=field(default_factory=datetime.utcnow)
    reason:str=""; zone:object=None; sweep:object=None
    displacement:object=None; fvg:object=None
    metadata:Dict[str,Any]=field(default_factory=dict)

    def to_dict(self):
        return {"symbol":self.symbol,"direction":self.direction,
                "entry_price":self.entry_price,"stop_loss":self.stop_loss,
                "take_profit_1":self.take_profit_1,"take_profit_2":self.take_profit_2,
                "rr_ratio":self.rr_ratio,"confidence":self.confidence,
                "ai_score":self.ai_score,"timeframe":self.timeframe,
                "signal_time":str(self.signal_time),"reason":self.reason,
                "killzone":self.killzone,"dol_target":self.dol_target,
                "displacement":self.displacement_str,"fvg_size_pips":self.fvg_size_pips}

def _pip(symbol,point):
    s=symbol.replace("m","").upper()
    if "JPY" in s or "XAU" in s or "XAG" in s: return point*100
    if "BTC" in s or "ETH" in s: return point*10
    return point*10

class CRTEngine:
    def generate_signal(self,symbol,direction,df,ms,point,killzone,zones=None):
        if df is None or len(df)<30: return None
        atr=float((df["high"]-df["low"]).tail(14).mean())
        if atr==0: return None
        pip=_pip(symbol,point)
        sweep=self._sweep(df,ms,direction,atr,pip)
        if sweep is None: return None
        if direction=="BUY" and sweep.kind!="LOW_SWEPT": return None
        if direction=="SELL" and sweep.kind!="HIGH_SWEPT": return None
        if not self._crt3(df,sweep,direction,atr): return None
        disp=self._disp(df,sweep,direction,atr)
        if disp is None or not disp.is_valid: return None
        fvg=self._fvg(df,disp,direction,atr,pip)
        if fvg is None: return None
        return self._build(symbol,direction,df,sweep,disp,fvg,ms,killzone,atr,pip,point,zones)

    def _sweep(self,df,ms,direction,atr,pip):
        n=len(df); levels=[]
        if ms.prev_day_high: levels+=[(ms.prev_day_high,"PDH",1.0),(ms.prev_day_low,"PDL",1.0)]
        if ms.prev_week_high: levels+=[(ms.prev_week_high,"PWH",0.95),(ms.prev_week_low,"PWL",0.95)]
        for sl in ms.session_levels: levels.append((sl.price,sl.kind.upper(),0.85))
        for sh in ms.swing_highs[-5:]: levels.append((sh.price,"SwingH",0.80))
        for sl in ms.swing_lows[-5:]: levels.append((sl.price,"SwingL",0.80))
        for p in ms.pools: levels.append((p.price,"EQ"+("H" if "high" in p.kind else "L"),min(0.85*p.strength+0.3,1.0)))
        if len(df)>=20:
            levels+=[(float(df["high"].tail(20).max()),"SessH",0.75),
                     (float(df["low"].tail(20).min()),"SessL",0.75)]
        for i in range(max(0,n-SWEEP_LOOKBACK_BARS),n-1):
            bar=df.iloc[i]; rng=bar["high"]-bar["low"]
            if rng==0: continue
            for lp,lt,ls in levels:
                if bar["high"]>lp>bar["close"]:
                    wp=(bar["high"]-max(bar["open"],bar["close"]))/rng
                    if wp>=SWEEP_WICK_MIN_PCT:
                        return LiquiditySweep("HIGH_SWEPT",lp,bar["high"],bar["low"],bar["close"],i,wp,lt,ls)
                if bar["low"]<lp<bar["close"]:
                    wp=(min(bar["open"],bar["close"])-bar["low"])/rng
                    if wp>=SWEEP_WICK_MIN_PCT:
                        return LiquiditySweep("LOW_SWEPT",lp,bar["high"],bar["low"],bar["close"],i,wp,lt,ls)
        return None

    def _crt3(self,df,sweep,direction,atr):
        i=sweep.bar_index
        if i<2: return False
        c1=df.iloc[i-1]; c2=df.iloc[i]; c3i=min(i+1,len(df)-1); c3=df.iloc[c3i]
        c1r=c1["high"]-c1["low"]
        if c1r==0: return False
        if direction=="BUY":
            if c1["low"]-c2["low"]<c1r*CRT_SWEEP_THRESHOLD_PCT: return False
            if c1["low"]-c2["close"]>c1r*CRT_SWEEP_MAX_CLOSE_PCT: return False
            body=abs(c3["close"]-c3["open"]); rng=c3["high"]-c3["low"]
            cp=(c3["close"]-c3["low"])/(rng+1e-9)
            return c3["close"]>c1["high"]*0.999 and body>=CRT_CONFIRMATION_BODY_ATR*atr and cp>=CRT_CONFIRMATION_CLOSE_PCT
        else:
            if c2["high"]-c1["high"]<c1r*CRT_SWEEP_THRESHOLD_PCT: return False
            if c2["close"]-c1["high"]>c1r*CRT_SWEEP_MAX_CLOSE_PCT: return False
            body=abs(c3["close"]-c3["open"]); rng=c3["high"]-c3["low"]
            cp=(c3["high"]-c3["close"])/(rng+1e-9)
            return c3["close"]<c1["low"]*1.001 and body>=CRT_CONFIRMATION_BODY_ATR*atr and cp>=CRT_CONFIRMATION_CLOSE_PCT

    def _disp(self,df,sweep,direction,atr):
        n=len(df); va=df["volume"].tail(20).mean()
        for i in range(sweep.bar_index,min(sweep.bar_index+FVG_MAX_LOOKBACK,n)):
            bar=df.iloc[i]; rng=bar["high"]-bar["low"]
            if rng==0: continue
            body=abs(bar["close"]-bar["open"]); vr=float(bar["volume"])/(va+1e-9)
            if direction=="BUY" and bar["close"]>bar["open"]:
                ba=body/(atr+1e-9); ro=rng>=DISPLACEMENT_ATR_MULT*atr
                cp=(bar["close"]-bar["low"])/rng; co=cp>=(1-DISPLACEMENT_CLOSE_PCT)
                return DisplacementCandle("BULLISH",i,ba,cp,vr,ro and co)
            elif direction=="SELL" and bar["close"]<bar["open"]:
                ba=body/(atr+1e-9); ro=rng>=DISPLACEMENT_ATR_MULT*atr
                cp=(bar["high"]-bar["close"])/rng; co=cp>=(1-DISPLACEMENT_CLOSE_PCT)
                return DisplacementCandle("BEARISH",i,ba,cp,vr,ro and co)
        return None

    def _fvg(self,df,disp,direction,atr,pip):
        n=len(df); best=None; bs=0
        for i in range(max(disp.bar_index-2,0)+2,min(disp.bar_index+FVG_MAX_LOOKBACK,n)):
            c0=df.iloc[i-2]; c2=df.iloc[i]
            if direction=="BUY" and c2["low"]>c0["high"]:
                sz=(c2["low"]-c0["high"])/pip
                if sz>=FVG_MIN_SIZE_PIPS and sz>bs:
                    bs=sz; best=FairValueGap("BULLISH_FVG",c2["low"],c0["high"],(c2["low"]+c0["high"])/2,sz,i)
            elif direction=="SELL" and c2["high"]<c0["low"]:
                sz=(c0["low"]-c2["high"])/pip
                if sz>=FVG_MIN_SIZE_PIPS and sz>bs:
                    bs=sz; best=FairValueGap("BEARISH_FVG",c0["low"],c2["high"],(c0["low"]+c2["high"])/2,sz,i)
        return best

    def _build(self,symbol,direction,df,sweep,disp,fvg,ms,kz,atr,pip,point,zones):
        entry=fvg.mid; buf=SL_ATR_BUFFER*atr
        sl=sweep.sweep_low-buf if direction=="BUY" else sweep.sweep_high+buf
        risk=abs(entry-sl); min_r=pip*8
        if risk<min_r: sl=entry-min_r if direction=="BUY" else entry+min_r; risk=min_r
        if risk<=0 or risk>entry*0.05: return None
        tp1=entry+risk*2 if direction=="BUY" else entry-risk*2
        tp2=entry+risk*3 if direction=="BUY" else entry-risk*3
        tp3=entry+risk*5 if direction=="BUY" else entry-risk*5
        rr=abs(tp1-entry)/risk
        if rr<MIN_RR_RATIO: return None
        dol=self._dol(ms,direction)
        score,reasons=self._score(sweep,disp,fvg,ms,kz,zones,entry,atr,pip)
        return CRTSignal(
            symbol=symbol,direction=direction,
            entry_price=round(entry,5),entry_top=round(fvg.top,5),
            entry_bottom=round(fvg.bottom,5),stop_loss=round(sl,5),
            sl_pips=round(risk/pip,1),take_profit_1=round(tp1,5),
            take_profit_2=round(tp2,5),take_profit_3=round(tp3,5),
            dol_target=round(dol,5) if dol else 0.0,rr_ratio=round(rr,2),
            confidence=round(score,1),displacement_str=round(disp.body_atr,2),
            fvg_size_pips=round(fvg.size_pips,1),sweep_strength=round(sweep.strength,2),
            killzone=kz,reason=" | ".join(reasons),sweep=sweep,displacement=disp,fvg=fvg,
            metadata={"atr":atr,"sweep_type":sweep.level_type,"disp_atr":disp.body_atr,
                      "fvg_pips":fvg.size_pips,"dol":dol or 0.0,"killzone":kz})

    def _score(self,sweep,disp,fvg,ms,kz,zones,entry,atr,pip):
        score=0.0; reasons=[]
        kzp={"silver_bullet":30,"ny_am":25,"london_open":20}
        score+=kzp.get(kz,10)
        reasons.append({"silver_bullet":"Silver Bullet","ny_am":"NY AM",
                        "london_open":"London","other":"Off-Hours"}.get(kz,kz))
        score+=sweep.strength*15+sweep.wick_pct*10
        reasons.append(f"{sweep.level_type}({sweep.strength:.2f})")
        score+=min(disp.body_atr*10,15)
        reasons.append(f"Disp {disp.body_atr:.2f}xATR")
        score+=min(fvg.size_pips/3,10)
        reasons.append(f"FVG {fvg.size_pips:.1f}pips")
        if ms.last_choch: score+=12; reasons.append("CHOCH")
        elif ms.last_bos: score+=8; reasons.append("BOS")
        score+=ms.bias_strength*8
        if zones:
            zt="demand" if sweep.kind=="LOW_SWEPT" else "supply"
            nb=[z for z in zones if z.kind==zt and abs(z.mid-entry)<atr*2]
            if nb: bz=max(nb,key=lambda z:z.strength); score+=min(bz.strength,5); reasons.append(f"SD({bz.origin_tf})")
        if disp.volume_ratio>=1.2: score+=5; reasons.append(f"Vol {disp.volume_ratio:.1f}x")
        return min(score,100.0),reasons

    def _dol(self,ms,direction):
        if direction=="BUY":
            h=[p.price for p in ms.pools if "high" in p.kind]+[ms.prev_day_high,ms.prev_week_high]
            h=[x for x in h if x>0]; return max(h) if h else None
        else:
            l=[p.price for p in ms.pools if "low" in p.kind]+[ms.prev_day_low,ms.prev_week_low]
            l=[x for x in l if x>0]; return min(l) if l else None
'@ | Out-File -FilePath "C:\ForexBot\strategy\crt_engine.py" -Encoding UTF8
Write-Host "[4/13] crt_engine.py" -ForegroundColor Green

# ==============================================================================
# FILE 5 — strategy/smt_divergence.py
# ==============================================================================
@'
import pandas as pd
from dataclasses import dataclass
from typing import Dict
from core.logger import get_logger
from config.settings import SMT_LOOKBACK, SMT_PAIRS

log = get_logger("strategy.smt")

@dataclass
class SMTResult:
    confirmed:bool; kind:str; strength:float; reason:str

class SMTEngine:
    def check(self,symbol,direction,candles):
        corr=SMT_PAIRS.get(symbol)
        if not corr or corr not in candles: return SMTResult(False,"NONE",0.0,"No pair")
        da=candles.get(symbol); db=candles.get(corr)
        if da is None or db is None or len(da)<SMT_LOOKBACK: return SMTResult(False,"NONE",0.0,"No data")
        lb=SMT_LOOKBACK
        ah=da["high"].tail(lb).max(); bh=db["high"].tail(lb).max()
        al=da["low"].tail(lb).min();  bl=db["low"].tail(lb).min()
        pah=da["high"].tail(lb*2).head(lb).max(); pbh=db["high"].tail(lb*2).head(lb).max()
        pal=da["low"].tail(lb*2).head(lb).min();  pbl=db["low"].tail(lb*2).head(lb).min()
        if direction=="SELL" and ah>pah and bh<=pbh:
            s=min(((ah-pah)/(pah+1e-9)+(pbh-bh)/(pbh+1e-9))*10,1.0)
            return SMTResult(True,"BEARISH_SMT",s,f"SMT: {symbol} HH, {corr} failed")
        if direction=="BUY" and al<pal and bl>=pbl:
            s=min(((pal-al)/(pal+1e-9)+(bl-pbl)/(pbl+1e-9))*10,1.0)
            return SMTResult(True,"BULLISH_SMT",s,f"SMT: {symbol} LL, {corr} failed")
        return SMTResult(False,"NONE",0.0,"No divergence")
'@ | Out-File -FilePath "C:\ForexBot\strategy\smt_divergence.py" -Encoding UTF8
Write-Host "[5/13] smt_divergence.py" -ForegroundColor Green

# ==============================================================================
# FILE 6 — strategy/supply_demand.py
# ==============================================================================
@'
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
from core.logger import get_logger

log = get_logger("strategy.supply_demand")

@dataclass
class Zone:
    kind:str; top:float; bottom:float; strength:float
    retests:int=0; fresh:bool=True; origin_tf:str=""; bar_time:object=None
    @property
    def mid(self): return (self.top+self.bottom)/2
    def contains(self,price): return self.bottom<=price<=self.top
    def is_valid(self): return self.fresh and self.retests<3 and self.strength>=2

class SupplyDemandEngine:
    def __init__(self): self._zones=[]

    def detect_zones(self,df,timeframe="",point=0.0001):
        if df is None or len(df)<10: return []
        df=df.tail(100).copy().reset_index(drop=True)
        zones=[]; price_level=df["close"].iloc[-1]
        if price_level>10000: pip=point*10; ext=pip*50
        elif price_level>1000: pip=point*100; ext=pip*20
        elif price_level>100: pip=point*100; ext=pip*5
        else: pip=point*10; ext=pip*5
        for i in range(2,len(df)-1):
            base=df.iloc[i]; body=abs(base["close"]-base["open"]); rng=base["high"]-base["low"]
            if rng==0: continue
            if body/rng>0.5: continue
            prev=df.iloc[i-1]; nxt=df.iloc[i+1]
            pr=prev["high"]-prev["low"]+1e-9; nr=nxt["high"]-nxt["low"]+1e-9
            di=(prev["open"]-prev["close"])/pr; ri=(nxt["close"]-nxt["open"])/nr
            if di>0.55 and ri>0.45:
                zones.append(Zone("demand",base["high"]+ext,base["low"]-ext,
                    min(di*3+ri*3+(1-body/rng)*2,10.0),origin_tf=timeframe))
            ri2=(prev["close"]-prev["open"])/pr; di2=(nxt["open"]-nxt["close"])/nr
            if ri2>0.55 and di2>0.45:
                zones.append(Zone("supply",base["high"]+ext,base["low"]-ext,
                    min(ri2*3+di2*3+(1-body/rng)*2,10.0),origin_tf=timeframe))
        cur=df["close"].iloc[-1]
        for z in zones:
            if z.contains(cur): z.retests+=1
            if z.retests>=3: z.fresh=False
        self._zones=[z for z in zones if z.is_valid()]
        return self._zones
'@ | Out-File -FilePath "C:\ForexBot\strategy\supply_demand.py" -Encoding UTF8
Write-Host "[6/13] supply_demand.py" -ForegroundColor Green

# ==============================================================================
# FILE 7 — risk/institutional_risk.py
# ==============================================================================
@'
import math
from datetime import date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from core.logger import get_logger
from config.settings import (RISK_PER_TRADE_PCT,RISK_MIN_PCT,RISK_MAX_PCT,
    DAILY_LOSS_CAP_PCT,WEEKLY_LOSS_CAP_PCT,MAX_OPEN_POSITIONS,MAX_CORRELATED_EXPOSURE,
    EQUITY_CURVE_LOOKBACK,VOLATILITY_ATR_KILL,CONSECUTIVE_LOSS_KILL,
    SPREAD_MAX_PIPS,SL_ATR_BUFFER,EQUITY_TIERS,SLIPPAGE_PIPS)

log = get_logger("risk.institutional")

@dataclass
class RiskAssessment:
    allowed:bool; reason:str; lots:float; risk_pct:float; risk_usd:float
    kill_switch:bool=False; kill_reason:str=""

class InstitutionalRiskManager:
    def __init__(self):
        self._day_bal=0.0; self._week_bal=0.0
        self._day_date=None; self._week_date=None
        self._consec=0; self._outcomes=[]; self._kill=False; self._kill_r=""

    def assess_trade(self,symbol,direction,entry,stop_loss,sl_pips,balance,equity,
                     open_positions,spread_pips=0.0,current_atr=0.0,normal_atr=0.0,symbol_info=None):
        self._update(balance)
        if self._kill: return RiskAssessment(False,f"Kill: {self._kill_r}",0,0,0,True)
        kill,kr=self._chk_kill(balance,equity,spread_pips,current_atr,normal_atr)
        if kill: self._kill=True; self._kill_r=kr; return RiskAssessment(False,kr,0,0,0,True,kr)
        dl=(self._day_bal-equity)/(self._day_bal+1e-9)*100
        if dl>=DAILY_LOSS_CAP_PCT: return RiskAssessment(False,f"Daily cap {dl:.1f}%",0,0,0)
        wl=(self._week_bal-equity)/(self._week_bal+1e-9)*100
        if wl>=WEEKLY_LOSS_CAP_PCT: return RiskAssessment(False,f"Weekly cap",0,0,0)
        if len(open_positions)>=MAX_OPEN_POSITIONS: return RiskAssessment(False,"Max pos",0,0,0)
        buys=sum(1 for p in open_positions if p.get("type")=="BUY")
        sells=sum(1 for p in open_positions if p.get("type")=="SELL")
        if direction=="BUY" and buys>=MAX_CORRELATED_EXPOSURE: return RiskAssessment(False,"Max BUY",0,0,0)
        if direction=="SELL" and sells>=MAX_CORRELATED_EXPOSURE: return RiskAssessment(False,"Max SELL",0,0,0)
        ms=self._max_spread(symbol)
        if spread_pips>ms: return RiskAssessment(False,f"Spread {spread_pips:.1f}>{ms}",0,0,0)
        if equity<balance*0.15: return RiskAssessment(False,"Survival mode",0,0,0)
        rp=self._risk_pct(balance,current_atr,normal_atr)
        lots=self._lots(balance,rp,sl_pips,symbol_info or {})
        rusd=balance*rp/100
        log.info("[%s] Risk: lots=%.2f risk=%.2f%% spread=%.1f dd=%.1f%%",symbol,lots,rp,spread_pips,dl)
        return RiskAssessment(True,"OK",lots,rp,rusd)

    def record_outcome(self,profit,outcome):
        self._outcomes.append(profit)
        if len(self._outcomes)>EQUITY_CURVE_LOOKBACK*2: self._outcomes.pop(0)
        if outcome=="SL": self._consec+=1
        else: self._consec=0
        if self._consec>=CONSECUTIVE_LOSS_KILL:
            self._kill=True; self._kill_r=f"{self._consec} consec losses"

    def reset_kill(self):
        if self._kill and "loss" in self._kill_r.lower():
            self._kill=False; self._kill_r=""; self._consec=0

    def update_tracking(self,balance): self._update(balance)

    def _update(self,balance):
        today=date.today(); week=today.isocalendar()[1]
        if self._day_date!=today: self._day_bal=balance; self._day_date=today; self.reset_kill()
        if self._week_date!=week: self._week_bal=balance; self._week_date=week

    def _chk_kill(self,bal,eq,sp,atr,natr):
        if natr>0 and atr>natr*VOLATILITY_ATR_KILL: return True,f"Vol spike"
        if self._consec>=CONSECUTIVE_LOSS_KILL: return True,f"{self._consec} consec losses"
        return False,""

    def _risk_pct(self,balance,atr,natr):
        base=RISK_PER_TRADE_PCT
        for t,m in EQUITY_TIERS:
            if balance>=t: base=RISK_PER_TRADE_PCT*m; break
        if not self._eq_ok(): base*=0.5
        if natr>0 and atr>0: base*=min(max(natr/(atr+1e-9),0.25),1.5)
        return max(RISK_MIN_PCT,min(RISK_MAX_PCT,round(base,3)))

    def _lots(self,balance,rp,sl_pips,si):
        if sl_pips<=0 or balance<=0: return si.get("volume_min",0.01)
        ra=balance*rp/100; cs=si.get("trade_contract_size",100000)
        pt=si.get("point",0.0001); ps=si.get("pip_size",pt*10); pv=ps*cs
        lots=ra/(sl_pips*pv+1e-9)
        vs=si.get("volume_step",0.01); vn=si.get("volume_min",0.01); vx=si.get("volume_max",100.0)
        return round(max(vn,min(vx,math.floor(lots/vs)*vs)),2)

    def _eq_ok(self):
        if len(self._outcomes)<EQUITY_CURVE_LOOKBACK: return True
        r=self._outcomes[-EQUITY_CURVE_LOOKBACK:]; t=sum(r)
        return t>-abs(sum(abs(x) for x in r))*0.5

    @staticmethod
    def _max_spread(symbol):
        s=symbol.replace("m","").upper()
        if "BTC" in s or "ETH" in s: return 50.0
        if "XAU" in s: return 8.0; 
        if "XAG" in s: return 15.0
        if "ZAR" in s: return 12.0
        if "JPY" in s: return 2.5
        return SPREAD_MAX_PIPS

    def is_drawdown_exceeded(self,equity):
        if self._day_bal<=0: return False
        return (self._day_bal-equity)/self._day_bal*100>=DAILY_LOSS_CAP_PCT

    def can_open_new_trade(self,op,sym,bal,eq,fm=None):
        if len(op)>=MAX_OPEN_POSITIONS: return False
        if self.is_drawdown_exceeded(eq): return False
        if eq<bal*0.15: return False
        return True

    def sl_pips(self,e,sl,pt): return abs(e-sl)/(pt*10)
    def break_even_sl(self,e,d,bp,pt):
        buf=bp*pt*10; return e+buf if d=="BUY" else e-buf
    def tp1_close_volume(self,v,vs):
        h=math.floor(v*0.5/vs)*vs; return max(h,vs)
'@ | Out-File -FilePath "C:\ForexBot\risk\institutional_risk.py" -Encoding UTF8
Write-Host "[7/13] institutional_risk.py" -ForegroundColor Green

# ==============================================================================
# FILE 8 — core/master_scanner.py
# ==============================================================================
@'
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime
from core.logger import get_logger
from config.settings import (HTF_BIAS_TIMEFRAMES,EXECUTION_TIMEFRAMES,CANDLES_REQUIRED,
    AI_MIN_SCORE,KILLZONES_UTC,KILLZONES_DST,ALWAYS_ON_SYMBOLS,
    SMT_DIVERGENCE_ENABLED,NEWS_FILTER_ENABLED,SPREAD_FILTER_ENABLED,
    CORRELATION_CHECK_ENABLED,SMT_PAIRS)
from strategy.market_structure import MarketStructureEngine
from strategy.crt_engine import CRTEngine, CRTSignal
from strategy.supply_demand import SupplyDemandEngine
from strategy.smt_divergence import SMTEngine

log = get_logger("core.master_scanner")
MAX_SAME_DIR=2
AI_BY_KZ={"silver_bullet":47,"ny_am":50,"london_open":52,"other":55}

def _is_dst(): return 3<=datetime.utcnow().month<=11
def get_killzone():
    h=datetime.utcnow().hour
    kz=KILLZONES_DST if _is_dst() else KILLZONES_UTC
    for name,(s,e) in kz.items():
        if s<=h<e: return name
    return None

class MasterScanner:
    def __init__(self,mt5,ai):
        self._mt5=mt5; self._ai=ai
        self._ms=MarketStructureEngine(); self._crt=CRTEngine()
        self._sd=SupplyDemandEngine(); self._smt=SMTEngine()
        self._news=None; self._corr=None
        if NEWS_FILTER_ENABLED:
            try:
                from core.news_filter import NewsFilter; self._news=NewsFilter()
            except: pass
        if CORRELATION_CHECK_ENABLED:
            try:
                from core.correlation_engine import CorrelationEngine; self._corr=CorrelationEngine()
            except: pass

    def scan(self,symbol,open_positions=None):
        open_positions=open_positions or []
        kz=get_killzone(); always=symbol in ALWAYS_ON_SYMBOLS
        if kz is None and not always: return None
        if self._news:
            try:
                ns=self._news.get_state(symbol)
                if not ns.should_trade: return None
            except: pass
        si=self._mt5.get_symbol_info(symbol)
        if si is None: return None
        point=si["point"]
        tick=self._mt5.get_tick(symbol)
        if tick is None: return None
        cur=tick["bid"]
        if SPREAD_FILTER_ENABLED:
            sp=(tick["ask"]-tick["bid"])/(point*10)
            ms2=self._max_spread(symbol)
            if sp>ms2: log.debug("[%s] Spread %.1f>%.1f",symbol,sp,ms2); return None
        else: sp=0.0
        mr={}; dfd=self._mt5.get_candles(symbol,"D1",CANDLES_REQUIRED)
        dfw=self._mt5.get_candles(symbol,"W1",CANDLES_REQUIRED)
        for tf in HTF_BIAS_TIMEFRAMES:
            df=self._mt5.get_candles(symbol,tf,CANDLES_REQUIRED)
            if df is not None and len(df)>=20:
                mr[tf]=self._ms.analyze(df,symbol,tf,dfd,dfw)
        bias,strength=self._agg(mr)
        if bias=="neutral" or strength<0.50: return None
        buys=sum(1 for p in open_positions if p.get("type")=="BUY")
        sells=sum(1 for p in open_positions if p.get("type")=="SELL")
        if bias=="bullish" and buys>=MAX_SAME_DIR: return None
        if bias=="bearish" and sells>=MAX_SAME_DIR: return None
        if self._corr and open_positions:
            try:
                cc=self._corr.check(symbol,"BUY" if bias=="bullish" else "SELL",open_positions)
                if not cc.allowed: return None
            except: pass
        zones=[]
        for ztf in ["D1","H4","H1"]:
            dfz=self._mt5.get_candles(symbol,ztf,CANDLES_REQUIRED)
            if dfz is not None:
                try: zones.extend(self._sd.detect_zones(dfz,timeframe=ztf,point=point))
                except: pass
        smt_bonus=0.0
        if SMT_DIVERGENCE_ENABLED:
            try:
                cm={}
                corr_sym=SMT_PAIRS.get(symbol)
                for s2 in [symbol]+([corr_sym] if corr_sym else []):
                    df=self._mt5.get_candles(s2,"H1",50)
                    if df is not None: cm[s2]=df
                smt=self._smt.check(symbol,"BUY" if bias=="bullish" else "SELL",cm)
                if smt.confirmed: smt_bonus=smt.strength*10
            except: pass
        ms_e=mr.get("H1") or mr.get("H4") or (next(iter(mr.values()),None))
        if ms_e is None: return None
        direction="BUY" if bias=="bullish" else "SELL"
        etfs=EXECUTION_TIMEFRAMES if not always else ["M5","M15","M30","H1"]
        for etf in etfs:
            dfe=self._mt5.get_candles(symbol,etf,CANDLES_REQUIRED)
            if dfe is None or len(dfe)<30: continue
            try: sig=self._crt.generate_signal(symbol,direction,dfe,ms_e,point,kz or "other",zones)
            except Exception as e: log.error("[%s %s] CRT: %s",symbol,etf,e); continue
            if sig is None: continue
            sig.timeframe=etf
            atr=float((dfe["high"]-dfe["low"]).tail(14).mean())
            feats={"htf_bias_score":1.0 if bias=="bullish" else -1.0,"htf_strength":strength,
                   "structure_strength":ms_e.bias_strength,"entry_tf_bias":1.0,
                   "zone_strength":0.0,"zone_retests":2,
                   "ssl_swept":sig.sweep.kind=="LOW_SWEPT" if sig.sweep else False,
                   "bsl_swept":sig.sweep.kind=="HIGH_SWEPT" if sig.sweep else False,
                   "of_score":65.0,"sweep_score":sig.sweep_strength,"rr_ratio":sig.rr_ratio,
                   "session_encoded":{"london_open":1,"ny_am":2,"silver_bullet":3,"other":0}.get(kz or "other",0),
                   "volatility_norm":min(atr/(cur+1e-9)*100,1.0),"confidence_raw":sig.confidence,
                   "zone_freshness":True,"displacement":sig.displacement_str,"fvg_pips":sig.fvg_size_pips}
            ai=min(self._ai.score_signal(feats)+smt_bonus,100.0)
            sig.ai_score=ai
            sig.metadata.update({"features":feats,"htf_bias":bias,"htf_strength":strength,
                "regime":"TRENDING_UP" if bias=="bullish" else "TRENDING_DOWN",
                "session":kz or "other","symbol_info":si,"spread_pips":sp})
            threshold=AI_BY_KZ.get(kz or "other",AI_MIN_SCORE)
            if always: threshold-=3
            if ai<threshold: log.debug("[%s %s] AI=%.1f<%d",symbol,etf,ai,threshold); continue
            log.info("[%s %s] APPROVED: %s AI=%.1f KZ=%s Sweep=%s Disp=%.2f FVG=%.1fpips RR=%.1f",
                     symbol,etf,sig.direction,ai,kz,
                     sig.sweep.kind if sig.sweep else "?",
                     sig.displacement_str,sig.fvg_size_pips,sig.rr_ratio)
            return sig
        return None

    @staticmethod
    def _agg(mr):
        s={"bullish":0.0,"bearish":0.0}; w={"W1":5,"D1":4,"H4":3,"H1":2}
        for tf,res in mr.items():
            wt=w.get(tf,1)
            if res.bias in s: s[res.bias]+=wt*res.bias_strength
        b=s["bullish"]; be=s["bearish"]; t=b+be+1e-9
        if b>be and b/t>0.55: return "bullish",round(b/t,3)
        if be>b and be/t>0.55: return "bearish",round(be/t,3)
        return "neutral",0.0

    @staticmethod
    def _max_spread(symbol):
        s=symbol.replace("m","").upper()
        if "BTC" in s or "ETH" in s: return 50.0
        if "XAU" in s: return 8.0
        if "XAG" in s: return 15.0
        if "ZAR" in s: return 12.0
        if "JPY" in s: return 2.5
        return 3.0
'@ | Out-File -FilePath "C:\ForexBot\core\master_scanner.py" -Encoding UTF8
Write-Host "[8/13] master_scanner.py" -ForegroundColor Green

# ==============================================================================
# FILE 9 — core/trade_manager.py
# ==============================================================================
@'
import math
from typing import Dict, List
from datetime import datetime
from core.logger import get_logger
from config.settings import AI_RETRAIN_INTERVAL, LEARNING_ENGINE_ENABLED, MAGIC_NUMBER
from risk.trailing_stop import TrailingStopManager

log = get_logger("core.trade_manager")
ADDON_MIN_AI   = 75
BAD_TRADE_R    = -1.8

def _pip(symbol, point):
    s=symbol.replace("m","").upper()
    if "JPY" in s or "XAU" in s or "XAG" in s: return point*100
    if "BTC" in s or "ETH" in s: return point*10
    return point*10

class TradeManager:
    def __init__(self,mt5,risk,database,notifier,ai):
        self._mt5=mt5; self._risk=risk; self._db=database
        self._tg=notifier; self._ai=ai
        self._active={}; self._tp1_done=set(); self._retrain_c=0
        self._trailing=TrailingStopManager(mt5)
        self._learning=None
        if LEARNING_ENGINE_ENABLED:
            try:
                from core.trade_learning_engine import TradeLearningEngine
                self._learning=TradeLearningEngine()
            except: pass
        self._restore()

    def execute_signal(self,signal) -> bool:
        si=self._mt5.get_symbol_info(signal.symbol)
        if si is None: return False
        tick=self._mt5.get_tick(signal.symbol)
        if tick is None: return False
        spread_pips=(tick["ask"]-tick["bid"])/(si["point"]*10)
        acct=self._mt5.get_account_info()
        if not acct: return False
        balance=acct["balance"]; equity=acct["equity"]
        free_margin=acct.get("free_margin",equity)
        open_pos=self._mt5.get_open_positions()
        meta=signal.metadata or {}
        atr=meta.get("atr",0.0)
        ra=self._risk.assess_trade(
            signal.symbol,signal.direction,signal.entry_price,signal.stop_loss,
            signal.sl_pips if hasattr(signal,"sl_pips") else self._risk.sl_pips(signal.entry_price,signal.stop_loss,si["point"]),
            balance,equity,open_pos,spread_pips=spread_pips,
            current_atr=atr,normal_atr=atr,symbol_info=si)
        if not ra.allowed:
            log.info("[%s] Trade blocked: %s",signal.symbol,ra.reason)
            return False
        volume=ra.lots
        if volume<=0: return False
        result=self._mt5.place_order(signal.symbol,signal.direction,volume,
                                     signal.stop_loss,signal.take_profit_2,"CRT-V4")
        if result is None:
            log.warning("Order failed: %s %s",signal.symbol,signal.direction)
            return False
        ticket=result["ticket"]
        signal_id=self._db.save_signal(signal.to_dict())
        trade={"ticket":ticket,"signal_id":signal_id,"symbol":signal.symbol,
               "direction":signal.direction,"volume":volume,
               "entry_price":result["price"],"stop_loss":signal.stop_loss,
               "take_profit_1":signal.take_profit_1,"take_profit_2":signal.take_profit_2,
               "open_time":datetime.utcnow(),"ai_score":signal.ai_score,
               "features":meta.get("features",{}),"regime":meta.get("regime","RANGING"),
               "session":meta.get("session","other"),"entry_reason":signal.reason,
               "killzone":signal.killzone if hasattr(signal,"killzone") else "other",
               "sl_pips":signal.sl_pips if hasattr(signal,"sl_pips") else 0}
        self._db.save_trade(trade); self._active[ticket]=trade
        sd=signal.to_dict()
        sd.update({"entry_price":result["price"],"regime":meta.get("regime","RANGING"),
                   "risk_mult":ra.risk_pct,"lots":volume,"is_addon":False,
                   "killzone":signal.killzone if hasattr(signal,"killzone") else "other",
                   "displacement":signal.displacement_str if hasattr(signal,"displacement_str") else 0,
                   "fvg_size_pips":signal.fvg_size_pips if hasattr(signal,"fvg_size_pips") else 0,
                   "dol_target":signal.dol_target if hasattr(signal,"dol_target") else 0})
        self._tg.new_trade_v3(sd)
        log.info("TRADE: %s %s ticket=%d lots=%.2f ai=%.1f spread=%.1fpips",
                 signal.direction,signal.symbol,ticket,volume,signal.ai_score,spread_pips)
        return True

    def monitor_positions(self):
        op=self._mt5.get_open_positions()
        lt={p["ticket"] for p in op}
        for ticket in list(self._active.keys()):
            if ticket not in lt: self._handle_closed(ticket)
        for pos in op:
            if pos["ticket"] not in self._active: continue
            self._check_tp1(pos); self._check_bad(pos)
        self._trailing.update(op)

    def _check_tp1(self,pos):
        ticket=pos["ticket"]
        if ticket in self._tp1_done: return
        trade=self._active.get(ticket,{}); tp1=trade.get("take_profit_1",0)
        if not tp1: return
        d=pos["type"]; cur=pos["current_price"]
        if not((d=="BUY" and cur>=tp1) or (d=="SELL" and cur<=tp1)): return
        si=self._mt5.get_symbol_info(pos["symbol"])
        if si is None: return
        vs=si.get("volume_step",0.01)
        cv=self._risk.tp1_close_volume(pos["volume"],vs)
        if self._mt5.close_position(ticket,volume=cv):
            self._tp1_done.add(ticket)
            be=self._risk.break_even_sl(trade["entry_price"],d,5,si["point"])
            self._mt5.modify_position(ticket,sl=be)
            self._tg.tp_hit(ticket,pos["symbol"],1,pos["profit"])
            log.info("TP1 hit ticket=%d profit=%.4f",ticket,pos["profit"])

    def _check_bad(self,pos):
        ticket=pos["ticket"]
        if ticket in self._tp1_done: return
        trade=self._active.get(ticket,{})
        entry=trade.get("entry_price",pos["open_price"])
        sl=trade.get("stop_loss",pos["sl"])
        risk=abs(entry-sl) if sl else 0
        if risk==0: return
        cur=pos["current_price"]; d=pos["type"]
        r=(cur-entry)/risk if d=="BUY" else (entry-cur)/risk
        if r<BAD_TRADE_R:
            log.warning("[%s] Bad trade %.2fR closing ticket=%d",pos["symbol"],r,ticket)
            if self._mt5.close_position(ticket):
                self._tg.bad_trade_closed(ticket,pos["symbol"],pos["profit"],r)

    def _handle_closed(self,ticket):
        trade=self._active.pop(ticket,{})
        if not trade: return
        self._trailing.remove(ticket)
        history=self._mt5.get_trade_history(days=1)
        deal=next((d for d in history if d["ticket"]==ticket),None)
        import time; count=0
        while deal is None and count<3: time.sleep(1); history=self._mt5.get_trade_history(days=1); deal=next((d for d in history if d["ticket"]==ticket),None); count+=1
        profit=deal["profit"] if deal else 0.0; close_price=deal["price"] if deal else 0.0
        outcome="TP1" if profit>0.001 else ("SL" if profit<-0.001 else "BE")
        entry=trade.get("entry_price",close_price); d=trade.get("direction","BUY")
        risk=abs(entry-trade.get("stop_loss",entry))
        rr=abs(close_price-entry)/risk if risk>0 else 0.0
        si=self._mt5.get_symbol_info(trade.get("symbol",""))
        pm=_pip(trade.get("symbol",""),si["point"] if si else 0.0001)
        pips=(close_price-entry)/pm if d=="BUY" else (entry-close_price)/pm
        self._db.update_trade_close(ticket,close_price,profit,outcome,pips=pips)
        label=1 if outcome in ("TP1","TP2") else 0
        self._db.save_training_sample(ticket,trade.get("features",{}),label)
        self._risk.record_outcome(profit,outcome)
        if self._learning:
            try:
                self._learning.record(ticket=ticket,symbol=trade.get("symbol",""),
                    direction=trade.get("direction",""),entry_reason=trade.get("entry_reason",""),
                    regime=trade.get("regime","RANGING"),session=trade.get("session","other"),
                    atr=0.0,news_state="clear",ai_score=trade.get("ai_score",0),
                    features=trade.get("features",{}),outcome=outcome,rr_achieved=rr,pips=pips)
            except: pass
        self._retrain_c+=1
        if outcome=="SL": self._tg.sl_hit(ticket,trade.get("symbol",""),profit)
        elif outcome=="BE": self._tg.trade_closed_be(ticket,trade.get("symbol",""),pips)
        else: self._tg.trade_closed(ticket,trade.get("symbol",""),profit,pips)
        log.info("Closed: ticket=%d %s profit=%.4f pips=%.1f rr=%.2f",ticket,outcome,profit,pips,rr)
        if self._retrain_c>=AI_RETRAIN_INTERVAL:
            trades=self._db.get_labelled_trades()
            if len(trades)>=20:
                ok=self._ai.retrain(trades)
                if ok:
                    acc=sum(1 for t in trades if t["outcome"]==1)/len(trades)*100
                    self._tg.ai_retrained(len(trades),acc)
                    if self._learning:
                        try:
                            ins=self._learning.get_insights()
                            if ins: self._tg._send(self._learning.telegram_report(ins))
                        except: pass
            self._retrain_c=0

    def _restore(self):
        for t in self._db.get_open_trades(): self._active[t["ticket"]]=t
'@ | Out-File -FilePath "C:\ForexBot\core\trade_manager.py" -Encoding UTF8
Write-Host "[9/13] trade_manager.py" -ForegroundColor Green

# ==============================================================================
# FILE 10 — risk/trailing_stop.py
# ==============================================================================
@'
from core.logger import get_logger
from config.settings import MAGIC_NUMBER

log = get_logger("risk.trailing_stop")

class TrailingStopManager:
    def __init__(self,mt5): self._mt5=mt5; self._peaks={}

    def update(self,positions):
        for pos in positions:
            try:
                ticket=pos["ticket"]; d=pos["type"]
                entry=pos["open_price"]; cur=pos["current_price"]; sl=pos["sl"]
                si=self._mt5.get_symbol_info(pos["symbol"])
                if si is None: continue
                pt=si["point"]; digits=si.get("digits",5); risk=abs(entry-sl) if sl else 0
                if risk==0: continue
                pr=(cur-entry)/risk if d=="BUY" else (entry-cur)/risk
                if pr<1.0: continue
                if ticket not in self._peaks: self._peaks[ticket]=cur
                else:
                    if d=="BUY": self._peaks[ticket]=max(self._peaks[ticket],cur)
                    else: self._peaks[ticket]=min(self._peaks[ticket],cur)
                peak=self._peaks[ticket]; trail=risk*0.5
                if d=="BUY":
                    nsl=round(peak-trail,digits)
                    if nsl>sl+pt: self._mt5.modify_position(ticket,sl=nsl); log.info("Trail SL %d %.5f",ticket,nsl)
                else:
                    nsl=round(peak+trail,digits)
                    if nsl<sl-pt: self._mt5.modify_position(ticket,sl=nsl); log.info("Trail SL %d %.5f",ticket,nsl)
            except Exception as e: log.error("Trail: %s",e)

    def remove(self,ticket): self._peaks.pop(ticket,None)
'@ | Out-File -FilePath "C:\ForexBot\risk\trailing_stop.py" -Encoding UTF8
Write-Host "[10/13] trailing_stop.py" -ForegroundColor Green

# ==============================================================================
# FILE 11 — ai/signal_scorer.py
# ==============================================================================
@'
import os, pickle
import numpy as np
from typing import Dict, List
from core.logger import get_logger
from config.settings import AI_SYNTHETIC_SAMPLES

log = get_logger("ai.signal_scorer")
MODEL_PATH = "storage/ai_model.pkl"

try:
    from xgboost import XGBClassifier
    XGB_OK = True
except:
    XGB_OK = False

def _synthetic(n=600):
    rng=np.random.default_rng(42); h=n//2
    def gw(c):
        return np.column_stack([
            rng.choice([1],c), rng.uniform(0.6,1.0,c), rng.uniform(0.6,1.0,c),
            np.ones(c), rng.uniform(0.6,1.0,c), rng.integers(0,2,c),
            rng.integers(1,2,c), rng.integers(0,2,c), rng.uniform(0.6,1.0,c),
            rng.uniform(0.5,1.0,c), rng.uniform(2.0,5.0,c), rng.integers(1,4,c),
            rng.uniform(0.0,0.5,c), rng.uniform(0.65,1.0,c), np.ones(c),
            rng.uniform(0.5,2.0,c), rng.uniform(5.0,30.0,c)])
    def gl(c):
        return np.column_stack([
            rng.choice([-1,0,1],c), rng.uniform(0.1,0.5,c), rng.uniform(0.1,0.5,c),
            rng.uniform(0.0,0.5,c), rng.uniform(0.0,0.5,c), rng.integers(2,4,c),
            rng.integers(0,2,c), rng.integers(0,2,c), rng.uniform(0.0,0.5,c),
            rng.uniform(0.0,0.3,c), rng.uniform(1.0,2.0,c), rng.integers(0,4,c),
            rng.uniform(0.5,1.0,c), rng.uniform(0.0,0.5,c), rng.integers(0,2,c),
            rng.uniform(0.1,0.5,c), rng.uniform(1.0,3.0,c)])
    Xw=gw(h); yw=np.ones(h,dtype=int)
    Xl=gl(n-h); yl=np.zeros(n-h,dtype=int)
    X=np.vstack([Xw,Xl]); y=np.concatenate([yw,yl])
    sh=rng.permutation(len(y)); return X[sh],y[sh]

class AISignalScorer:
    def __init__(self):
        self._model=None; self._trained=False
        self._load_or_bootstrap()

    def _load_or_bootstrap(self):
        if not XGB_OK: return
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH,"rb") as f: self._model=pickle.load(f)
                self._trained=True; log.info("AI model loaded"); return
            except: pass
        log.info("Bootstrapping AI model...")
        X,y=_synthetic(AI_SYNTHETIC_SAMPLES); self._train(X,y)

    def _train(self,X,y):
        if not XGB_OK: return
        try:
            m=XGBClassifier(n_estimators=300,max_depth=5,learning_rate=0.05,
                            subsample=0.8,colsample_bytree=0.8,eval_metric="logloss",
                            random_state=42,n_jobs=-1)
            m.fit(X,y); self._model=m; self._trained=True
            os.makedirs("storage",exist_ok=True)
            with open(MODEL_PATH,"wb") as f: pickle.dump(m,f)
            log.info("AI trained. Samples=%d",len(y))
        except Exception as e: log.error("Train: %s",e)

    def score_signal(self,features):
        vec=self._vec(features)
        if self._trained and self._model:
            try: return round(float(self._model.predict_proba([vec])[0][1]*100),2)
            except: pass
        return self._rules(features)

    @staticmethod
    def _vec(f):
        return [f.get("htf_bias_score",0.0),f.get("htf_strength",0.0),
                f.get("structure_strength",0.0),f.get("entry_tf_bias",0.0),
                f.get("zone_strength",0.0)/10,f.get("zone_retests",0.0),
                float(f.get("ssl_swept",False)),float(f.get("bsl_swept",False)),
                f.get("of_score",50.0)/100,f.get("sweep_score",0.0),
                f.get("rr_ratio",2.0),f.get("session_encoded",0.0),
                f.get("volatility_norm",0.0),f.get("confidence_raw",0.0)/100,
                float(f.get("zone_freshness",True)),
                f.get("displacement",0.0),f.get("fvg_pips",0.0)]

    @staticmethod
    def _rules(f):
        s=f.get("htf_strength",0)*20+f.get("structure_strength",0)*15
        s+=float(f.get("ssl_swept",False))*15+float(f.get("bsl_swept",False))*15
        s+=min(f.get("displacement",0)*8,15)+min(f.get("fvg_pips",0)/3,10)
        s+=f.get("sweep_score",0)*10+f.get("confidence_raw",0)/100*15
        return max(0.0,min(100.0,round(s,2)))

    def retrain(self,trades):
        if not XGB_OK or len(trades)<20: return False
        try:
            Xs,ys=_synthetic(min(AI_SYNTHETIC_SAMPLES,300))
            rows=[self._vec(t.get("features",{})) for t in trades]
            labels=[int(t.get("outcome",0)) for t in trades]
            X=np.vstack([Xs,np.array(rows)]); y=np.concatenate([ys,np.array(labels)])
            self._train(X,y); return True
        except Exception as e: log.error("Retrain: %s",e); return False
'@ | Out-File -FilePath "C:\ForexBot\ai\signal_scorer.py" -Encoding UTF8
Write-Host "[11/13] signal_scorer.py" -ForegroundColor Green

# ==============================================================================
# FILE 12 — telegram/notifier.py
# ==============================================================================
@'
import threading, time, requests
from datetime import datetime
from core.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = get_logger("telegram.notifier")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
KZ = {"silver_bullet":"🥈⚡ SILVER BULLET","ny_am":"🗽 NY AM SESSION",
      "london_open":"🇬🇧 LONDON OPEN","other":"🕐 OFF-HOURS"}

class TelegramNotifier:
    def __init__(self):
        self._enabled=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN!="YOUR_BOT_TOKEN")
        log.info("Telegram %s","ENABLED" if self._enabled else "DISABLED")

    def startup_v2(self,balance,account,pairs,is_micro):
        tier="🔬 MICRO" if is_micro else "💼 STANDARD"
        self._send(
            f"╔══════════════════════════════╗\n"
            f"║  🏛️  INSTITUTIONAL CRT BOT V4   ║\n"
            f"╚══════════════════════════════╝\n\n"
            f"🏦 Account:  {account}\n"
            f"💰 Balance:  ${balance:,.2f}\n"
            f"📊 Mode:     {tier}\n"
            f"🎯 Pairs:    {pairs} symbols\n\n"
            f"📐 Engine: Systematic CRT + Romeo ICT\n"
            f"⏰ Kill Zones (EST):\n"
            f"   🇬🇧 London:  02-05 AM\n"
            f"   🗽 NY AM:    08:30-11 AM\n"
            f"   🥈 Silver:   10-11 AM ← Priority\n\n"
            f"✅ CRT 3-Candle: Systematic\n"
            f"✅ Sweep: Wick≥50% rule\n"
            f"✅ Disp: Range>1.5xATR\n"
            f"✅ FVG: 50% equilibrium entry\n"
            f"✅ SL: Beyond sweep extreme\n"
            f"✅ TP: 2R / 3R / DOL\n"
            f"✅ SMT Divergence: ON\n"
            f"✅ Daily Cap: 3% | Weekly: 6%\n"
            f"✅ Kill Switch: {5} consec losses\n"
            f"❤️  Heartbeat: Every 3 hrs\n\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def startup(self,b,a): self.startup_v2(b,a,30,b<500)

    def heartbeat(self,balance,equity,open_trades,pairs):
        pnl=equity-balance; ei="📈" if pnl>=0 else "📉"
        bars="█"*open_trades+"░"*(5-min(open_trades,5))
        bl="🔴" if balance<20 else("🟡" if balance<100 else "🟢")
        self._send(
            f"💓 HEARTBEAT  ·  BOT ALIVE\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"💰 Balance: ${balance:,.2f} {bl}\n"
            f"⚖️  Equity:  ${equity:,.2f}\n"
            f"{ei} Float:  ${pnl:+.4f}\n"
            f"📂 Trades: [{bars}] {open_trades}/4\n"
            f"🌐 Pairs:  {pairs}\n"
            f"⏳ Next:   3 hours\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def new_trade_v3(self,s):
        d=s.get("direction","BUY"); sym=s.get("symbol","")
        ai=s.get("ai_score",0); kz=s.get("killzone","other")
        di="🟢 BUY  ▲ LONG" if d=="BUY" else "🔴 SELL ▼ SHORT"
        arrow="📈" if d=="BUY" else "📉"
        kzl=KZ.get(kz,"🕐")
        tags=[]
        if "XAU" in sym: tags.append("🥇 GOLD")
        if "BTC" in sym: tags.append("₿ CRYPTO")
        if "ETH" in sym: tags.append("⟠ ETH")
        if s.get("is_addon"): tags.append("➕ ADD-ON")
        if ai>=85: tags.append("🔥 PREMIUM")
        elif ai>=70: tags.append("⭐ HIGH CONF")
        tl="  ".join(tags)
        ab="█"*int(min(ai,100)/10)+"░"*(10-int(min(ai,100)/10))
        dol=s.get("dol_target",0); dl=f"🎯 DOL:     {dol:.5f}\n" if dol else ""
        disp=s.get("displacement",0); fvg=s.get("fvg_size_pips",0)
        self._send(
            f"{arrow} CRT SIGNAL\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{kzl}\n{tl}\n\n"
            f"💱 {sym}  ·  {di}\n\n"
            f"🎯 Entry:   {s.get('entry_price',0):.5f}  ← FVG 50%\n"
            f"🛑 SL:      {s.get('stop_loss',0):.5f}  ← Sweep extreme\n"
            f"🎁 TP1(2R): {s.get('take_profit_1',0):.5f}\n"
            f"🏆 TP2(3R): {s.get('take_profit_2',0):.5f}\n"
            f"{dl}"
            f"⚖️  RR:      {s.get('rr_ratio',0):.1f}R\n"
            f"📦 Lots:    {s.get('lots',0):.2f}\n\n"
            f"🧠 AI: [{ab}] {ai:.0f}/100\n"
            f"💥 Disp:   {disp:.2f}x ATR\n"
            f"📐 FVG:    {fvg:.1f} pips\n\n"
            f"💡 {s.get('reason','')}\n\n"
            f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def new_trade(self,s): self.new_trade_v3(s)

    def tp_hit(self,ticket,symbol,tp_level,profit):
        self._send(
            f"✅ TP{tp_level} HIT {'⭐'*tp_level}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💰 ${profit:+.4f}\n"
            f"🔒 SL → Break-Even\n"
            f"🏃 Running to TP{tp_level+1}...\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def trade_closed(self,ticket,symbol,profit,pips):
        r="PROFIT 💰" if profit>0 else "LOSS"
        self._send(
            f"{'✅' if profit>0 else '❌'} CLOSED — {r}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💵 ${profit:+.4f}\n📏 {pips:+.1f} pips\n"
            f"🕐 {datetime.utcnow().strftime('%H:%M')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def trade_closed_be(self,ticket,symbol,pips):
        self._send(f"🔰 BREAKEVEN\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n🛡️ Capital protected\n📏 {pips:+.1f} pips")

    def sl_hit(self,ticket,symbol,loss):
        self._send(
            f"❌ STOP LOSS HIT\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💸 ${loss:+.4f}\n📌 SL protected capital\n"
            f"🔄 Next setup...\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def bad_trade_closed(self,ticket,symbol,profit,r):
        self._send(f"⚠️ BAD TRADE CLOSED\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n📉 {r:.2f}R\n💸 ${profit:+.4f}\n🛡️ Capital preserved")

    def drawdown_warning(self,balance,equity,loss_pct):
        self._send(
            f"⚠️ DAILY LIMIT HIT — ONE WARNING\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📉 {loss_pct:.1f}% daily loss\n"
            f"💰 ${balance:,.2f} | ⚖️ ${equity:,.2f}\n"
            f"🔒 No new trades today\n"
            f"🔄 Auto-resumes tomorrow\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def drawdown_recovered(self,balance,equity):
        self._send(f"✅ TRADING RESUMED\n━━━━━━━━━━━━━━━━\n💰 ${balance:,.2f}\n⚖️ ${equity:,.2f}\n🚀 Hunting setups!")

    def account_empty(self): self._send("🚨 ACCOUNT EMPTY\n━━━━━━━━━━━━━━━━\n⛔ Halted\n💡 Please deposit")
    def account_low(self,bal): self._send(f"⚠️ BALANCE LOW\n━━━━━━━━━━━━━━━━\n💰 ${bal:.2f}\n💡 Top up")

    def daily_summary(self,s):
        wins=s.get("wins",0); losses=s.get("losses",0); total=s.get("total_trades",0)
        pnl=s.get("net_pnl",0); bal=s.get("balance",0)
        wb=("🟢"*wins+"🔴"*losses) if total>0 else "⬜ No trades"
        pi="📈" if pnl>=0 else "📉"
        self._send(
            f"📅 DAILY SUMMARY\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📆 {s.get('date','')}\n{wb}\n"
            f"🎯 {total} trades | ✅ {wins} | ❌ {losses}\n"
            f"📊 WR: {s.get('win_rate',0):.1f}%\n"
            f"{pi} PnL: ${pnl:+.4f}\n"
            f"💰 Balance: ${bal:,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def weekly_summary(self,s):
        pnl=s.get("net_pnl",0); pi="📈" if pnl>=0 else "📉"
        self._send(f"🗓️ WEEKLY\n━━━━━━━━━━━━━━━━\n📊 WR: {s.get('win_rate',0):.1f}%\n{pi} ${pnl:+.4f}")

    def ai_retrained(self,s,a):
        b="█"*int(a/10)+"░"*(10-int(a/10))
        self._send(f"🤖 AI RETRAINED\n━━━━━━━━━━━━━━━━\n📚 {s} samples\n🎯 [{b}] {a:.1f}%")

    def mt5_connected(self,server):
        self._send(f"🔌 MT5 RECONNECTED\n━━━━━━━━━━━━━━━━\n🖥️ {server}\n🕐 {datetime.utcnow().strftime('%H:%M')} UTC")

    def error(self,m): self._send(f"🚨 ERROR\n━━━━━━━━━━━━━━━━\n{m}")
    def warning(self,m): self._send(f"⚠️ WARNING\n━━━━━━━━━━━━━━━━\n{m}")

    def _send(self,text):
        if not self._enabled: return
        threading.Thread(target=self._post,args=(text,),daemon=True).start()

    def _post(self,text,retries=3):
        for i in range(retries):
            try:
                r=requests.post(API_URL,json={"chat_id":TELEGRAM_CHAT_ID,"text":text},timeout=15)
                if r.status_code==200: return
            except Exception as e: log.warning("TG %d: %s",i+1,e)
            time.sleep(3**i)
'@ | Out-File -FilePath "C:\ForexBot\telegram\notifier.py" -Encoding UTF8
Write-Host "[12/13] notifier.py" -ForegroundColor Green

# ==============================================================================
# FILE 13 — main.py
# ==============================================================================
@'
import os,sys,time,signal,traceback,threading
from datetime import datetime,date

ROOT=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)

from core.logger import get_logger
from config import settings
from mt5.connector import MT5Connector
from core.master_scanner import MasterScanner,get_killzone
from core.trade_manager import TradeManager
from core.reporting import ReportingEngine
from risk.institutional_risk import InstitutionalRiskManager
from storage.database import Database
from telegram.notifier import TelegramNotifier
from ai.signal_scorer import AISignalScorer

log=get_logger("main")
_RUNNING=True
ADDON_AI=75

def _stop(s,f):
    global _RUNNING; _RUNNING=False

signal.signal(signal.SIGINT,_stop)
signal.signal(signal.SIGTERM,_stop)

class ForexBot:
    def __init__(self):
        log.info("="*65)
        log.info("  INSTITUTIONAL CRT BOT V4")
        log.info("  CRT + Romeo ICT + SMT + Institutional Risk")
        log.info("  Pairs: %d | Kill Zones: London/NY/Silver Bullet",len(settings.SYMBOLS))
        log.info("="*65)
        self.db=Database(); self.notifier=TelegramNotifier()
        self.mt5=MT5Connector(); self.risk=InstitutionalRiskManager()
        self.ai=AISignalScorer()
        self.scanner=None; self.trader=None; self.reporter=None
        self._dd_warned_date=None; self._dd_active=False
        self._dd_recovery_sent=False; self._low_warned=False

    def start(self):
        log.info("Connecting to MT5...")
        connected=False
        for i in range(20):
            log.info("MT5 attempt %d/20...",i+1)
            if self.mt5.connect(): connected=True; break
            time.sleep(15)
        if not connected:
            self.notifier.error("MT5 connection failed!"); sys.exit(1)
        self.scanner=MasterScanner(self.mt5,self.ai)
        self.trader=TradeManager(self.mt5,self.risk,self.db,self.notifier,self.ai)
        self.reporter=ReportingEngine(self.db,self.notifier)
        acct=self.mt5.get_account_info()
        if acct:
            self.notifier.startup_v2(acct["balance"],acct["login"],
                                     len(settings.SYMBOLS),acct["balance"]<500)
        threading.Thread(target=self._heartbeat,daemon=True).start()
        log.info("Bot live. Scanning %d pairs every %ds",
                 len(settings.SYMBOLS),settings.MAIN_LOOP_INTERVAL_SEC)
        self._loop()

    def _heartbeat(self):
        time.sleep(10800)
        while _RUNNING:
            try:
                acct=self.mt5.get_account_info()
                if acct:
                    op=self.mt5.get_open_positions()
                    self.notifier.heartbeat(acct["balance"],acct["equity"],
                                            len(op),len(settings.SYMBOLS))
            except Exception as e: log.error("Heartbeat: %s",e)
            time.sleep(10800)

    def _loop(self):
        global _RUNNING; errors=0
        while _RUNNING:
            t0=time.time()
            try: self._cycle(); errors=0
            except KeyboardInterrupt: break
            except Exception as e:
                errors+=1; log.error("Loop:\n%s",traceback.format_exc())
                if errors<=2: self.notifier.error(f"Error #{errors}: {e}")
                if errors>=5:
                    self.mt5.disconnect(); time.sleep(10)
                    for i in range(15):
                        if self.mt5.connect(): break
                        time.sleep(15)
                    errors=0
            time.sleep(max(0,settings.MAIN_LOOP_INTERVAL_SEC-(time.time()-t0)))
        self.mt5.disconnect()

    def _cycle(self):
        if not self.mt5.is_connected():
            for i in range(10):
                if self.mt5.connect():
                    self.notifier.mt5_connected(settings.MT5_SERVER); break
                time.sleep(15)
            return
        acct=self.mt5.get_account_info()
        if not acct: return
        balance=acct["balance"]; equity=acct["equity"]
        if balance<=0.01:
            if not self._low_warned: self._low_warned=True; self.notifier.account_empty()
            return
        if balance<settings.MIN_BALANCE_TO_TRADE:
            if not self._low_warned: self._low_warned=True; self.notifier.account_low(balance)
            self.trader.monitor_positions(); return
        if self._low_warned and balance>=settings.MIN_BALANCE_TO_TRADE: self._low_warned=False
        self.risk.update_tracking(balance)
        dd=self.risk.is_drawdown_exceeded(equity); today=date.today()
        if dd:
            self._dd_active=True
            if self._dd_warned_date!=today:
                self._dd_warned_date=today; self._dd_recovery_sent=False
                lp=(balance-equity)/balance*100 if balance>0 else 0
                self.notifier.drawdown_warning(balance,equity,lp)
            self.trader.monitor_positions(); return
        else:
            if self._dd_active and not self._dd_recovery_sent:
                self._dd_active=False; self._dd_recovery_sent=True
                self.notifier.drawdown_recovered(balance,equity)
        self.trader.monitor_positions()
        for symbol in settings.SYMBOLS:
            try:
                cop=self.mt5.get_open_positions(); nop=len(cop)
                csyms={p["symbol"] for p in cop}
                if nop<settings.MAX_OPEN_POSITIONS:
                    sig=self.scanner.scan(symbol,open_positions=cop)
                    if sig:
                        if symbol in csyms:
                            if sig.ai_score>=ADDON_AI: self.trader.execute_signal(sig)
                        else: self.trader.execute_signal(sig)
                elif nop>=settings.MAX_OPEN_POSITIONS and symbol in csyms:
                    sig=self.scanner.scan(symbol,open_positions=cop)
                    if sig and sig.ai_score>=ADDON_AI: self.trader.execute_signal(sig)
            except Exception as e: log.error("[%s] Scan: %s",symbol,e)
        self.reporter.check_and_send_reports(balance)

if __name__=="__main__":
    try:
        from dotenv import load_dotenv; load_dotenv(".env")
    except: pass
    ForexBot().start()
'@ | Out-File -FilePath "C:\ForexBot\main.py" -Encoding UTF8
Write-Host "[13/13] main.py" -ForegroundColor Green

# ==============================================================================
# Clear old AI model + Start Bot
# ==============================================================================
Remove-Item "C:\ForexBot\storage\ai_model.pkl" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Starting Institutional CRT Bot V4..." -ForegroundColor Cyan
Start-Process -FilePath "C:\Program Files\Python311\python.exe" `
    -ArgumentList "C:\ForexBot\main.py" `
    -WorkingDirectory "C:\ForexBot" `
    -WindowStyle Normal
Start-Sleep -Seconds 25
Get-Content "C:\ForexBot\logs\main.log" -Tail 20

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  INSTITUTIONAL CRT BOT V4 — LIVE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  📐 Strategy:  CRT + Romeo ICT" -ForegroundColor White
Write-Host "  ⚙️  Engine:    Zero discretion" -ForegroundColor White
Write-Host "  ⏰ Sessions:  London / NY / Silver Bullet" -ForegroundColor White
Write-Host "  💧 Sweep:     Wick≥50% + close-back rule" -ForegroundColor White
Write-Host "  💥 Disp:      Range>1.5xATR + close in 20%" -ForegroundColor White
Write-Host "  📐 Entry:     FVG 50% (equilibrium)" -ForegroundColor White
Write-Host "  🛑 SL:        Beyond sweep extreme + ATR buf" -ForegroundColor White
Write-Host "  🎯 Targets:   2R / 3R / Draw on Liquidity" -ForegroundColor White
Write-Host "  📊 SMT:       Correlated pair divergence" -ForegroundColor White
Write-Host "  🛡️  Risk:      Kill switch + equity curve" -ForegroundColor White
Write-Host "  📉 Daily cap: 3% | Weekly cap: 6%" -ForegroundColor White
Write-Host "  🔴 Kill:      5 consecutive losses" -ForegroundColor White
Write-Host ""
Write-Host "  Telegram startup message incoming..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
