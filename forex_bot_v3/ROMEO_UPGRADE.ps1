# ==============================================================================
# ROMEO ICT STRATEGY UPGRADE
# Paste this ENTIRE script on your VPS PowerShell and run it
# ==============================================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ROMEO ICT STRATEGY UPGRADE" -ForegroundColor Cyan
Write-Host "  Stop Hunt -> MSS -> FVG Entry" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Write-Host "Bot stopped." -ForegroundColor Yellow

# ==============================================================================
# FILE 1: Romeo ICT Strategy Engine
# ==============================================================================
$romeo_strategy = @'
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from core.logger import get_logger
from config.settings import MIN_RR_RATIO

log = get_logger("strategy.romeo_ict")

KILLZONES_UTC = {"london_open":(7,10),"ny_am":(13,16),"silver_bullet":(15,16)}
KILLZONES_DST = {"london_open":(6,9), "ny_am":(12,15),"silver_bullet":(14,15)}
DISPLACEMENT_MIN_ATR = 0.7
FVG_MAX_LOOKBACK = 12
SL_BUFFER = {"DEFAULT":3,"JPY":5,"XAU":50,"XAG":20,"BTC":200,"ETH":80}

def _pip(symbol, point):
    s=symbol.replace("m","").upper()
    if "JPY" in s or "XAU" in s or "XAG" in s: return point*100
    if "BTC" in s or "ETH" in s: return point*10
    return point*10

def _buf(symbol, point):
    s=symbol.replace("m","").upper(); pip=_pip(symbol,point)
    if "JPY" in s: return SL_BUFFER["JPY"]*pip
    if "XAU" in s: return SL_BUFFER["XAU"]*pip
    if "XAG" in s: return SL_BUFFER["XAG"]*pip
    if "BTC" in s: return SL_BUFFER["BTC"]*pip
    if "ETH" in s: return SL_BUFFER["ETH"]*pip
    return SL_BUFFER["DEFAULT"]*pip

def _is_dst(): return 3<=datetime.utcnow().month<=11

def get_killzone():
    h=datetime.utcnow().hour
    kz=KILLZONES_DST if _is_dst() else KILLZONES_UTC
    for name,(s,e) in kz.items():
        if s<=h<e: return name
    return None

def is_in_killzone(): return get_killzone() is not None

@dataclass
class FVG:
    kind:str; top:float; bottom:float; bar_index:int; size_pips:float
    @property
    def mid(self): return (self.top+self.bottom)/2

@dataclass
class Sweep:
    kind:str; level:float; sweep_high:float; sweep_low:float
    bar_index:int; strength:float

@dataclass
class MSS:
    direction:str; break_price:float; displacement:float
    bar_index:int; energetic:bool

@dataclass
class RomeoSignal:
    symbol:str; direction:str; entry_price:float; stop_loss:float
    take_profit_1:float; take_profit_2:float; take_profit_3:float
    rr_ratio:float; confidence:float; ai_score:float=0.0
    timeframe:str=""; signal_time:datetime=field(default_factory=datetime.utcnow)
    reason:str=""; zone:object=None; fvg:object=None
    sweep:object=None; mss:object=None; killzone:str=""
    dol_target:float=0.0; metadata:Dict[str,Any]=field(default_factory=dict)

    def to_dict(self):
        return {"symbol":self.symbol,"direction":self.direction,
                "entry_price":self.entry_price,"stop_loss":self.stop_loss,
                "take_profit_1":self.take_profit_1,"take_profit_2":self.take_profit_2,
                "rr_ratio":self.rr_ratio,"confidence":self.confidence,
                "ai_score":self.ai_score,"timeframe":self.timeframe,
                "signal_time":str(self.signal_time),"reason":self.reason}


