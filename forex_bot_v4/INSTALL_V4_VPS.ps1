# ==============================================================================
# INSTITUTIONAL CRT BOT V4 — VPS INSTALLER
# Paste entire script in PowerShell as Administrator
# ==============================================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  INSTITUTIONAL CRT BOT V4 - REBUILDING" -ForegroundColor Cyan
Write-Host "  CRT + Romeo ICT + Full Risk Management" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Write-Host "Old bot stopped." -ForegroundColor Yellow

# Create module directories
New-Item -ItemType Directory -Force -Path C:\ForexBot\strategy   | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\risk       | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\core       | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\storage    | Out-Null
New-Item -ItemType Directory -Force -Path C:\ForexBot\logs       | Out-Null

# ==============================================================================
# settings.py
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

KILLZONES_UTC: Dict[str,tuple] = {"london_open":(7,10),"ny_am":(13,16),"silver_bullet":(15,16)}
KILLZONES_DST: Dict[str,tuple] = {"london_open":(6,9), "ny_am":(12,15),"silver_bullet":(14,15)}

CRT_SWEEP_THRESHOLD_PCT    = 0.10
CRT_SWEEP_MAX_CLOSE_PCT    = 0.15
CRT_CONFIRMATION_BODY_ATR  = 0.40
CRT_CONFIRMATION_CLOSE_PCT = 0.60

DISPLACEMENT_ATR_MULT   = 1.5
DISPLACEMENT_CLOSE_PCT  = 0.20
DISPLACEMENT_VOL_MULT   = 1.2
DISPLACEMENT_MIN_ATR    = 0.70

SWING_PIVOT_BARS   = 5
BOS_LOOKBACK       = 50
EMA_BIAS_PERIOD    = 50
SESSION_LOOKBACK   = 48
EQUAL_LEVEL_TOLERANCE = 0.0003
SWEEP_WICK_MIN_PCT    = 0.50
SWEEP_CLOSEBACK_BARS  = 3
SWEEP_LOOKBACK_BARS   = 30
FVG_MAX_LOOKBACK      = 15
FVG_MIN_SIZE_PIPS     = 2.0

SMT_ENABLED  = True
SMT_LOOKBACK = 20
SMT_PAIRS: Dict[str,str] = {
    "EURUSDm":"GBPUSDm","GBPUSDm":"EURUSDm",
    "AUDUSDm":"NZDUSDm","NZDUSDm":"AUDUSDm",
}

RISK_PER_TRADE_PCT       = 1.0
RISK_MIN_PCT             = 0.25
RISK_MAX_PCT             = 1.0
DAILY_LOSS_CAP_PCT       = 3.0
WEEKLY_LOSS_CAP_PCT      = 6.0
MAX_OPEN_POSITIONS       = 4
MAX_CORRELATED_EXPOSURE  = 2
EQUITY_CURVE_LOOKBACK    = 20
VOLATILITY_ATR_KILL      = 4.0
CONSECUTIVE_LOSS_KILL    = 5
SPREAD_MAX_PIPS          = 3.0
SL_ATR_BUFFER            = 0.5
MIN_RR_RATIO             = 2.0
PARTIAL_CLOSE_RR         = 1.0
PARTIAL_CLOSE_PCT        = 50
TRAILING_STRUCTURE_BASED = True
MAGIC_NUMBER             = 99999

EQUITY_TIERS = [
    (10000,1.00),(5000,1.00),(2000,1.00),(1000,0.80),
    (500,0.60),(200,0.40),(100,0.25),(50,0.15),
    (20,0.10),(5,0.05),(0,0.025),
]
MICRO_ACCOUNT_THRESHOLD = 500

AI_MODE               = "xgboost"
AI_MIN_SCORE          = 52
AI_ROLE               = "filter"
AI_RETRAIN_INTERVAL   = 30
AI_SYNTHETIC_SAMPLES  = 600

BACKTEST_ENABLED    = False
SLIPPAGE_PIPS       = 0.5
COMMISSION_PER_LOT  = 3.5

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
Write-Host "[1/8] settings.py written!" -ForegroundColor Green

