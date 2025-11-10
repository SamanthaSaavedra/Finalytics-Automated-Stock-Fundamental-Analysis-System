from typing import List, Dict
from .db import db

COLLECTION = "user_prefs"


def _norm(s: str) -> str:
    return (s or "").strip().upper()


def _ensure_doc(user: str) -> Dict:
    doc = db[COLLECTION].find_one({"user": user})
    if not doc:
        doc = {
            "user": user,
            "display_name": "",
            "watchlist": [],
            "quick_symbols": ["MSFT", "AAPL", "GOOGL"],
            "recents": [],
            "theme": "dark",
        }
        db[COLLECTION].insert_one(doc)
    return doc


def get_prefs(user: str) -> Dict:
    return _ensure_doc(user)


# ---- Display name ----
def get_display_name(user: str) -> str:
    return _ensure_doc(user).get("display_name", "") or ""


def set_display_name(name: str, user: str):
    db[COLLECTION].update_one({"user": user}, {"$set": {"display_name": name}})


# ---- Theme ----
def get_theme(user: str) -> str:
    return _ensure_doc(user).get("theme", "dark")


def set_theme(theme: str, user: str):
    theme = "light" if (theme or "").lower().startswith("l") else "dark"
    db[COLLECTION].update_one({"user": user}, {"$set": {"theme": theme}})


# ---- Watchlist ----
def get_watchlist(user: str) -> List[str]:
    wl = _ensure_doc(user).get("watchlist", [])
    return sorted(list({_norm(s) for s in wl}))


def add_to_watchlist(symbol: str, user: str):
    sym = _norm(symbol)
    if not sym:
        return get_watchlist(user)
    db[COLLECTION].update_one({"user": user}, {"$addToSet": {"watchlist": sym}}, upsert=True)
    return get_watchlist(user)


def remove_from_watchlist(symbol: str, user: str):
    sym = _norm(symbol)
    db[COLLECTION].update_one({"user": user}, {"$pull": {"watchlist": sym}}, upsert=True)
    return get_watchlist(user)


# ---- Quick symbols  ----
def get_quick_symbols(user: str) -> List[str]:
    return [_norm(s) for s in _ensure_doc(user).get("quick_symbols", [])]


def add_quick_symbol(symbol: str, user: str):
    sym = _norm(symbol)
    if not sym:
        return get_quick_symbols(user)
    db[COLLECTION].update_one({"user": user}, {"$addToSet": {"quick_symbols": sym}}, upsert=True)
    return get_quick_symbols(user)


def remove_quick_symbol(symbol: str, user: str):
    sym = _norm(symbol)
    db[COLLECTION].update_one({"user": user}, {"$pull": {"quick_symbols": sym}}, upsert=True)
    return get_quick_symbols(user)


# ---- Recientes ----
def get_recents(user: str) -> List[str]:
    return [_norm(s) for s in _ensure_doc(user).get("recents", [])]


def touch_recent(symbol: str, user: str, max_len: int = 8):
    sym = _norm(symbol)
    doc = _ensure_doc(user)
    arr = [s for s in doc.get("recents", []) if _norm(s) != sym]
    arr.insert(0, sym)
    arr = arr[:max_len]
    db[COLLECTION].update_one({"user": user}, {"$set": {"recents": arr}}, upsert=True)


def remove_recent(symbol: str, user: str):
    sym = _norm(symbol)
    doc = _ensure_doc(user)
    arr = [s for s in doc.get("recents", []) if _norm(s) != sym]
    db[COLLECTION].update_one({"user": user}, {"$set": {"recents": arr}}, upsert=True)