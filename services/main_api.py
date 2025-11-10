import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from services.db import db
from services.dashboard_data_builder import DashboardData
from services.db import docs_col, emb_col
from services.user_prefs import (
    get_prefs, get_display_name, set_display_name,
    get_theme, set_theme,
    get_watchlist, get_recents, remove_recent,
    get_watchlist, add_to_watchlist, remove_from_watchlist, touch_recent
)
from services.kpi_services import compute_shortcuts_ultra
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

app = FastAPI()

class DocumentData(BaseModel):
    id: str = Field(..., alias="_id")
    trend_summary: str
    table_summary: str
    sec_text_full_clean: str

    class Config:
        allow_population_by_field_name = True

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/dashboard/{symbol}")
def get_dashboard(symbol: str):
    company = DashboardData(symbol)
    return company.get_full_data()

@app.get("/document/{symbol}")
def get_document(symbol: str):
    doc = docs_col.find_one({"_id": symbol.upper()})
    if not doc:
        return {"exists": False, "message": "Document not found"}

    doc["_id"] = str(doc["_id"])
    return {"exists": True, "document": doc}

@app.post("/document/")
def save_document(doc_data: DocumentData):

    doc_dict = doc_data.dict(by_alias=True)
    symbol_upper = doc_dict["_id"].upper()
    doc_dict["_id"] = symbol_upper


    if docs_col.find_one({"_id": doc_dict["_id"]}):
            raise HTTPException(status_code=400, detail=f"Document for {doc_dict['_id']} already exists")

    data_to_save = {
        "_id": symbol_upper,
        "trend_summary": doc_data.trend_summary,
        "table_summary": doc_data.table_summary,
        "sec_text_full_clean": doc_data.sec_text_full_clean
    }

    print("=== DEBUG: data_to_save ===")
    for key, value in data_to_save.items():
        print(f"{key}: {type(value)} -> {value[:100] + '...' if isinstance(value, str) and len(value) > 100 else value}")

    result = docs_col.insert_one(data_to_save)
    return {"success": True, "inserted_id": str(result.inserted_id)}

@app.get("/all-docs")
def get_all_docs():
    docs = list(docs_col.find({}))
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"documents": docs}

@app.get("/all-embeddings")
def get_all_embeddings():
    embeddings = list(emb_col.find({}))
    for e in embeddings:
        e["_id"] = str(e["_id"])
    return {"embeddings": embeddings}

@app.get("/analysis/{symbol}/summary")
def get_summary(symbol: str):
    rec = db["analysis"].find_one({"symbol": symbol.upper()}) or {}
    return {"summary": rec.get("summary", "")}

@app.get("/docs/{symbol}/preview")
def get_preview(symbol: str):
    doc = db["docs"].find_one({"_id": symbol.upper()}) or {}
    preview_txt = (
        (doc.get("trend_summary") or "") + "\n\n" + (doc.get("table_summary") or "")
    ).strip()
    return {"preview": preview_txt}

### FROTEND OPTIONS ###

@app.get("/user/{user_id}/prefs")
def get_user_prefs(user_id: str):

    def to_json_safe(data):
        """Convierte ObjectId y otros tipos no serializables en tipos válidos de JSON."""
        if isinstance(data, list):
            return [to_json_safe(v) for v in data]
        elif isinstance(data, dict):
            return {k: to_json_safe(v) for k, v in data.items()}
        elif isinstance(data, ObjectId):
            return str(data)
        else:
            return data

    prefs = get_prefs(user_id)
    safe_prefs = to_json_safe(prefs)
    return jsonable_encoder(safe_prefs)

@app.get("/user/{user_id}/display-name")
def get_display_name_api(user_id: str):
    name = get_display_name(user_id)
    return {"display_name": name}

@app.post("/user/{user}/display-name/{name}")
def set_display_name_api(user: str, name: str):
    set_display_name(name, user)
    return {"status": "ok"}

@app.get("/user/{user_id}/theme")
def get_theme_api(user_id: str):
    theme = get_theme(user_id)
    return {"theme": theme}   

@app.post("/user/{user}/theme/{theme}")
def set_theme_api(user: str, theme: str):
    set_theme(theme, user)
    return {"status": "ok"}

@app.get("/user/{user_id}/watchlist")
def get_watchlist_api(user_id: str):
    return {"watchlist": get_watchlist(user_id)}

@app.post("/user/{user_id}/watchlist/{symbol}")
def add_to_watchlist_api(user_id: str, symbol: str):
    return {"watchlist": add_to_watchlist(symbol, user_id)}

@app.delete("/user/{user_id}/watchlist/{symbol}")
def remove_from_watchlist_api(user_id: str, symbol: str):
    return {"watchlist": remove_from_watchlist(symbol, user_id)}

@app.get("/user/{user_id}/recents")
def get_recents_api(user_id: str):
    return {"recents": get_recents(user_id)}

@app.delete("/user/{user_id}/recents/{symbol}")
def remove_recent_api(user_id: str, symbol: str):
    remove_recent(symbol, user_id)
    return {"status": "ok", "recents": get_recents(user_id)}

@app.get("/user/{symbol}/shortcuts")
def get_shortcuts_api(symbol: str):
    return compute_shortcuts_ultra(symbol, allow_stale=True, ttl=900)

@app.post("/user/{user_id}/recents/{symbol}")
def touch_recent_api(user_id: str, symbol: str):
    touch_recent(symbol, user_id)
    return {"status": "ok", "recents": get_recents(user_id)}