# ==============================================================================
# market_structure.py
# ==============================================================================
@'
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
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
        pools=self._pools(df)
        sess=self._session(df)
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

    def _classify(self,highs,lows):
        hh=hl=lh=ll=False
        if len(highs)>=2: hh=highs[-1].price>highs[-2].price; lh=highs[-1].price<highs[-2].price
        if len(lows)>=2:  hl=lows[-1].price>lows[-2].price;   ll=lows[-1].price<lows[-2].price
        return hh,hl,lh,ll

    def _events(self,df,highs,lows):
        events=[]
        if len(highs)<2 or len(lows)<2: return events
        close=df["close"].iloc[-1]; ph=highs[-2].price; pl=lows[-2].price
        pb=len(highs)>=3 and highs[-2].price>highs[-3].price
        if close>ph:
            k="BOS_UP" if pb else "CHOCH_UP"
            events.append(StructureEvent(k,ph,len(df)-1,min((close-ph)/(ph*0.001+1e-9),1.0)))
        if close<pl:
            k="BOS_DOWN" if not pb else "CHOCH_DOWN"
            events.append(StructureEvent(k,pl,len(df)-1,min((pl-close)/(pl*0.001+1e-9),1.0)))
        return events

    def _bias(self,hh,hl,lh,ll,events,ema_slope):
        bull=bear=0.0
        if hh: bull+=2; 
        if hl: bull+=1.5
        if lh: bear+=2
        if ll: bear+=1.5
        for e in events:
            if "UP" in e.kind: bull+=3 if "CHOCH" in e.kind else 2
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
                    p=(h[i]+h[j])/2; ex=next((x for x in pools if x.kind=="high_pool" and abs(x.price-p)/(p+1e-9)<tol),None)
                    if ex: ex.touches+=1; ex.strength=min(ex.touches/5,1.0)
                    else: pools.append(LiquidityPool(p,"high_pool"))
                if abs(l[i]-l[j])/(l[i]+1e-9)<tol:
                    p=(l[i]+l[j])/2; ex=next((x for x in pools if x.kind=="low_pool" and abs(x.price-p)/(p+1e-9)<tol),None)
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
Write-Host "[2/8] market_structure.py written!" -ForegroundColor Green

# ==============================================================================
# crt_engine.py (simplified for VPS paste)
# ==============================================================================
@'
import numpy as np
import pandas as pd
from dataclasses import dataclass,field
from typing import Optional,List,Tuple,Dict,Any
from datetime import datetime
from core.logger import get_logger
from config.settings import (CRT_SWEEP_THRESHOLD_PCT,CRT_SWEEP_MAX_CLOSE_PCT,
    CRT_CONFIRMATION_BODY_ATR,CRT_CONFIRMATION_CLOSE_PCT,DISPLACEMENT_ATR_MULT,
    DISPLACEMENT_CLOSE_PCT,DISPLACEMENT_VOL_MULT,FVG_MAX_LOOKBACK,FVG_MIN_SIZE_PIPS,
    MIN_RR_RATIO,SL_ATR_BUFFER,SWEEP_WICK_MIN_PCT,SWEEP_LOOKBACK_BARS,EQUAL_LEVEL_TOLERANCE)

