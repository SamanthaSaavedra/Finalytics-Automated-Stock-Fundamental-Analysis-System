from __future__ import annotations

import threading
from typing import Dict, Any, Optional, Tuple, List
from time import time

from services.db import db
from services.fast_cache import swr_cache

# -------- Formatting utilities --------
def _safe_float(x) -> Optional[float]:
    if x is None:
        return None
    try:
        s = str(x).strip()
        if s == "" or s.lower() in {"none", "nan"}:
            return None
        s = s.replace(",", "").replace("%", "")
        return float(s)
    except Exception:
        return None

def _fmt_money(n: Optional[float]) -> str:
    if n is None:
        return ""
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1e12: return f"{sign}${n/1e12:.2f}T"
    if n >= 1e9:  return f"{sign}${n/1e9:.2f}B"
    if n >= 1e6:  return f"{sign}${n/1e6:.2f}M"
    if n >= 1e3:  return f"{sign}${n/1e3:.2f}K"
    return f"{sign}${n:.0f}"

def _fmt_percent(n: Optional[float]) -> str:
    if n is None: return ""
    return f"{n:.2f}%"

def _growth_pct(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None or prev == 0:
        return None
    try:
        return ((curr - prev) / abs(prev)) * 100.0
    except Exception:
        return None

# -------- Minimal Mongo reads --------
def _find_overview(sym: str) -> dict:
    return db["overview"].find_one(
        {"$or": [{"Symbol": sym}, {"Ticket": sym}, {"symbol": sym}]},
        {
            "_id": 0,
            "RevenueTTM": 1, "GrossProfitTTM": 1,
            "OperatingMarginTTM": 1, "ProfitMargin": 1,
            "EPS": 1, "PERatio": 1, "DividendYield": 1,
            "MarketCapitalization": 1,
        },
    ) or {}

def _find_income_last_two(sym: str) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    doc = db["income_statements"].find_one(
        {"$or": [{"symbol": sym}, {"Symbol": sym}]},
        {"_id": 0, "annualReports": 1}
    )
    if not doc: return None, None, None, None
    ars = list(doc.get("annualReports") or [])
    ars.sort(key=lambda x: x.get("fiscalDateEnding") or "", reverse=True)
    last = ars[0] if ars else {}
    prev = ars[1] if len(ars) > 1 else {}
    rev_last = _safe_float(last.get("totalRevenue"))
    rev_prev = _safe_float(prev.get("totalRevenue"))
    net_last = _safe_float(last.get("netIncome"))
    net_prev = _safe_float(prev.get("netIncome"))
    return rev_last, rev_prev, net_last, net_prev

def _find_balance_latest(sym: str) -> dict:
    doc = db["balance_sheets"].find_one(
        {"$or": [{"symbol": sym}, {"Symbol": sym}]},
        {"_id": 0, "annualReports": 1}
    )
    if not doc: return {}
    ars = list(doc.get("annualReports") or [])
    ars.sort(key=lambda x: x.get("fiscalDateEnding") or "", reverse=True)
    last = ars[0] if ars else {}
    return {
        "Cash": _safe_float(last.get("cashAndCashEquivalentsAtCarryingValue")),
        "TotalDebt": _safe_float(last.get("shortLongTermDebtTotal")),
        "CurrentAssets": _safe_float(last.get("totalCurrentAssets")),
        "CurrentLiabilities": _safe_float(last.get("totalCurrentLiabilities")),
        "Equity": _safe_float(last.get("totalShareholderEquity")),
    }

# -------- KPI builder --------
def _build_items(sym: str) -> Dict[str, Any]:
    ov = _find_overview(sym)
    rev_ttm = _safe_float(ov.get("RevenueTTM"))
    gross_ttm = _safe_float(ov.get("GrossProfitTTM"))
    op_margin_ttm = _safe_float(ov.get("OperatingMarginTTM"))
    net_margin_ttm = _safe_float(ov.get("ProfitMargin"))

    rev_last, rev_prev, net_last, net_prev = _find_income_last_two(sym)
    bal = _find_balance_latest(sym)

    cash = bal.get("Cash")
    debt = bal.get("TotalDebt")
    curr_assets = bal.get("CurrentAssets")
    curr_liab = bal.get("CurrentLiabilities")
    equity = bal.get("Equity")

    net_cash = (cash - debt) if (cash is not None and debt is not None) else None
    curr_ratio = (curr_assets / curr_liab) if (curr_assets and curr_liab and curr_liab != 0) else None
    de_ratio = ((debt / equity) * 100.0) if (debt is not None and equity not in (None, 0)) else None

    rev_yoy = _growth_pct(rev_last, rev_prev)
    net_yoy = _growth_pct(net_last, net_prev)

    items: List[Dict[str, Any]] = []

    def _add(title: str, value_str: str, delta: Optional[float] = None):
        d: Dict[str, Any] = {"title": title, "value": value_str}
        if isinstance(delta, (int, float)):
            d["delta"] = float(delta)
        items.append(d)

    # Revenue
    if rev_ttm is not None:
        _add("Revenue (TTM)", _fmt_money(rev_ttm), rev_yoy)
    elif rev_last is not None:
        _add("Revenue (last year)", _fmt_money(rev_last), rev_yoy)

    # Net income
    if net_last is not None:
        _add("Net Income", _fmt_money(net_last), net_yoy)

    # Cash / Debt / Net cash
    if cash is not None:
        _add("Cash", _fmt_money(cash))
    if debt is not None:
        _add("Debt", _fmt_money(debt))
    if net_cash is not None:
        _add("Net Cash", _fmt_money(net_cash))

    # Ratios
    if de_ratio is not None:
        _add("Debt/Equity", _fmt_percent(de_ratio))
    if curr_ratio is not None:
        _add("Current Ratio", f"{curr_ratio:.2f}×")

    # Margins (TTM)
    if gross_ttm is not None and rev_ttm not in (None, 0):
        _add("Gross Margin (TTM)", _fmt_percent((gross_ttm / rev_ttm) * 100.0))
    if op_margin_ttm is not None:
        _add("Operating Margin (TTM)", _fmt_percent(op_margin_ttm * 100.0))
    if net_margin_ttm is not None:
        _add("Net Margin (TTM)", _fmt_percent(net_margin_ttm * 100.0))

    # Additional overview metrics
    mc = _safe_float(ov.get("MarketCapitalization"))
    if mc is not None: _add("Market Cap", _fmt_money(mc))
    eps = _safe_float(ov.get("EPS"))
    if eps is not None: _add("EPS (TTM)", f"{eps:.2f}")
    pe = _safe_float(ov.get("PERatio"))
    if pe is not None: _add("P/E Ratio", f"{pe:.2f}")
    dy = _safe_float(ov.get("DividendYield"))
    if dy is not None: _add("Dividend Yield", _fmt_percent(dy * 100.0))

    return {"symbol": sym, "items": items}

# -------- SWR + KPI cache --------
def _cache_key(sym: str) -> str:
    return f"kpis_ultra:{sym}"

def _persist_get(sym: str) -> Optional[Dict[str, Any]]:
    doc = db["kpi_cache"].find_one({"_id": sym}, {"_id": 0, "data": 1})
    return None if not doc else doc.get("data")

def _persist_set(sym: str, data: Dict[str, Any]) -> None:
    db["kpi_cache"].update_one({"_id": sym}, {"$set": {"data": data, "ts": time()}}, upsert=True)

def _revalidate(sym: str, ttl: int):
    # runs in a thread, recomputes and updates caches
    try:
        data = _build_items(sym)
        swr_cache.set(_cache_key(sym), data, ttl=ttl)
        _persist_set(sym, data)
    except Exception:
        pass

def compute_shortcuts_ultra(symbol: str, allow_stale: bool = True, ttl: int = 900) -> Tuple[Dict[str, Any], bool]:
    """
    Returns (data, fresh)
    - If memory cache exists: serve it (fresh or stale).
    - If no memory cache: try persistent kpi_cache (instant), and trigger background revalidation.
    - If nothing exists: compute synchronously (first hit) and store.
    """
    sym = (symbol or "").upper()
    key = _cache_key(sym)

    # memory cache
    val, fresh = swr_cache.get(key)
    if val is not None:
        if not fresh and allow_stale:
            threading.Thread(target=_revalidate, args=(sym, ttl), daemon=True).start()
        return val, fresh

    # persistent cache
    persisted = _persist_get(sym)
    if persisted is not None:
        swr_cache.set(key, persisted, ttl=ttl)
        if allow_stale:
            threading.Thread(target=_revalidate, args=(sym, ttl), daemon=True).start()
        return persisted, False

    data = _build_items(sym)
    swr_cache.set(key, data, ttl=ttl)
    _persist_set(sym, data)
    return data, True

__all__ = ["compute_shortcuts_ultra"]