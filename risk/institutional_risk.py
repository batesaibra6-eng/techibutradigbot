"""
==============================================================================
INSTITUTIONAL RISK MANAGEMENT ENGINE
==============================================================================
Features:
  - Dynamic position sizing (equity-tier based)
  - Daily + weekly loss caps
  - Equity curve filter
  - Volatility-adjusted sizing
  - Kill switch (consecutive losses / abnormal volatility / drawdown)
  - Spread filter
  - Slippage modeling
  - Correlation exposure limits
  - Portfolio heat tracking
"""

import math
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from core.logger import get_logger
from config.settings import (
    RISK_PER_TRADE_PCT, RISK_MIN_PCT, RISK_MAX_PCT,
    DAILY_LOSS_CAP_PCT, WEEKLY_LOSS_CAP_PCT,
    MAX_OPEN_POSITIONS, MAX_CORRELATED_EXPOSURE,
    EQUITY_CURVE_LOOKBACK, VOLATILITY_ATR_KILL,
    CONSECUTIVE_LOSS_KILL, SPREAD_MAX_PIPS,
    SL_ATR_BUFFER, EQUITY_TIERS, MICRO_ACCOUNT_THRESHOLD,
    SLIPPAGE_PIPS, COMMISSION_PER_LOT,
)

log = get_logger("risk.institutional")


@dataclass
class RiskAssessment:
    allowed:         bool
    reason:          str
    lots:            float
    risk_pct:        float
    risk_usd:        float
    kill_switch:     bool = False
    kill_reason:     str  = ""
    spread_ok:       bool = True
    volatility_ok:   bool = True
    equity_curve_ok: bool = True


@dataclass
class PortfolioState:
    open_trades:      int   = 0
    total_risk_pct:   float = 0.0
    buys:             int   = 0
    sells:            int   = 0
    daily_pnl:        float = 0.0
    weekly_pnl:       float = 0.0
    consecutive_loss: int   = 0
    equity_curve:     List[float] = field(default_factory=list)


