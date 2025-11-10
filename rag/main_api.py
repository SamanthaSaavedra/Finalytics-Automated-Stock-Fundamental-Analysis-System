import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .summary_company import CompanyRAG
from .generate_rag_documents import CompanyRAGDocument
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

start_time = time.time()
print(f"[{time.strftime('%X')}] Starting initialization of models and data...")

ticker = "AAPL"
doc = CompanyRAGDocument(ticker)
rag = CompanyRAG(ticker)

end_time = time.time()
elapsed = end_time - start_time

print(f"[{time.strftime('%X')}] Initialization finished in {elapsed:.2f} seconds!")

app = FastAPI(title="Company RAG API")

class RAGSummaryResponse(BaseModel):
    ticker: str
    summary: str
    
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/company_rag", response_model=RAGSummaryResponse)
def get_company_rag_summary(ticker: str = Query(..., description="Ticker de la compañía, p.ej. AAPL")):

    ticker = ticker.upper()

    try:
        doc = CompanyRAGDocument(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        rag = CompanyRAG(ticker)
        return {
            "ticker": ticker,
            "summary": rag.summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))