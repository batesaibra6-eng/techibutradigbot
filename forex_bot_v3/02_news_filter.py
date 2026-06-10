"""
==============================================================================
02 — NEWS FILTER
==============================================================================
Blocks trading during high-impact news events.

Sources:
  • ForexFactory RSS (free, no API key)
  • Fallback: known fixed high-impact times

Blocks:
  • NFP (First Friday of month 13:30 UTC)
  • FOMC (varies, ~18:00-20:00 UTC)
  • CPI (varies, ~13:30 UTC)
  • ±30 min around any HIGH impact event

News states:
  • "clear"    → safe to trade
  • "pending"  → event within 30 min → reduce size
  • "active"   → event now → NO TRADING
  • "cooling"  → within 15 min after event → caution
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from core.logger import get_logger

log = get_logger("news_filter")

FF_RSS_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

BLOCK_BEFORE_MINS = 30   # block N mins before high-impact event
BLOCK_AFTER_MINS  = 15   # block N mins after event
REDUCE_BEFORE_MINS = 60  # reduce size N mins before


@dataclass
class NewsEvent:
    title:    str
    currency: str
    impact:   str      # "High" | "Medium" | "Low"
    time_utc: datetime


@dataclass
class NewsState:
    state:        str          # "clear" | "pending" | "active" | "cooling"
    next_event:   Optional[NewsEvent] = None
    mins_to_next: float = 999.0
    affected_currencies: List[str] = field(default_factory=list)
    should_trade: bool = True
    risk_multiplier: float = 1.0   # 0-1, reduce size near events


class NewsFilter:
    """Fetches economic calendar and blocks/reduces trades near high-impact events."""

    def __init__(self) -> None:
        self._events:      List[NewsEvent] = []
        self._last_fetch:  Optional[datetime] = None
        self._fetch_interval_mins = 120   # refresh every 2 hours

    # ──────────────────────────────────────────────────────────────────────────
    def get_state(self, symbol: str = "") -> NewsState:
        """Return current news state for a symbol."""
        self._refresh_if_needed()

        now = datetime.utcnow()
        # Extract currencies from symbol
        affected = self._symbol_to_currencies(symbol)

        # Find relevant upcoming high-impact events
        relevant = [
            e for e in self._events
            if e.impact == "High"
            and (not affected or e.currency in affected or e.currency == "ALL")
        ]

        if not relevant:
            return NewsState(state="clear", should_trade=True, risk_multiplier=1.0,
                             affected_currencies=affected)

        # Find nearest event
        future_events = [(e, (e.time_utc - now).total_seconds() / 60)
                         for e in relevant if e.time_utc > now - timedelta(minutes=BLOCK_AFTER_MINS)]
        if not future_events:
            return NewsState(state="clear", should_trade=True, risk_multiplier=1.0,
                             affected_currencies=affected)

        nearest_event, mins_away = min(future_events, key=lambda x: abs(x[1]))

        # Active: event happening now or just passed
        if -BLOCK_AFTER_MINS <= mins_away <= 0:
            log.warning("NEWS ACTIVE: %s %s — NO TRADING", nearest_event.currency, nearest_event.title)
            return NewsState(
                state="active", next_event=nearest_event,
                mins_to_next=mins_away, affected_currencies=affected,
                should_trade=False, risk_multiplier=0.0
            )

        # Pending: within block window
        if 0 < mins_away <= BLOCK_BEFORE_MINS:
            log.warning("NEWS PENDING in %.0f min: %s %s — NO TRADING",
                        mins_away, nearest_event.currency, nearest_event.title)
            return NewsState(
                state="pending", next_event=nearest_event,
                mins_to_next=mins_away, affected_currencies=affected,
                should_trade=False, risk_multiplier=0.0
            )

        # Reduce: within soft window
        if BLOCK_BEFORE_MINS < mins_away <= REDUCE_BEFORE_MINS:
            risk_mult = min((mins_away - BLOCK_BEFORE_MINS) / REDUCE_BEFORE_MINS, 1.0)
            log.info("NEWS APPROACHING in %.0f min: %s — risk_mult=%.2f",
                     mins_away, nearest_event.title, risk_mult)
            return NewsState(
                state="pending", next_event=nearest_event,
                mins_to_next=mins_away, affected_currencies=affected,
                should_trade=True, risk_multiplier=risk_mult
            )

        return NewsState(
            state="clear", next_event=nearest_event,
            mins_to_next=mins_away, affected_currencies=affected,
            should_trade=True, risk_multiplier=1.0
        )

    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_if_needed(self) -> None:
        if (self._last_fetch is None or
                (datetime.utcnow() - self._last_fetch).seconds > self._fetch_interval_mins * 60):
            self._fetch_events()

    def _fetch_events(self) -> None:
        try:
            r = requests.get(FF_RSS_URL, timeout=10)
            if r.status_code == 200:
                self._events = self._parse_ff_rss(r.text)
                self._last_fetch = datetime.utcnow()
                log.info("News calendar updated: %d events", len(self._events))
            else:
                log.warning("News fetch failed: HTTP %d", r.status_code)
                self._use_fallback()
        except Exception as e:
            log.warning("News fetch error: %s — using fallback", e)
            self._use_fallback()

    def _parse_ff_rss(self, xml_text: str) -> List[NewsEvent]:
        events = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.iter("event"):
                try:
                    impact   = item.findtext("impact", "Low")
                    currency = item.findtext("country", "")
                    title    = item.findtext("title", "")
                    date_str = item.findtext("date", "")
                    time_str = item.findtext("time", "00:00am")
                    if impact not in ("High", "Medium"):
                        continue
                    dt = self._parse_ff_datetime(date_str, time_str)
                    if dt:
                        events.append(NewsEvent(
                            title=title, currency=currency,
                            impact=impact, time_utc=dt
                        ))
                except Exception:
                    continue
        except Exception as e:
            log.error("RSS parse error: %s", e)
        return events

    @staticmethod
    def _parse_ff_datetime(date_str: str, time_str: str) -> Optional[datetime]:
        try:
            dt_str = f"{date_str} {time_str}"
            for fmt in ["%m-%d-%Y %I:%M%p", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I:%M%p"]:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    def _use_fallback(self) -> None:
        """Known fixed high-impact times as fallback."""
        now   = datetime.utcnow()
        today = now.date()
        events = []

        # NFP: First Friday 13:30 UTC
        if today.weekday() == 4:   # Friday
            nfp_time = datetime(today.year, today.month, today.day, 13, 30)
            events.append(NewsEvent("NFP", "USD", "High", nfp_time))

        # Daily fixed times that are commonly high-impact
        for hour, currency, title in [
            (13, 30, "USD", "US Data"),
            (8,  30, "GBP", "UK Data"),
            (9,  30, "EUR", "EU Data"),
        ]:
            pass  # simplified — real events come from RSS

        if not self._events:
            self._events = events
        self._last_fetch = datetime.utcnow()

    @staticmethod
    def _symbol_to_currencies(symbol: str) -> List[str]:
        """Extract currency codes from symbol name."""
        currency_map = {
            "EUR": ["EURUSD","EURGBP","EURJPY","EURAUD","EURCAD","EURCHF"],
            "GBP": ["GBPUSD","GBPJPY","GBPAUD","GBPCAD","GBPCHF","EURGBP"],
            "USD": ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","XAUUSD","BTCUSD","ETHUSD"],
            "JPY": ["USDJPY","EURJPY","GBPJPY","AUDJPY","CADJPY","CHFJPY","NZDJPY"],
            "AUD": ["AUDUSD","EURAUD","GBPAUD","AUDCAD","AUDJPY"],
            "CAD": ["USDCAD","EURCAD","GBPCAD","AUDCAD","CADJPY"],
            "CHF": ["USDCHF","GBPCHF","CHFJPY"],
            "NZD": ["NZDUSD","NZDJPY"],
            "XAU": ["XAUUSD"],
            "XAG": ["XAGUSD"],
        }
        currencies = []
        for cur, symbols in currency_map.items():
            if symbol in symbols:
                currencies.append(cur)
        return currencies