class RomeoICTStrategy:

    def generate_signal(self,symbol,higher_tf_bias,higher_tf_strength,
                        current_price,point,df_htf,df_entry,entry_tf,zones=None):
        if higher_tf_bias=="neutral" or higher_tf_strength<0.35: return None
        if df_entry is None or len(df_entry)<30: return None
        killzone=get_killzone()
        if killzone is None and symbol.replace("m","").upper() not in ["XAUUSD","BTCUSD","ETHUSD","XAGUSD"]:
            return None
        atr=float((df_entry["high"]-df_entry["low"]).tail(14).mean())
        if atr==0: return None
        pip=_pip(symbol,point)
        direction="BUY" if higher_tf_bias=="bullish" else "SELL"
        sweep=self._sweep(df_htf,df_entry,atr,symbol)
        if sweep is None: return None
        if higher_tf_bias=="bullish" and sweep.kind!="LOW_SWEPT": return None
        if higher_tf_bias=="bearish" and sweep.kind!="HIGH_SWEPT": return None
        mss=self._mss(df_entry,direction,sweep,atr)
        if mss is None or not mss.energetic: return None
        fvg=self._fvg(df_entry,direction,mss,atr,pip)
        if fvg is None: return None
        return self._build(symbol,direction,current_price,fvg,sweep,mss,
                           higher_tf_strength,killzone or "other",atr,pip,
                           point,entry_tf,zones,df_htf)

    def _sweep(self,df_htf,df_entry,atr,symbol):
        df=df_entry; n=len(df)
        if n<20: return None
        levels=[]
        if df_htf is not None and len(df_htf)>=5:
            levels+=[(df_htf["high"].iloc[-2],0.9,"PDH"),
                     (df_htf["low"].iloc[-2], 0.9,"PDL"),
                     (df_htf["high"].tail(10).max(),0.8,"SwH"),
                     (df_htf["low"].tail(10).min(), 0.8,"SwL")]
        if len(df)>=20:
            levels+=[(df["high"].tail(20).max(),0.7,"SessH"),
                     (df["low"].tail(20).min(), 0.7,"SessL")]
        for i in range(n-10,n-1):
            bar=df.iloc[i]
            for lp,ls,lt in levels:
                if bar["high"]>lp and bar["close"]<lp:
                    return Sweep("HIGH_SWEPT",lp,bar["high"],bar["low"],i,ls)
                if bar["low"]<lp and bar["close"]>lp:
                    return Sweep("LOW_SWEPT",lp,bar["high"],bar["low"],i,ls)
        return None

    def _mss(self,df,direction,sweep,atr):
        n=len(df); start=max(sweep.bar_index+1,0); end=min(start+FVG_MAX_LOOKBACK,n)
        if start>=n: return None
        for i in range(start,end):
            bar=df.iloc[i]
            if direction=="BUY":
                body=bar["close"]-bar["open"]
                if body<=0: continue
                lh=df["high"].iloc[max(0,sweep.bar_index-5):sweep.bar_index].max() if sweep.bar_index>0 else bar["high"]
                if bar["close"]>lh:
                    d=body/(atr+1e-9)
                    return MSS("BULLISH",lh,d,i,d>=DISPLACEMENT_MIN_ATR)
            else:
                body=bar["open"]-bar["close"]
                if body<=0: continue
                ll=df["low"].iloc[max(0,sweep.bar_index-5):sweep.bar_index].min() if sweep.bar_index>0 else bar["low"]
                if bar["close"]<ll:
                    d=body/(atr+1e-9)
                    return MSS("BEARISH",ll,d,i,d>=DISPLACEMENT_MIN_ATR)
        return None

    def _fvg(self,df,direction,mss,atr,pip):
        n=len(df); start=max(mss.bar_index-2,0); end=min(mss.bar_index+FVG_MAX_LOOKBACK,n)
        best=None; best_sz=0
        for i in range(start+2,end):
            c0=df.iloc[i-2]; c2=df.iloc[i]
            if direction=="BUY" and c2["low"]>c0["high"]:
                sz=(c2["low"]-c0["high"])/pip
                if sz>best_sz: best_sz=sz; best=FVG("bullish",c2["low"],c0["high"],i,sz)
            elif direction=="SELL" and c2["high"]<c0["low"]:
                sz=(c0["low"]-c2["high"])/pip
                if sz>best_sz: best_sz=sz; best=FVG("bearish",c0["low"],c2["high"],i,sz)
        return best

    def _build(self,symbol,direction,cur,fvg,sweep,mss,htf_str,kz,atr,pip,point,tf,zones,df_htf):
        entry=fvg.mid; buf=_buf(symbol,point)
        sl=sweep.sweep_low-buf if direction=="BUY" else sweep.sweep_high+buf
        risk=abs(entry-sl)
        if risk<=0 or risk>cur*0.1: return None
        tp1=entry+risk*2 if direction=="BUY" else entry-risk*2
        tp2=entry+risk*3 if direction=="BUY" else entry-risk*3
        tp3=entry+risk*5 if direction=="BUY" else entry-risk*5
        rr=abs(tp1-entry)/risk
        if rr<MIN_RR_RATIO: return None
        dol=float(df_htf["high"].tail(20).max() if direction=="BUY" else df_htf["low"].tail(20).min()) if df_htf is not None else 0.0
        score=0.0; reasons=[]
        kz_pts={"silver_bullet":30,"ny_am":25,"london_open":20}
        score+=kz_pts.get(kz,15); reasons.append(kz.replace("_"," ").title())
        score+=sweep.strength*20; reasons.append(f"{sweep.kind.replace('_',' ')}")
        if mss.energetic: score+=15; reasons.append(f"Displacement {mss.displacement:.1f}xATR")
        score+=min(fvg.size_pips/5,10); reasons.append(f"FVG {fvg.size_pips:.1f}pips")
        score+=htf_str*10
        best_zone=None
        if zones:
            ztype="demand" if direction=="BUY" else "supply"
            nb=[z for z in zones if z.kind==ztype and abs(z.mid-entry)<atr*3]
            if nb: best_zone=max(nb,key=lambda z:z.strength); score+=min(best_zone.strength,10); reasons.append(f"SD({best_zone.origin_tf})")
        score=min(score,100.0)
        log.info("[%s %s] %s: score=%.1f kz=%s sweep=%s disp=%.2f fvg=%.1fpips",
                 symbol,tf,direction,score,kz,sweep.kind,mss.displacement,fvg.size_pips)
        return RomeoSignal(
            symbol=symbol,direction=direction,
            entry_price=round(entry,5),stop_loss=round(sl,5),
            take_profit_1=round(tp1,5),take_profit_2=round(tp2,5),
            take_profit_3=round(tp3,5),rr_ratio=round(rr,2),
            confidence=round(score,1),timeframe=tf,
            reason=" | ".join(reasons),zone=best_zone,
            fvg=fvg,sweep=sweep,mss=mss,killzone=kz,dol_target=round(dol,5),
            metadata={"htf_strength":htf_str,"displacement":mss.displacement,
                      "fvg_size_pips":fvg.size_pips,"sweep_level":sweep.level,
                      "killzone":kz,"dol_target":dol})