log=get_logger("strategy.crt_engine")

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
        disp=self._displacement(df,sweep,direction,atr)
        if disp is None or not disp.is_valid: return None
        fvg=self._fvg(df,disp,direction,atr,pip)
        if fvg is None: return None
        return self._build(symbol,direction,df,sweep,disp,fvg,ms,killzone,atr,pip,point,zones)

    def _sweep(self,df,ms,direction,atr,pip):
        n=len(df)
        levels=[]
        if ms.prev_day_high: levels+=[(ms.prev_day_high,"PDH",1.0),(ms.prev_day_low,"PDL",1.0)]
        if ms.prev_week_high: levels+=[(ms.prev_week_high,"PWH",0.95),(ms.prev_week_low,"PWL",0.95)]
        for sl in ms.session_levels: levels.append((sl.price,sl.kind.upper(),0.85))
        for sh in ms.swing_highs[-5:]: levels.append((sh.price,"SwingH",0.80))
        for sl in ms.swing_lows[-5:]: levels.append((sl.price,"SwingL",0.80))
        for p in ms.pools: levels.append((p.price,"EQ"+("H" if "high" in p.kind else "L"),0.85*p.strength+0.3))
        if len(df)>=20:
            levels+=[(float(df["high"].tail(20).max()),"SessH20",0.75),
                     (float(df["low"].tail(20).min()), "SessL20",0.75)]
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
        c1=df.iloc[i-1]; c2=df.iloc[i]; c3_i=min(i+1,len(df)-1); c3=df.iloc[c3_i]
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

    def _displacement(self,df,sweep,direction,atr):
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
                if sz>=FVG_MIN_SIZE_PIPS and sz>bs: bs=sz; best=FairValueGap("BULLISH_FVG",c2["low"],c0["high"],(c2["low"]+c0["high"])/2,sz,i)
            elif direction=="SELL" and c2["high"]<c0["low"]:
                sz=(c0["low"]-c2["high"])/pip
                if sz>=FVG_MIN_SIZE_PIPS and sz>bs: bs=sz; best=FairValueGap("BEARISH_FVG",c0["low"],c2["high"],(c0["low"]+c2["high"])/2,sz,i)
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
            entry_price=round(entry,5),entry_top=round(fvg.top,5),entry_bottom=round(fvg.bottom,5),
            stop_loss=round(sl,5),sl_pips=round(risk/pip,1),
            take_profit_1=round(tp1,5),take_profit_2=round(tp2,5),take_profit_3=round(tp3,5),
            dol_target=round(dol,5) if dol else 0.0,rr_ratio=round(rr,2),confidence=round(score,1),
            displacement_str=round(disp.body_atr,2),fvg_size_pips=round(fvg.size_pips,1),
            sweep_strength=round(sweep.strength,2),killzone=kz,reason=" | ".join(reasons),
            sweep=sweep,displacement=disp,fvg=fvg,
            metadata={"atr":atr,"sweep_type":sweep.level_type,"disp_atr":disp.body_atr,
                      "fvg_pips":fvg.size_pips,"dol":dol or 0.0,"killzone":kz})

    def _score(self,sweep,disp,fvg,ms,kz,zones,entry,atr,pip):
        score=0.0; reasons=[]
        kzp={"silver_bullet":30,"ny_am":25,"london_open":20}
        score+=kzp.get(kz,10)
        reasons.append({"silver_bullet":"Silver Bullet","ny_am":"NY AM","london_open":"London","other":"Off-Hours"}.get(kz,kz))
        score+=sweep.strength*15+sweep.wick_pct*10; reasons.append(f"{sweep.level_type}({sweep.strength:.2f})")
        score+=min(disp.body_atr*10,15); reasons.append(f"Disp {disp.body_atr:.2f}xATR")
        score+=min(fvg.size_pips/3,10); reasons.append(f"FVG {fvg.size_pips:.1f}pips")
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
Write-Host "[3/8] crt_engine.py written!" -ForegroundColor Green

# ==============================================================================
# smt_divergence.py
# ==============================================================================
@'
import pandas as pd
from dataclasses import dataclass
from typing import Optional,Dict
from core.logger import get_logger
from config.settings import SMT_LOOKBACK,SMT_PAIRS

log=get_logger("strategy.smt")

@dataclass
class SMTResult:
    confirmed:bool; kind:str; strength:float; reason:str

class SMTEngine:
    def check(self,symbol,direction,candles):
        corr=SMT_PAIRS.get(symbol)
        if not corr or corr not in candles: return SMTResult(False,"NONE",0.0,"No pair")
        df_a=candles.get(symbol); df_b=candles.get(corr)
        if df_a is None or df_b is None or len(df_a)<SMT_LOOKBACK: return SMTResult(False,"NONE",0.0,"No data")
        lb=SMT_LOOKBACK
        ah=df_a["high"].tail(lb).max(); bh=df_b["high"].tail(lb).max()
        al=df_a["low"].tail(lb).min();  bl=df_b["low"].tail(lb).min()
        pah=df_a["high"].tail(lb*2).head(lb).max(); pbh=df_b["high"].tail(lb*2).head(lb).max()
        pal=df_a["low"].tail(lb*2).head(lb).min();  pbl=df_b["low"].tail(lb*2).head(lb).min()
        if direction=="SELL" and ah>pah and bh<=pbh:
            s=min(((ah-pah)/pah+(pbh-bh)/(pbh+1e-9))*10,1.0)
            return SMTResult(True,"BEARISH_SMT",s,f"SMT: {symbol} HH, {corr} failed HH")
        if direction=="BUY" and al<pal and bl>=pbl:
            s=min(((pal-al)/pal+(bl-pbl)/(pbl+1e-9))*10,1.0)
            return SMTResult(True,"BULLISH_SMT",s,f"SMT: {symbol} LL, {corr} failed LL")
        return SMTResult(False,"NONE",0.0,"No divergence")
