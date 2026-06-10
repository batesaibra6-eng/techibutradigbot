"""
==============================================================================
MT5 — Connector
==============================================================================
Handles connection, login, live price streaming and all trade operations.
"""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

from core.logger import get_logger
from config import settings

log = get_logger("mt5.connector")

# ── Lazy-import MetaTrader5 so the rest of the project can be tested
#    on a machine that does NOT have MT5 installed. ────────────────────
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None          # type: ignore
    MT5_AVAILABLE = False
    log.warning("MetaTrader5 package not installed — running in STUB mode.")


# ── MT5 timeframe constant map (filled at import time if mt5 available) ─
TF_MAP: Dict[str, Any] = {}


def _build_tf_map() -> None:
    if not MT5_AVAILABLE:
        return
    global TF_MAP
    TF_MAP = {
        "M1":  mt5.TIMEFRAME_M1,
        "M5":  mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1":  mt5.TIMEFRAME_H1,
        "H4":  mt5.TIMEFRAME_H4,
        "D1":  mt5.TIMEFRAME_D1,
        "W1":  mt5.TIMEFRAME_W1,
    }


_build_tf_map()


class MT5Connector:
    """Manages the lifecycle of the MT5 terminal connection."""

    def __init__(self) -> None:
        self._connected = False

    # ------------------------------------------------------------------
    # CONNECTION
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Initialise and authenticate with the MT5 terminal."""
        if not MT5_AVAILABLE:
            log.error("MetaTrader5 library not found.")
            return False

        log.info("Initialising MT5 terminal…")
        if not mt5.initialize(
            path=settings.MT5_PATH,
            login=settings.MT5_LOGIN,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER,
            timeout=10_000,
            portable=False,
        ):
            err = mt5.last_error()
            log.error("mt5.initialize() failed: %s", err)
            return False

        info = mt5.account_info()
        if info is None:
            log.error("Could not retrieve account info after init.")
            mt5.shutdown()
            return False

        self._connected = True
        log.info(
            "MT5 connected | Account: %s | Balance: %.2f %s | Server: %s",
            info.login, info.balance, info.currency, info.server,
        )
        return True

    def disconnect(self) -> None:
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False
            log.info("MT5 disconnected.")

    def is_connected(self) -> bool:
        if not MT5_AVAILABLE or not self._connected:
            return False
        info = mt5.account_info()
        return info is not None

    def reconnect(self, max_attempts: int = settings.MAX_RECONNECT_ATTEMPTS) -> bool:
        for attempt in range(1, max_attempts + 1):
            log.info("Reconnect attempt %d/%d…", attempt, max_attempts)
            if self.connect():
                return True
            time.sleep(settings.RECONNECT_DELAY_SEC)
        log.error("All reconnect attempts failed.")
        return False

    # ------------------------------------------------------------------
    # ACCOUNT
    # ------------------------------------------------------------------
    def get_account_info(self) -> Optional[Dict]:
        if not self.is_connected():
            return None
        info = mt5.account_info()
        if info is None:
            return None
        return {
            "login":    info.login,
            "balance":  info.balance,
            "equity":   info.equity,
            "margin":   info.margin,
            "free_margin": info.margin_free,
            "profit":   info.profit,
            "currency": info.currency,
            "leverage": info.leverage,
            "server":   info.server,
        }

    def get_balance(self) -> float:
        info = self.get_account_info()
        return info["balance"] if info else 0.0

    def get_equity(self) -> float:
        info = self.get_account_info()
        return info["equity"] if info else 0.0

    # ------------------------------------------------------------------
    # MARKET DATA
    # ------------------------------------------------------------------
    def get_candles(self, symbol: str, timeframe: str, count: int = 300) -> Optional[pd.DataFrame]:
        """Fetch OHLCV candles from MT5."""
        if not self.is_connected():
            return None
        tf = TF_MAP.get(timeframe)
        if tf is None:
            log.warning("Unknown timeframe: %s", timeframe)
            return None

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            log.warning("No data returned for %s %s", symbol, timeframe)
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        return df[["open", "high", "low", "close", "volume"]]

    def get_tick(self, symbol: str) -> Optional[Dict]:
        if not self.is_connected():
            return None
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {"bid": tick.bid, "ask": tick.ask, "time": tick.time}

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        if not self.is_connected():
            return None
        info = mt5.symbol_info(symbol)
        if info is None:
            return None
        return {
            "point":      info.point,
            "digits":     info.digits,
            "trade_contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step":info.volume_step,
        }

    # ------------------------------------------------------------------
    # ORDER EXECUTION
    # ------------------------------------------------------------------
    def place_order(
        self,
        symbol: str,
        order_type: str,      # "BUY" | "SELL"
        volume: float,
        sl: float,
        tp: float,
        comment: str = "FXBot",
    ) -> Optional[Dict]:
        """Place a market order and return result dict."""
        if not self.is_connected():
            log.error("place_order: not connected.")
            return None

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            log.error("Could not retrieve tick for %s", symbol)
            return None

        otype = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if order_type == "BUY" else tick.bid

        request = {
            "action":     mt5.TRADE_ACTION_DEAL,
            "symbol":     symbol,
            "volume":     volume,
            "type":       otype,
            "price":      price,
            "sl":         sl,
            "tp":         tp,
            "deviation":  20,
            "magic":      settings.MAGIC_NUMBER,
            "comment":    comment,
            "type_time":  mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = mt5.last_error() if result is None else result.retcode
            log.error("Order failed for %s %s: %s", symbol, order_type, err)
            return None

        log.info("Order placed: %s %s vol=%.2f price=%.5f sl=%.5f tp=%.5f ticket=%s",
                 order_type, symbol, volume, price, sl, tp, result.order)
        return {
            "ticket":    result.order,
            "symbol":    symbol,
            "type":      order_type,
            "volume":    volume,
            "price":     result.price,
            "sl":        sl,
            "tp":        tp,
            "open_time": datetime.utcnow(),
        }

    def close_position(self, ticket: int, volume: Optional[float] = None) -> bool:
        """Close (fully or partially) an open position by ticket."""
        if not self.is_connected():
            return False

        pos = self._get_position_by_ticket(ticket)
        if pos is None:
            log.warning("Position ticket %d not found.", ticket)
            return False

        close_vol = volume if volume else pos.volume
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            "action":    mt5.TRADE_ACTION_DEAL,
            "position":  ticket,
            "symbol":    pos.symbol,
            "volume":    close_vol,
            "type":      close_type,
            "price":     close_price,
            "deviation": 20,
            "magic":     settings.MAGIC_NUMBER,
            "comment":   "FXBot-Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error("Close failed for ticket %d: %s", ticket,
                      mt5.last_error() if result is None else result.retcode)
            return False

        log.info("Position %d closed. Volume=%.2f", ticket, close_vol)
        return True

    def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Modify SL and/or TP of an open position."""
        if not self.is_connected():
            return False
        pos = self._get_position_by_ticket(ticket)
        if pos is None:
            return False

        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol":   pos.symbol,
            "sl":       sl if sl is not None else pos.sl,
            "tp":       tp if tp is not None else pos.tp,
        }
        result = mt5.order_send(request)
        ok = result is not None and result.retcode == mt5.TRADE_RETCODE_DONE
        if ok:
            log.info("Modified ticket %d → SL=%.5f TP=%.5f", ticket,
                     request["sl"], request["tp"])
        else:
            log.error("Modify failed for ticket %d", ticket)
        return ok

    # ------------------------------------------------------------------
    # POSITION TRACKING
    # ------------------------------------------------------------------
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        if not self.is_connected():
            return []
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            return []
        result = []
        for p in positions:
            if p.magic != settings.MAGIC_NUMBER:
                continue
            result.append({
                "ticket":     p.ticket,
                "symbol":     p.symbol,
                "type":       "BUY" if p.type == 0 else "SELL",
                "volume":     p.volume,
                "open_price": p.price_open,
                "current_price": p.price_current,
                "sl":         p.sl,
                "tp":         p.tp,
                "profit":     p.profit,
                "open_time":  datetime.fromtimestamp(p.time),
                "comment":    p.comment,
            })
        return result

    def get_trade_history(self, days: int = 30) -> List[Dict]:
        if not self.is_connected():
            return []
        from datetime import timedelta
        date_from = datetime.utcnow() - timedelta(days=days)
        deals = mt5.history_deals_get(date_from, datetime.utcnow())
        if deals is None:
            return []
        result = []
        for d in deals:
            if d.magic != settings.MAGIC_NUMBER:
                continue
            result.append({
                "ticket":     d.order,
                "deal_id":    d.ticket,
                "symbol":     d.symbol,
                "type":       "BUY" if d.type == 0 else "SELL",
                "volume":     d.volume,
                "price":      d.price,
                "profit":     d.profit,
                "commission": d.commission,
                "swap":       d.swap,
                "time":       datetime.fromtimestamp(d.time),
                "comment":    d.comment,
            })
        return result

    def _get_position_by_ticket(self, ticket: int):
        positions = mt5.positions_get(ticket=ticket)
        if positions and len(positions) > 0:
            return positions[0]
        return None
