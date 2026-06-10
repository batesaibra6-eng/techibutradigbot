"""
SMT DIVERGENCE ENGINE
Compares correlated pairs for confirmation.
Bearish SMT: Asset A makes HH, Asset B fails to make HH → weakness
Bullish SMT: Asset A makes LL, Asset B fails to make LL → strength
"""
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict
from core.logger import get_logger
from config.settings import SMT_LOOKBACK, SMT_PAIRS

log = get_logger("strategy.smt")

@dataclass
class SMTResult:
    confirmed: bool
    kind: str        # "BULLISH_SMT" | "BEARISH_SMT" | "NONE"
    strength: float  # 0-1
    reason: str


class SMTEngine:
    def check(self, symbol: str, direction: str,
              candles: Dict[str, pd.DataFrame]) -> SMTResult:
        corr = SMT_PAIRS.get(symbol)
        if not corr or corr not in candles:
            return SMTResult(False, "NONE", 0.0, "No correlation pair")

        df_a = candles.get(symbol)
        df_b = candles.get(corr)
        if df_a is None or df_b is None or len(df_a) < SMT_LOOKBACK:
            return SMTResult(False, "NONE", 0.0, "Insufficient data")

        lb = SMT_LOOKBACK
        a_high = df_a["high"].tail(lb).max()
        b_high = df_b["high"].tail(lb).max()
        a_low  = df_a["low"].tail(lb).min()
        b_low  = df_b["low"].tail(lb).min()
        a_prev_high = df_a["high"].tail(lb*2).head(lb).max()
        b_prev_high = df_b["high"].tail(lb*2).head(lb).max()
        a_prev_low  = df_a["low"].tail(lb*2).head(lb).min()
        b_prev_low  = df_b["low"].tail(lb*2).head(lb).min()

        if direction == "SELL":
            # Bearish SMT: A makes HH, B fails
            a_hh = a_high > a_prev_high
            b_fail = b_high <= b_prev_high
            if a_hh and b_fail:
                div = (a_high - a_prev_high) / (a_prev_high + 1e-9)
                fail = (b_prev_high - b_high) / (b_prev_high + 1e-9)
                strength = min((div + fail) * 10, 1.0)
                return SMTResult(True, "BEARISH_SMT", strength,
                                 f"SMT: {symbol} HH, {corr} failed HH")

        if direction == "BUY":
            # Bullish SMT: A makes LL, B fails
            a_ll = a_low < a_prev_low
            b_fail = b_low >= b_prev_low
            if a_ll and b_fail:
                div = (a_prev_low - a_low) / (a_prev_low + 1e-9)
                fail = (b_low - b_prev_low) / (b_prev_low + 1e-9)
                strength = min((div + abs(fail)) * 10, 1.0)
                return SMTResult(True, "BULLISH_SMT", strength,
                                 f"SMT: {symbol} LL, {corr} failed LL")

        return SMTResult(False, "NONE", 0.0, "No SMT divergence")