'@ | Out-File -FilePath "C:\ForexBot\strategy\smt_divergence.py" -Encoding UTF8
Write-Host "[4/8] smt_divergence.py written!" -ForegroundColor Green

# ==============================================================================
# institutional_risk.py
# ==============================================================================
@'
import math
from datetime import date,datetime
from typing import List,Dict,Optional,Tuple
from dataclasses import dataclass,field
from core.logger import get_logger
from config.settings import (RISK_PER_TRADE_PCT,RISK_MIN_PCT,RISK_MAX_PCT,
    DAILY_LOSS_CAP_PCT,WEEKLY_LOSS_CAP_PCT,MAX_OPEN_POSITIONS,MAX_CORRELATED_EXPOSURE,
    EQUITY_CURVE_LOOKBACK,VOLATILITY_ATR_KILL,CONSECUTIVE_LOSS_KILL,
    SPREAD_MAX_PIPS,SL_ATR_BUFFER,EQUITY_TIERS,SLIPPAGE_PIPS)

log=get_logger("risk.institutional")

@dataclass
class RiskAssessment:
    allowed:bool; reason:str; lots:float; risk_pct:float; risk_usd:float
    kill_switch:bool=False; kill_reason:str=""; spread_ok:bool=True
    volatility_ok:bool=True; equity_curve_ok:bool=True