'@
$romeo_strategy | Out-File -FilePath "C:\ForexBot\strategy\romeo_ict_strategy.py" -Encoding UTF8
Write-Host "[1/5] romeo_ict_strategy.py written!" -ForegroundColor Green

# ==============================================================================
# FILE 2: Romeo Scanner
# ==============================================================================
$romeo_scanner = @'
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime
from core.logger import get_logger
from config.settings import (CANDLES_REQUIRED,AI_MIN_SCORE,
    REGIME_ENGINE_ENABLED,NEWS_FILTER_ENABLED,CORRELATION_CHECK_ENABLED)
from market_structure.analyzer import MarketStructureAnalyzer
from strategy.supply_demand import SupplyDemandEngine
from strategy.romeo_ict_strategy import RomeoICTStrategy,get_killzone,is_in_killzone

log = get_logger("core.romeo_scanner")
MAX_SAME_DIR  = 2
ALWAYS_ON     = ["BTCUSDm","ETHUSDm","XAUUSDm","XAGUSDm"]
AI_BY_KZ      = {"silver_bullet":48,"ny_am":50,"london_open":52,"other":54}

class RomeoScanner:
    def __init__(self,mt5,ai):
        self._mt5=mt5; self._ai=ai
        self._ms=MarketStructureAnalyzer(); self._sd=SupplyDemandEngine()
        self._romeo=RomeoICTStrategy()
        self._regime=None; self._news=None; self._corr=None
        if REGIME_ENGINE_ENABLED:
            try:
                from core.regime_engine import RegimeEngine
                self._regime=RegimeEngine()
            except: pass
        if NEWS_FILTER_ENABLED:
            try:
                from core.news_filter import NewsFilter
                self._news=NewsFilter()
            except: pass
        if CORRELATION_CHECK_ENABLED:
            try:
                from core.correlation_engine import CorrelationEngine
                self._corr=CorrelationEngine()
            except: pass

    def scan(self,symbol,open_positions=None):
        open_positions=open_positions or []
        kz=get_killzone()
        always=symbol in ALWAYS_ON
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
        br={}
        for tf in ["D1","H4","H1"]:
            df=self._mt5.get_candles(symbol,tf,CANDLES_REQUIRED)
            if df is not None and len(df)>=20:
                br[tf]=self._ms.analyze(df,symbol,tf)
        bias,strength=self._agg_bias(br)
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
        df_h4=self._mt5.get_candles(symbol,"H4",CANDLES_REQUIRED)
        df_h1=self._mt5.get_candles(symbol,"H1",CANDLES_REQUIRED)
        df_htf=df_h4 if df_h4 is not None else df_h1
        zones=[]
        for ztf in ["D1","H4","H1"]:
            dfz=self._mt5.get_candles(symbol,ztf,CANDLES_REQUIRED)
            if dfz is not None:
                try: zones.extend(self._sd.detect_zones(dfz,timeframe=ztf,point=point))
                except: pass
        entry_tfs=["M5","M15","M30"] if not always else ["M5","M15","M30","H1"]
        for etf in entry_tfs:
            df_e=self._mt5.get_candles(symbol,etf,CANDLES_REQUIRED)
            if df_e is None or len(df_e)<30: continue
            try:
                sig=self._romeo.generate_signal(
                    symbol=symbol,higher_tf_bias=bias,higher_tf_strength=strength,
                    current_price=cur,point=point,df_htf=df_htf,
                    df_entry=df_e,entry_tf=etf,zones=zones)
            except Exception as e:
                log.error("[%s %s] Romeo error: %s",symbol,etf,e); continue
            if sig is None: continue
            atr=float((df_e["high"]-df_e["low"]).tail(14).mean())
            feats={"htf_bias_score":1.0 if bias=="bullish" else -1.0,
                   "htf_strength":strength,"structure_strength":0.8,
                   "entry_tf_bias":1.0,
                   "zone_strength":sig.zone.strength if sig.zone else 0.0,
                   "zone_retests":sig.zone.retests if sig.zone else 2,
                   "ssl_swept":sig.sweep.kind=="LOW_SWEPT",
                   "bsl_swept":sig.sweep.kind=="HIGH_SWEPT",
                   "of_score":65.0,"sweep_score":sig.sweep.strength,
                   "rr_ratio":sig.rr_ratio,
                   "session_encoded":{"london_open":1,"ny_am":2,"silver_bullet":3,"other":0}.get(kz or "other",0),
                   "volatility_norm":min(atr/(cur+1e-9)*100,1.0),
                   "confidence_raw":sig.confidence,
                   "zone_freshness":sig.zone.fresh if sig.zone else True}
            ai=self._ai.score_signal(feats)
            sig.ai_score=ai
            sig.metadata["features"]=feats
            sig.metadata["regime"]="TRENDING_UP" if bias=="bullish" else "TRENDING_DOWN"
            sig.metadata["session"]=kz or "other"
            threshold=AI_BY_KZ.get(kz or "other",AI_MIN_SCORE)
            if always: threshold-=3
            if ai<threshold:
                log.debug("[%s %s] AI=%.1f < %d",symbol,etf,ai,threshold); continue
            log.info("[%s %s] ROMEO APPROVED: %s AI=%.1f KZ=%s Sweep=%s Disp=%.2f FVG=%.1fpips",
                     symbol,etf,sig.direction,ai,kz,sig.sweep.kind,
                     sig.mss.displacement,sig.fvg.size_pips)
            return sig
        return None

    @staticmethod
    def _agg_bias(br):
        s={"bullish":0.0,"bearish":0.0}; w={"D1":4,"H4":3,"H1":2}
        for tf,res in br.items():
            wt=w.get(tf,1)
            if res.bias in s: s[res.bias]+=wt*res.strength
        b=s["bullish"]; be=s["bearish"]; t=b+be+1e-9
        if b>be and b/t>0.55: return "bullish",round(b/t,3)
        if be>b and be/t>0.55: return "bearish",round(be/t,3)
        return "neutral",0.0