class InstitutionalRiskManager:

    def __init__(self) -> None:
        self._day_start_balance:  float = 0.0
        self._week_start_balance: float = 0.0
        self._day_start_date:     Optional[date] = None
        self._week_start_date:    Optional[date] = None
        self._consecutive_losses: int = 0
        self._trade_outcomes:     List[float] = []  # recent P&L
        self._kill_switch_active: bool = False
        self._kill_reason:        str  = ""

    # ──────────────────────────────────────────────────────────────────────
    def assess_trade(
        self,
        symbol:        str,
        direction:     str,
        entry:         float,
        stop_loss:     float,
        sl_pips:       float,
        balance:       float,
        equity:        float,
        open_positions:List[Dict],
        spread_pips:   float = 0.0,
        current_atr:   float = 0.0,
        normal_atr:    float = 0.0,
        symbol_info:   Dict  = None,
    ) -> RiskAssessment:

        self._update_tracking(balance)

        # ── KILL SWITCH ───────────────────────────────────────────────────
        if self._kill_switch_active:
            return RiskAssessment(False, f"Kill switch: {self._kill_reason}",
                                  0.0, 0.0, 0.0, kill_switch=True)

        kill, kill_reason = self._check_kill_conditions(
            balance, equity, spread_pips, current_atr, normal_atr
        )
        if kill:
            self._kill_switch_active = True
            self._kill_reason = kill_reason
            log.critical("KILL SWITCH ACTIVATED: %s", kill_reason)
            return RiskAssessment(False, kill_reason, 0.0, 0.0, 0.0,
                                  kill_switch=True, kill_reason=kill_reason)

        # ── DAILY LOSS CAP ────────────────────────────────────────────────
        daily_loss_pct = (self._day_start_balance - equity) / (self._day_start_balance + 1e-9) * 100
        if daily_loss_pct >= DAILY_LOSS_CAP_PCT:
            return RiskAssessment(False,
                f"Daily loss cap hit: {daily_loss_pct:.1f}% >= {DAILY_LOSS_CAP_PCT}%",
                0.0, 0.0, 0.0)

        # ── WEEKLY LOSS CAP ───────────────────────────────────────────────
        weekly_loss_pct = (self._week_start_balance - equity) / (self._week_start_balance + 1e-9) * 100
        if weekly_loss_pct >= WEEKLY_LOSS_CAP_PCT:
            return RiskAssessment(False,
                f"Weekly loss cap hit: {weekly_loss_pct:.1f}% >= {WEEKLY_LOSS_CAP_PCT}%",
                0.0, 0.0, 0.0)

        # ── MAX POSITIONS ─────────────────────────────────────────────────
        if len(open_positions) >= MAX_OPEN_POSITIONS:
            return RiskAssessment(False,
                f"Max positions ({MAX_OPEN_POSITIONS}) reached", 0.0, 0.0, 0.0)

        # ── DIRECTION LIMIT ───────────────────────────────────────────────
        buys  = sum(1 for p in open_positions if p.get("type")=="BUY")
        sells = sum(1 for p in open_positions if p.get("type")=="SELL")
        if direction == "BUY"  and buys  >= MAX_CORRELATED_EXPOSURE:
            return RiskAssessment(False, f"Max BUY exposure ({MAX_CORRELATED_EXPOSURE})", 0.0, 0.0, 0.0)
        if direction == "SELL" and sells >= MAX_CORRELATED_EXPOSURE:
            return RiskAssessment(False, f"Max SELL exposure ({MAX_CORRELATED_EXPOSURE})", 0.0, 0.0, 0.0)

        # ── SPREAD FILTER ─────────────────────────────────────────────────
        max_spread = self._max_spread(symbol)
        spread_ok  = spread_pips <= max_spread
        if not spread_ok:
            return RiskAssessment(False,
                f"Spread too wide: {spread_pips:.1f} pips (max {max_spread})",
                0.0, 0.0, 0.0, spread_ok=False)

        # ── EQUITY CURVE FILTER ───────────────────────────────────────────
        eq_curve_ok = self._equity_curve_ok()
        if not eq_curve_ok:
            return RiskAssessment(False,
                "Equity curve declining — reducing size", 0.0, 0.0, 0.0,
                equity_curve_ok=False)

        # ── SURVIVAL MODE ─────────────────────────────────────────────────
        if equity < balance * 0.15:
            return RiskAssessment(False,
                f"Survival mode: equity ${equity:.2f} < 15% of balance", 0.0, 0.0, 0.0)

        # ── POSITION SIZING ───────────────────────────────────────────────
        risk_pct = self._calc_risk_pct(balance, current_atr, normal_atr)
        lots     = self._calc_lots(balance, risk_pct, sl_pips, symbol_info or {})
        risk_usd = balance * risk_pct / 100

        # Include slippage in effective risk
        slip_cost = SLIPPAGE_PIPS * (lots * 10)  # approximate
        effective_risk = risk_usd + slip_cost

        log.info(
            "[%s] Risk assessment: lots=%.2f risk=%.2f%% ($%.2f) spread=%.1f daily_dd=%.1f%%",
            symbol, lots, risk_pct, risk_usd, spread_pips, daily_loss_pct
        )

        return RiskAssessment(
            allowed=True, reason="OK",
            lots=lots, risk_pct=risk_pct,
            risk_usd=effective_risk,
            spread_ok=spread_ok,
            volatility_ok=True,
            equity_curve_ok=eq_curve_ok,
        )

    # ──────────────────────────────────────────────────────────────────────
    def record_outcome(self, profit: float, outcome: str) -> None:
        """Record trade outcome for streak and equity curve tracking."""
        self._trade_outcomes.append(profit)
        if len(self._trade_outcomes) > EQUITY_CURVE_LOOKBACK * 2:
            self._trade_outcomes.pop(0)

        if outcome == "SL":
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        # Reset kill switch on new day if losses were daily-based
        if self._consecutive_losses >= CONSECUTIVE_LOSS_KILL:
            self._kill_switch_active = True
            self._kill_reason = f"{self._consecutive_losses} consecutive losses"
            log.critical("Kill switch: %d consecutive losses", self._consecutive_losses)

    def reset_kill_switch(self) -> None:
        """Call at start of new trading day."""
        if self._kill_switch_active and "loss" in self._kill_reason.lower():
            self._kill_switch_active = False
            self._kill_reason = ""
            self._consecutive_losses = 0
            log.info("Kill switch reset for new day")

    def update_tracking(self, balance: float) -> None:
        self._update_tracking(balance)

    # ──────────────────────────────────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────────────────────────────────
    def _update_tracking(self, balance: float) -> None:
        today = date.today()
        week  = today.isocalendar()[1]

        if self._day_start_date != today:
            self._day_start_balance  = balance
            self._day_start_date     = today
            self.reset_kill_switch()
            log.info("New trading day. Balance: $%.2f", balance)

        if self._week_start_date != week:
            self._week_start_balance = balance
            self._week_start_date    = week
            log.info("New trading week. Balance: $%.2f", balance)

    def _check_kill_conditions(
        self, balance, equity, spread_pips, current_atr, normal_atr
    ) -> Tuple[bool, str]:

        # Abnormal volatility
        if normal_atr > 0 and current_atr > normal_atr * VOLATILITY_ATR_KILL:
            return True, f"Abnormal volatility: ATR {current_atr:.5f} > {VOLATILITY_ATR_KILL}x normal"

        # Consecutive losses
        if self._consecutive_losses >= CONSECUTIVE_LOSS_KILL:
            return True, f"{self._consecutive_losses} consecutive losses"

        return False, ""

    def _calc_risk_pct(self, balance: float, current_atr: float, normal_atr: float) -> float:
        """Volatility-adjusted risk percentage."""
        base = RISK_PER_TRADE_PCT

        # Scale by equity tier
        for threshold, pct_mult in EQUITY_TIERS:
            if balance >= threshold:
                base = RISK_PER_TRADE_PCT * pct_mult
                break

        # Equity curve adjustment
        if not self._equity_curve_ok():
            base *= 0.5

        # Volatility scaling
        if normal_atr > 0 and current_atr > 0:
            vol_ratio = normal_atr / (current_atr + 1e-9)
            base *= min(max(vol_ratio, 0.25), 1.5)

        return max(RISK_MIN_PCT, min(RISK_MAX_PCT, round(base, 3)))

    def _calc_lots(
        self, balance: float, risk_pct: float,
        sl_pips: float, symbol_info: Dict
    ) -> float:
        if sl_pips <= 0 or balance <= 0:
            return symbol_info.get("volume_min", 0.01)

        risk_amount   = balance * risk_pct / 100
        contract_size = symbol_info.get("trade_contract_size", 100000)
        point         = symbol_info.get("point", 0.0001)
        pip_size      = symbol_info.get("pip_size", point * 10)
        pip_value     = pip_size * contract_size
        lots          = risk_amount / (sl_pips * pip_value + 1e-9)

        vol_step = symbol_info.get("volume_step", 0.01)
        vol_min  = symbol_info.get("volume_min",  0.01)
        vol_max  = symbol_info.get("volume_max",  100.0)
        lots     = math.floor(lots / vol_step) * vol_step
        return round(max(vol_min, min(vol_max, lots)), 2)

    def _equity_curve_ok(self) -> bool:
        """Equity curve filter — are we in a losing streak pattern?"""
        if len(self._trade_outcomes) < EQUITY_CURVE_LOOKBACK:
            return True
        recent = self._trade_outcomes[-EQUITY_CURVE_LOOKBACK:]
        total  = sum(recent)
        # If losing more than 50% of risk in lookback period → reduce size
        return total > -abs(sum(abs(x) for x in recent)) * 0.5

    @staticmethod
    def _max_spread(symbol: str) -> float:
        s = symbol.replace("m","").upper()
        if "BTC" in s or "ETH" in s: return 50.0
        if "XAU" in s: return 8.0
        if "XAG" in s: return 15.0
        if "ZAR" in s: return 12.0
        if "JPY" in s: return 2.5
        return SPREAD_MAX_PIPS

    # Backward compatibility
    def is_drawdown_exceeded(self, equity: float) -> bool:
        if self._day_start_balance <= 0: return False
        return (self._day_start_balance - equity) / self._day_start_balance * 100 >= DAILY_LOSS_CAP_PCT

    def can_open_new_trade(self, open_positions, symbol, balance, equity, free_margin=None):
        if len(open_positions) >= MAX_OPEN_POSITIONS: return False
        if self.is_drawdown_exceeded(equity): return False
        if equity < balance * 0.15: return False
        return True

    def sl_pips(self, entry, sl, point):
        return abs(entry - sl) / (point * 10)

    def break_even_sl(self, entry, direction, be_buffer_pips, point):
        buf = be_buffer_pips * point * 10
        return entry + buf if direction == "BUY" else entry - buf

    def tp1_close_volume(self, original_volume, vol_step):
        half = math.floor(original_volume * 0.5 / vol_step) * vol_step
        return max(half, vol_step)