class InstitutionalRiskManager:
    def __init__(self):
        self._day_bal=0.0; self._week_bal=0.0
        self._day_date=None; self._week_date=None
        self._consec_loss=0; self._outcomes=[]; self._kill=False; self._kill_r=""

    def assess_trade(self,symbol,direction,entry,stop_loss,sl_pips,balance,equity,
                     open_positions,spread_pips=0.0,current_atr=0.0,normal_atr=0.0,symbol_info=None):
        self._update(balance)
        if self._kill: return RiskAssessment(False,f"Kill: {self._kill_r}",0,0,0,kill_switch=True)
        kill,kr=self._check_kill(balance,equity,spread_pips,current_atr,normal_atr)
        if kill: self._kill=True; self._kill_r=kr; return RiskAssessment(False,kr,0,0,0,kill_switch=True)
        dl=(self._day_bal-equity)/(self._day_bal+1e-9)*100
        if dl>=DAILY_LOSS_CAP_PCT: return RiskAssessment(False,f"Daily cap {dl:.1f}%",0,0,0)
        wl=(self._week_bal-equity)/(self._week_bal+1e-9)*100
        if wl>=WEEKLY_LOSS_CAP_PCT: return RiskAssessment(False,f"Weekly cap {wl:.1f}%",0,0,0)
        if len(open_positions)>=MAX_OPEN_POSITIONS: return RiskAssessment(False,"Max positions",0,0,0)
        buys=sum(1 for p in open_positions if p.get("type")=="BUY")
        sells=sum(1 for p in open_positions if p.get("type")=="SELL")
        if direction=="BUY" and buys>=MAX_CORRELATED_EXPOSURE: return RiskAssessment(False,"Max BUY",0,0,0)
        if direction=="SELL" and sells>=MAX_CORRELATED_EXPOSURE: return RiskAssessment(False,"Max SELL",0,0,0)
        ms=self._max_spread(symbol)
        if spread_pips>ms: return RiskAssessment(False,f"Spread {spread_pips:.1f}>{ms}",0,0,0,spread_ok=False)
        if equity<balance*0.15: return RiskAssessment(False,"Survival mode",0,0,0)
        rp=self._risk_pct(balance,current_atr,normal_atr)
        lots=self._lots(balance,rp,sl_pips,symbol_info or {})
        rusd=balance*rp/100
        log.info("[%s] Risk: lots=%.2f risk=%.2f%% spread=%.1f daily_dd=%.1f%%",symbol,lots,rp,spread_pips,dl)
        return RiskAssessment(True,"OK",lots,rp,rusd)

    def record_outcome(self,profit,outcome):
        self._outcomes.append(profit)
        if len(self._outcomes)>EQUITY_CURVE_LOOKBACK*2: self._outcomes.pop(0)
        if outcome=="SL": self._consec_loss+=1
        else: self._consec_loss=0
        if self._consec_loss>=CONSECUTIVE_LOSS_KILL:
            self._kill=True; self._kill_r=f"{self._consec_loss} consecutive losses"

    def reset_kill(self):
        if self._kill and "loss" in self._kill_r.lower():
            self._kill=False; self._kill_r=""; self._consec_loss=0

    def update_tracking(self,balance): self._update(balance)

    def _update(self,balance):
        today=date.today(); week=today.isocalendar()[1]
        if self._day_date!=today: self._day_bal=balance; self._day_date=today; self.reset_kill()
        if self._week_date!=week: self._week_bal=balance; self._week_date=week

    def _check_kill(self,balance,equity,spread,atr,n_atr):
        if n_atr>0 and atr>n_atr*VOLATILITY_ATR_KILL: return True,f"Volatility spike {atr:.5f}"
        if self._consec_loss>=CONSECUTIVE_LOSS_KILL: return True,f"{self._consec_loss} consec losses"
        return False,""

    def _risk_pct(self,balance,atr,n_atr):
        base=RISK_PER_TRADE_PCT
        for t,m in EQUITY_TIERS:
            if balance>=t: base=RISK_PER_TRADE_PCT*m; break
        if not self._equity_ok(): base*=0.5
        if n_atr>0 and atr>0: base*=min(max(n_atr/(atr+1e-9),0.25),1.5)
        return max(RISK_MIN_PCT,min(RISK_MAX_PCT,round(base,3)))

    def _lots(self,balance,rp,sl_pips,si):
        if sl_pips<=0 or balance<=0: return si.get("volume_min",0.01)
        ra=balance*rp/100; cs=si.get("trade_contract_size",100000)
        pt=si.get("point",0.0001); ps=si.get("pip_size",pt*10); pv=ps*cs
        lots=ra/(sl_pips*pv+1e-9)
        vs=si.get("volume_step",0.01); vn=si.get("volume_min",0.01); vx=si.get("volume_max",100.0)
        return round(max(vn,min(vx,math.floor(lots/vs)*vs)),2)

    def _equity_ok(self):
        if len(self._outcomes)<EQUITY_CURVE_LOOKBACK: return True
        r=self._outcomes[-EQUITY_CURVE_LOOKBACK:]; t=sum(r)
        return t>-abs(sum(abs(x) for x in r))*0.5

    @staticmethod
    def _max_spread(symbol):
        s=symbol.replace("m","").upper()
        if "BTC" in s or "ETH" in s: return 50.0
        if "XAU" in s: return 8.0
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
Write-Host "[5/8] institutional_risk.py written!" -ForegroundColor Green

# ==============================================================================
# master_scanner.py
# ==============================================================================
@'
from typing import Optional,Dict,List
import pandas as pd
from datetime import datetime
from core.logger import get_logger
from config.settings import (HTF_BIAS_TIMEFRAMES,EXECUTION_TIMEFRAMES,CANDLES_REQUIRED,
    AI_MIN_SCORE,KILLZONES_UTC,KILLZONES_DST,ALWAYS_ON_SYMBOLS,SMT_DIVERGENCE_ENABLED,
    NEWS_FILTER_ENABLED,SPREAD_FILTER_ENABLED,CORRELATION_CHECK_ENABLED)
from strategy.market_structure import MarketStructureEngine,MarketStructureResult
from strategy.crt_engine import CRTEngine,CRTSignal
from strategy.supply_demand import SupplyDemandEngine
from strategy.smt_divergence import SMTEngine