'@
$romeo_scanner | Out-File -FilePath "C:\ForexBot\core\romeo_scanner.py" -Encoding UTF8
Write-Host "[2/5] romeo_scanner.py written!" -ForegroundColor Green

# ==============================================================================
# FILE 3: Updated Notifier (Romeo-style messages)
# ==============================================================================
$notifier = @'
import threading, time, requests
from datetime import datetime
from core.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = get_logger("telegram.notifier")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

KZ_EMOJI={"silver_bullet":"🥈⚡ SILVER BULLET","ny_am":"🗽 NY AM SESSION",
           "london_open":"🇬🇧 LONDON OPEN","other":"🕐 OFF-HOURS"}

class TelegramNotifier:
    def __init__(self):
        self._enabled=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN!="YOUR_BOT_TOKEN")
        log.info("Telegram %s","ENABLED" if self._enabled else "DISABLED")

    def startup_v2(self,balance,account,pairs,is_micro):
        tier="🔬 MICRO" if is_micro else "💼 STANDARD"
        self._send(
            f"╔══════════════════════════╗\n"
            f"║  🤖  ROMEO ICT BOT LIVE   ║\n"
            f"╚══════════════════════════╝\n\n"
            f"🏦 Account:  {account}\n"
            f"💰 Balance:  ${balance:,.2f}\n"
            f"📊 Mode:     {tier}\n"
            f"🎯 Pairs:    {pairs} symbols\n\n"
            f"📐 Strategy: ICT 2022 Model\n"
            f"⏰ Killzones:\n"
            f"   🇬🇧 London: 02-05 EST\n"
            f"   🗽 NY AM:   08:30-11 EST\n"
            f"   🥈 Silver:  10-11 EST\n\n"
            f"✅ Stop Hunt → MSS → FVG\n"
            f"✅ S&D = Confluence only\n"
            f"✅ Displacement filter ON\n"
            f"✅ DOL targeting ON\n"
            f"❤️  Heartbeat: Every 3hrs\n\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def startup(self,b,a): self.startup_v2(b,a,30,b<500)

    def heartbeat(self,balance,equity,open_trades,pairs):
        pnl=equity-balance; ei="📈" if pnl>=0 else "📉"
        bars="█"*open_trades+"░"*(5-min(open_trades,5))
        bl="🔴 LOW" if balance<20 else ("🟡" if balance<100 else "🟢")
        self._send(
            f"💓 HEARTBEAT  ·  BOT ALIVE\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"💰 Balance: ${balance:,.2f} {bl}\n"
            f"⚖️  Equity:  ${equity:,.2f}\n"
            f"{ei} Float:  ${pnl:+.4f}\n"
            f"📂 Trades: [{bars}] {open_trades}/5\n"
            f"🌐 Pairs:  {pairs} scanning\n"
            f"⏳ Next:   3 hours\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def new_trade_v3(self,s):
        d=s.get("direction","BUY"); sym=s.get("symbol","")
        ai=s.get("ai_score",0); kz=s.get("killzone","other")
        addon=s.get("is_addon",False)
        dir_icon="🟢 BUY  ▲ LONG" if d=="BUY" else "🔴 SELL ▼ SHORT"
        arrow="📈" if d=="BUY" else "📉"
        kz_label=KZ_EMOJI.get(kz,"🕐")
        tags=[]
        if "XAU" in sym: tags.append("🥇 GOLD")
        if "BTC" in sym: tags.append("₿ CRYPTO")
        if "ETH" in sym: tags.append("⟠ ETH")
        if addon: tags.append("➕ ADD-ON")
        if ai>=85: tags.append("🔥 PREMIUM")
        elif ai>=70: tags.append("⭐ HIGH CONF")
        tag_line="  ".join(tags) if tags else ""
        ai_bar="█"*int(min(ai,100)/10)+"░"*(10-int(min(ai,100)/10))
        reason=s.get("reason","")
        dol=s.get("dol_target",0)
        dol_line=f"🎯 DOL:     {dol:.5f}\n" if dol else ""
        fvg_size=s.get("fvg_size_pips",0)
        disp=s.get("displacement",0)
        self._send(
            f"{arrow} {'ADD-ON TRADE' if addon else 'ROMEO SIGNAL'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{kz_label}\n"
            f"{tag_line}\n\n"
            f"💱 {sym}  ·  {dir_icon}\n\n"
            f"🎯 Entry:   {s.get('entry_price',0):.5f}\n"
            f"🛑 SL:      {s.get('stop_loss',0):.5f}\n"
            f"🎁 TP1(2R): {s.get('take_profit_1',0):.5f}\n"
            f"🏆 TP2(3R): {s.get('take_profit_2',0):.5f}\n"
            f"{dol_line}"
            f"⚖️  RR:      {s.get('rr_ratio',0):.1f}R\n"
            f"📦 Lots:    {s.get('lots',0):.2f}\n\n"
            f"🧠 AI: [{ai_bar}] {ai:.0f}/100\n"
            f"💥 Disp:   {disp:.2f}x ATR\n"
            f"📐 FVG:    {fvg_size:.1f} pips\n\n"
            f"💡 {reason}\n\n"
            f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def new_trade(self,s): self.new_trade_v3(s)

    def tp_hit(self,ticket,symbol,tp_level,profit):
        stars="⭐"*tp_level
        self._send(
            f"✅ TP{tp_level} HIT  {stars}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💰 Profit: ${profit:+.4f}\n"
            f"🔒 SL → Break-Even\n"
            f"🏃 Runner to TP{tp_level+1}...\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def trade_closed(self,ticket,symbol,profit,pips):
        r="PROFIT 💰" if profit>0 else "LOSS"
        self._send(
            f"{'✅' if profit>0 else '❌'} CLOSED — {r}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💵 PnL: ${profit:+.4f}\n📏 Pips: {pips:+.1f}\n"
            f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def trade_closed_be(self,ticket,symbol,pips):
        self._send(
            f"🔰 BREAKEVEN — Capital Safe\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"🛡️  Protected\n📏 Pips: {pips:+.1f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def sl_hit(self,ticket,symbol,loss):
        self._send(
            f"❌ STOP LOSS HIT\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"💸 Loss: ${loss:+.4f}\n"
            f"📌 SL did its job\n🔄 Next setup...\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def bad_trade_closed(self,ticket,symbol,profit,r):
        self._send(
            f"⚠️ BAD TRADE CLOSED\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 {symbol}\n🎫 #{ticket}\n"
            f"📉 {r:.2f}R — setup failed\n"
            f"💸 ${profit:+.4f}\n🛡️  Capital preserved\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def drawdown_warning(self,balance,equity,loss_pct):
        self._send(
            f"⚠️ DAILY LIMIT — ONE WARNING\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📉 Loss: {loss_pct:.1f}%\n"
            f"💰 Balance: ${balance:,.2f}\n⚖️  Equity: ${equity:,.2f}\n\n"
            f"🔒 No new trades today\n👁️  Monitoring positions\n"
            f"🔄 Resumes tomorrow\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def drawdown_recovered(self,balance,equity):
        self._send(
            f"✅ TRADING RESUMED\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 ${balance:,.2f} | ⚖️  ${equity:,.2f}\n"
            f"🚀 Hunting setups!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def account_empty(self):
        self._send("🚨 ACCOUNT EMPTY\n━━━━━━━━━━━━\n⛔ Trading halted\n💡 Please deposit")

    def account_low(self,balance):
        self._send(f"⚠️ ACCOUNT LOW\n━━━━━━━━━━━━\n💰 ${balance:.2f}\n⛔ Below minimum ($5)\n💡 Top up account")

    def daily_summary(self,s):
        wins=s.get("wins",0); losses=s.get("losses",0); total=s.get("total_trades",0)
        pnl=s.get("net_pnl",0); bal=s.get("balance",0)
        wb=("🟢"*wins+"🔴"*losses) if total>0 else "⬜ No trades"
        pi="📈" if pnl>=0 else "📉"
        self._send(
            f"📅 DAILY SUMMARY\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📆 {s.get('date','')}\n\n"
            f"📊 {wb}\n\n"
            f"🎯 Trades:   {total}\n✅ Wins: {wins}  ❌ Losses: {losses}\n"
            f"📈 Win Rate: {s.get('win_rate',0):.1f}%\n"
            f"{pi} PnL: ${pnl:+.4f}\n💰 Balance: ${bal:,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def weekly_summary(self,s):
        pnl=s.get("net_pnl",0); pi="📈" if pnl>=0 else "📉"
        self._send(f"🗓️  WEEKLY\n━━━━━━━━━━━━\n📊 WR: {s.get('win_rate',0):.1f}%\n{pi} ${pnl:+.4f}")

    def ai_retrained(self,samples,accuracy):
        bar="█"*int(accuracy/10)+"░"*(10-int(accuracy/10))
        self._send(f"🤖 AI RETRAINED\n━━━━━━━━━━━━\n📚 {samples} samples\n🎯 [{bar}] {accuracy:.1f}%")

    def mt5_connected(self,server):
        self._send(f"🔌 MT5 RECONNECTED\n━━━━━━━━━━━━\n🖥️  {server}\n🕐 {datetime.utcnow().strftime('%H:%M')} UTC")

    def error(self,m): self._send(f"🚨 ERROR\n━━━━━━━━━━━━\n{m}")
    def warning(self,m): self._send(f"⚠️ WARNING\n━━━━━━━━━━━━\n{m}")

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
'@
$notifier | Out-File -FilePath "C:\ForexBot\telegram\notifier.py" -Encoding UTF8
Write-Host "[3/5] notifier.py updated with Romeo-style messages!" -ForegroundColor Green

# ==============================================================================
# FILE 4: Updated main.py using RomeoScanner
# ==============================================================================
$main = @'
import os,sys,time,signal,traceback,threading
from datetime import datetime,timedelta,date

ROOT=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)

from core.logger import get_logger
from config import settings
from mt5.connector import MT5Connector
from core.romeo_scanner import RomeoScanner
from core.trade_manager import TradeManager
from core.reporting import ReportingEngine
from risk.manager import RiskManager
from storage.database import Database
from telegram.notifier import TelegramNotifier
from ai.signal_scorer import AISignalScorer

log=get_logger("main")
_RUNNING=True
ADDON_AI=72
MIN_BAL=5.0

def _stop(s,f):
    global _RUNNING; _RUNNING=False

signal.signal(signal.SIGINT,_stop)
signal.signal(signal.SIGTERM,_stop)

class ForexBot:
    def __init__(self):
        log.info("="*60)
        log.info("  ROMEO ICT BOT V3 - STARTING")
        log.info("  Strategy: Stop Hunt -> MSS -> FVG")
        log.info("  Pairs: %d",len(settings.SYMBOLS))
        log.info("="*60)
        self.db=Database(); self.notifier=TelegramNotifier()
        self.mt5=MT5Connector(); self.risk=RiskManager()
        self.ai=AISignalScorer()
        self.scanner=None; self.trader=None; self.reporter=None
        self._dd_warned_date=None; self._dd_active=False
        self._dd_recovery_sent=False; self._low_bal_warned=False
        self._last_balance=0.0

    def start(self):
        log.info("Waiting for MT5...")
        connected=False
        for attempt in range(20):
            log.info("MT5 attempt %d/20...",attempt+1)
            if self.mt5.connect(): connected=True; break
            time.sleep(15)
        if not connected:
            self.notifier.error("Bot failed to connect to MT5!")
            sys.exit(1)
        self.scanner=RomeoScanner(self.mt5,self.ai)
        self.trader=TradeManager(self.mt5,self.risk,self.db,self.notifier,self.ai)
        self.reporter=ReportingEngine(self.db,self.notifier)
        acct=self.mt5.get_account_info()
        if acct:
            self._last_balance=acct["balance"]
            self.notifier.startup_v2(acct["balance"],acct["login"],len(settings.SYMBOLS),acct["balance"]<500)
        threading.Thread(target=self._heartbeat_loop,daemon=True).start()
        log.info("Romeo ICT Bot scanning %d pairs",len(settings.SYMBOLS))
        self._loop()

    def _heartbeat_loop(self):
        time.sleep(10800)
        while _RUNNING:
            try:
                acct=self.mt5.get_account_info()
                if acct:
                    op=self.mt5.get_open_positions()
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
                    for i in range(10):
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
            if not self._low_bal_warned: self._low_bal_warned=True; self.notifier.account_empty()
            return
        if balance<MIN_BAL:
            if not self._low_bal_warned: self._low_bal_warned=True; self.notifier.account_low(balance)
            self.trader.monitor_positions(); return
        if self._low_bal_warned and balance>=MIN_BAL: self._low_bal_warned=False
        self._last_balance=balance
        self.risk.update_balance_tracking(balance)
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
                elif nop>=settings.MAX_OPEN_POSITIONS:
                    if symbol in csyms:
                        sig=self.scanner.scan(symbol,open_positions=cop)
                        if sig and sig.ai_score>=ADDON_AI: self.trader.execute_signal(sig)
            except Exception as e: log.error("[%s] Scan: %s",symbol,e)
        self.reporter.check_and_send_reports(balance)

if __name__=="__main__":
    try:
        from dotenv import load_dotenv; load_dotenv(".env")
    except: pass
    ForexBot().start()
'@
$main | Out-File -FilePath "C:\ForexBot\main.py" -Encoding UTF8
Write-Host "[4/5] main.py updated - using RomeoScanner!" -ForegroundColor Green

# ==============================================================================
# FILE 5: Update trade_manager to pass DOL/FVG info to Telegram
# ==============================================================================
# Quick patch - update new_trade_v3 call to include Romeo signal fields
$tm_content = Get-Content "C:\ForexBot\core\trade_manager.py" -Raw
$tm_content = $tm_content -replace 'sig_dict\.update\(\{([^}]+)\}\)', 'sig_dict.update({
            "entry_price": result["price"],
            "regime":      meta.get("regime","RANGING"),
            "risk_mult":   ar.risk_multiplier,
            "lots":        volume,
            "is_addon":    is_addon,
            "killzone":    meta.get("session","other"),
            "displacement":meta.get("displacement", 0),
            "fvg_size_pips":meta.get("fvg_size_pips",0),
            "dol_target":  meta.get("dol_target",0),
        })'
$tm_content | Out-File -FilePath "C:\ForexBot\core\trade_manager.py" -Encoding UTF8
Write-Host "[5/5] trade_manager.py patched for Romeo signal fields!" -ForegroundColor Green

# ==============================================================================
# START BOT
# ==============================================================================
Write-Host ""
Write-Host "Starting Romeo ICT Bot..." -ForegroundColor Cyan
Start-Process -FilePath "C:\Program Files\Python311\python.exe" -ArgumentList "C:\ForexBot\main.py" -WorkingDirectory "C:\ForexBot" -WindowStyle Normal
Start-Sleep -Seconds 20
Get-Content "C:\ForexBot\logs\main.log" -Tail 15

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ROMEO ICT BOT V3 - FULLY UPGRADED!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Strategy: ICT 2022 Model (RomeoTPT)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Entry Logic:" -ForegroundColor White
Write-Host "  1. Killzone check (London/NY/Silver Bullet)" -ForegroundColor White
Write-Host "  2. Liquidity sweep (PDH/PDL/EQH/EQL)" -ForegroundColor White
Write-Host "  3. MSS + Displacement (energetic snap)" -ForegroundColor White
Write-Host "  4. FVG entry at 50% (limit at gap)" -ForegroundColor White
Write-Host "  5. SL beyond sweep candle" -ForegroundColor White
Write-Host "  6. TP1=2R, TP2=3R, DOL=5R" -ForegroundColor White
Write-Host ""
Write-Host "S&D Zones = Confluence bonus only" -ForegroundColor Yellow
Write-Host "Crypto/Gold = 24/7 scanning" -ForegroundColor Yellow
Write-Host "Silver Bullet = Highest priority window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Telegram will show:" -ForegroundColor Cyan
Write-Host "  Killzone label" -ForegroundColor White
Write-Host "  Displacement strength" -ForegroundColor White
Write-Host "  FVG size in pips" -ForegroundColor White
Write-Host "  Draw on Liquidity target" -ForegroundColor White