log=get_logger("core.master_scanner")
MAX_SAME_DIR=2
AI_BY_KZ={"silver_bullet":47,"ny_am":50,"london_open":52,"other":55}

def _is_dst(): return 3<=datetime.utcnow().month<=11
def get_killzone():
    h=datetime.utcnow().hour; kz=KILLZONES_DST if _is_dst() else KILLZONES_UTC
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
            ms=self._max_spread(symbol)
            if sp>ms: log.debug("[%s] Spread %.1f>%.1f",symbol,sp,ms); return None
        else: sp=0.0
        mr={}; dfd=self._mt5.get_candles(symbol,"D1",CANDLES_REQUIRED); dfw=self._mt5.get_candles(symbol,"W1",CANDLES_REQUIRED)
        for tf in HTF_BIAS_TIMEFRAMES:
            df=self._mt5.get_candles(symbol,tf,CANDLES_REQUIRED)
            if df is not None and len(df)>=20: mr[tf]=self._ms.analyze(df,symbol,tf,dfd,dfw)
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
                for s2 in [symbol]+list({v for k,v in __import__("config.settings",fromlist=["SMT_PAIRS"]).SMT_PAIRS.items() if k==symbol}):
                    df=self._mt5.get_candles(s2,"H1",50)
                    if df is not None: cm[s2]=df
                smt=self._smt.check(symbol,"BUY" if bias=="bullish" else "SELL",cm)
                if smt.confirmed: smt_bonus=smt.strength*10; log.debug("[%s] SMT: %s",symbol,smt.kind)
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
                   "zone_strength":sig.metadata.get("zone_strength",0.0),
                   "zone_retests":sig.metadata.get("zone_retests",2),
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
                     symbol,etf,sig.direction,ai,kz,sig.sweep.kind if sig.sweep else "?",
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
Write-Host "[6/8] master_scanner.py written!" -ForegroundColor Green

# ==============================================================================
# main.py — Uses MasterScanner + InstitutionalRiskManager
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
        log.info("  Strategy: CRT + Romeo ICT + SMT + Full Risk Mgmt")
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
            self.notifier.startup_v2(acct["balance"],acct["login"],len(settings.SYMBOLS),acct["balance"]<500)
        threading.Thread(target=self._heartbeat,daemon=True).start()
        log.info("Bot live. Scanning %d pairs every %ds",len(settings.SYMBOLS),settings.MAIN_LOOP_INTERVAL_SEC)
        self._loop()

    def _heartbeat(self):
        time.sleep(10800)
        while _RUNNING:
            try:
                acct=self.mt5.get_account_info()
                if acct:
                    op=self.mt5.get_open_positions(); kz=get_killzone()
                    self.notifier.heartbeat(acct["balance"],acct["equity"],len(op),len(settings.SYMBOLS))
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
                if self.mt5.connect(): self.notifier.mt5_connected(settings.MT5_SERVER); break
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
Write-Host "[7/8] main.py written - using MasterScanner + InstitutionalRisk!" -ForegroundColor Green

# ==============================================================================
# Notifier V4
# ==============================================================================
@'
import threading,time,requests
from datetime import datetime
from core.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID

log=get_logger("telegram.notifier")
API_URL=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
KZ={"silver_bullet":"🥈⚡ SILVER BULLET","ny_am":"🗽 NY AM SESSION","london_open":"🇬🇧 LONDON OPEN","other":"🕐 OFF-HOURS"}

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
            f"📐 Strategy: CRT + Romeo ICT\n"
            f"⚙️  Engine:   Systematic / Zero Discretion\n\n"
            f"⏰ Kill Zones (EST):\n"
            f"   🇬🇧 London:  02:00-05:00\n"
            f"   🗽 NY AM:    08:30-11:00\n"
            f"   🥈 Silver:   10:00-11:00 ← Priority\n\n"
            f"✅ CRT 3-Candle: Systematic\n"
            f"✅ Sweep: Wick ≥50% + Close-back\n"
            f"✅ Displacement: Range >1.5x ATR\n"
            f"✅ FVG Entry: 50% equilibrium\n"
            f"✅ SL: Beyond sweep extreme\n"
            f"✅ Target: 2R/3R/DOL\n"
            f"✅ SMT Divergence: ON\n"
            f"✅ Spread Filter: ON\n"
            f"✅ Daily Cap: {3}% | Weekly: {6}%\n"
            f"✅ Kill Switch: {5} consec losses\n"
            f"❤️  Heartbeat: Every 3 hours\n\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def startup(self,b,a): self.startup_v2(b,a,30,b<500)

    def heartbeat(self,balance,equity,open_trades,pairs):
        pnl=equity-balance; ei="📈" if pnl>=0 else "📉"
        bars="█"*open_trades+"░"*(5-min(open_trades,5))
        bl="🔴" if balance<20 else ("🟡" if balance<100 else "🟢")
        self._send(
            f"💓 HEARTBEAT  ·  BOT ALIVE\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"💰 Balance: ${balance:,.2f} {bl}\n"
            f"⚖️  Equity:  ${equity:,.2f}\n"
            f"{ei} Float:  ${pnl:+.4f}\n"
            f"📂 Trades: [{bars}] {open_trades}/4\n"
            f"🌐 Pairs:  {pairs} scanning\n"
            f"⏳ Next:   3 hours\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def new_trade_v3(self,s):
        d=s.get("direction","BUY"); sym=s.get("symbol","")
        ai=s.get("ai_score",0); kz=s.get("killzone","other")
        addon=s.get("is_addon",False)
        di="🟢 BUY  ▲ LONG" if d=="BUY" else "🔴 SELL ▼ SHORT"
        arrow="📈" if d=="BUY" else "📉"
        kzl=KZ.get(kz,"🕐")
        tags=[]
        if "XAU" in sym: tags.append("🥇 GOLD")
        if "BTC" in sym: tags.append("₿ CRYPTO")
        if "ETH" in sym: tags.append("⟠ ETH")
        if addon: tags.append("➕ ADD-ON")
        if ai>=85: tags.append("🔥 PREMIUM")
        elif ai>=70: tags.append("⭐ HIGH")
        tl="  ".join(tags)
        ab="█"*int(min(ai,100)/10)+"░"*(10-int(min(ai,100)/10))
        dol=s.get("dol_target",0); dl=f"🎯 DOL:     {dol:.5f}\n" if dol else ""
        disp=s.get("displacement",0); fvg=s.get("fvg_size_pips",0)
        self._send(
            f"{arrow} {'ADD-ON' if addon else 'CRT SIGNAL'}\n"
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
        self._send(f"✅ TP{tp_level} HIT {'⭐'*tp_level}\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n💰 ${profit:+.4f}\n🔒 SL → Break-Even\n🏃 Running to TP{tp_level+1}...")

    def trade_closed(self,ticket,symbol,profit,pips):
        r="PROFIT 💰" if profit>0 else "LOSS"
        self._send(f"{'✅' if profit>0 else '❌'} CLOSED — {r}\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n💵 ${profit:+.4f}\n📏 {pips:+.1f} pips\n🕐 {datetime.utcnow().strftime('%H:%M')} UTC")

    def trade_closed_be(self,ticket,symbol,pips):
        self._send(f"🔰 BREAKEVEN\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n🛡️ Capital protected\n📏 {pips:+.1f} pips")

    def sl_hit(self,ticket,symbol,loss):
        self._send(f"❌ STOP LOSS\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n💸 ${loss:+.4f}\n📌 SL did its job\n🔄 Next setup...")

    def bad_trade_closed(self,ticket,symbol,profit,r):
        self._send(f"⚠️ BAD TRADE CLOSED\n━━━━━━━━━━━━━━━━\n💱 {symbol}\n🎫 #{ticket}\n📉 {r:.2f}R\n💸 ${profit:+.4f}\n🛡️ Capital preserved")

    def drawdown_warning(self,balance,equity,loss_pct):
        self._send(f"⚠️ DAILY LIMIT HIT\n━━━━━━━━━━━━━━━━\n📉 {loss_pct:.1f}% daily loss\n💰 ${balance:,.2f}\n⚖️ ${equity:,.2f}\n🔒 No new trades today\n🔄 Resumes tomorrow")

    def drawdown_recovered(self,balance,equity):
        self._send(f"✅ TRADING RESUMED\n━━━━━━━━━━━━━━━━\n💰 ${balance:,.2f}\n⚖️ ${equity:,.2f}\n🚀 Hunting setups!")

    def account_empty(self): self._send("🚨 ACCOUNT EMPTY\n━━━━━━━━━━━━━━━━\n⛔ Trading halted\n💡 Please deposit")
    def account_low(self,bal): self._send(f"⚠️ BALANCE LOW\n━━━━━━━━━━━━━━━━\n💰 ${bal:.2f}\n⛔ Below minimum\n💡 Top up account")

    def daily_summary(self,s):
        wins=s.get("wins",0); losses=s.get("losses",0); total=s.get("total_trades",0)
        pnl=s.get("net_pnl",0); bal=s.get("balance",0)
        wb=("🟢"*wins+"🔴"*losses) if total>0 else "⬜ No trades"
        pi="📈" if pnl>=0 else "📉"
        self._send(f"📅 DAILY SUMMARY\n━━━━━━━━━━━━━━━━\n📆 {s.get('date','')}\n{wb}\n🎯 {total} trades\n✅ {wins}  ❌ {losses}\n📊 WR: {s.get('win_rate',0):.1f}%\n{pi} ${pnl:+.4f}\n💰 ${bal:,.2f}")

    def weekly_summary(self,s):
        pnl=s.get("net_pnl",0); pi="📈" if pnl>=0 else "📉"
        self._send(f"🗓️ WEEKLY\n━━━━━━━━━━━━━━━━\n📊 WR: {s.get('win_rate',0):.1f}%\n{pi} ${pnl:+.4f}")

    def ai_retrained(self,s,a):
        b="█"*int(a/10)+"░"*(10-int(a/10))
        self._send(f"🤖 AI RETRAINED\n━━━━━━━━━━━━━━━━\n📚 {s} samples\n🎯 [{b}] {a:.1f}%")

    def mt5_connected(self,s): self._send(f"🔌 MT5 RECONNECTED\n━━━━━━━━━━━━━━━━\n🖥️ {s}\n🕐 {datetime.utcnow().strftime('%H:%M')} UTC")
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
Write-Host "[8/8] notifier.py written - V4 style!" -ForegroundColor Green

# ==============================================================================
# START
# ==============================================================================
Write-Host ""
Write-Host "Starting Institutional CRT Bot V4..." -ForegroundColor Cyan
Start-Process -FilePath "C:\Program Files\Python311\python.exe" -ArgumentList "C:\ForexBot\main.py" -WorkingDirectory "C:\ForexBot" -WindowStyle Normal
Start-Sleep -Seconds 25
Get-Content "C:\ForexBot\logs\main.log" -Tail 15
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  INSTITUTIONAL CRT BOT V4 - LIVE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "What's New in V4:" -ForegroundColor Cyan
Write-Host "  Systematic CRT 3-Candle Model (parameterized)" -ForegroundColor White
Write-Host "  Liquidity sweep: wick>=50% + close-back rule" -ForegroundColor White
Write-Host "  Displacement: range>1.5xATR + close in 20%" -ForegroundColor White
Write-Host "  FVG entry at 50% (equilibrium)" -ForegroundColor White
Write-Host "  SL beyond sweep extreme + ATR buffer" -ForegroundColor White
Write-Host "  Targets: 2R / 3R / Draw on Liquidity" -ForegroundColor White
Write-Host "  SMT Divergence: correlated pair confirmation" -ForegroundColor White
Write-Host "  Market Structure: N-bar fractal pivot" -ForegroundColor White
Write-Host "  Session levels: Asia/London/NY H&L" -ForegroundColor White
Write-Host "  Institutional Risk: kill switch, equity curve" -ForegroundColor White
Write-Host "  Daily cap: 3% | Weekly cap: 6%" -ForegroundColor White
Write-Host "  Kill after: 5 consecutive losses" -ForegroundColor White
Write-Host "  Spread filter: symbol-specific" -ForegroundColor White
Write-Host "  Zero discretion - all rules quantified" -ForegroundColor White
