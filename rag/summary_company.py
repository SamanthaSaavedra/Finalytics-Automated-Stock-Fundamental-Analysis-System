import os
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm
from openai import OpenAI
from services.db import *

# ===================== Config =====================
BATCH_SIZE = 16
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMB_MODEL = "ohsuz/k-finance-sentence-transformer"

# ===================== CHANGE FOR YOUR OWN APIS TO GET IT WORK  =====================

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if HUGGINGFACE_TOKEN:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACE_TOKEN

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Preload model
_embed_model_singleton = None
def get_embed_model():
    global _embed_model_singleton
    if _embed_model_singleton is None:
        _embed_model_singleton = SentenceTransformer(
            EMB_MODEL,
            device=device
        )
    return _embed_model_singleton

# ===================== RAG Summary =====================
class CompanyRAG:
    def __init__(self, ticker: str, *, verbose: bool = False):
        self.ticker = ticker.upper()
        self.docs_col = docs_col
        self.emb_col = emb_col
        self.embed_model = get_embed_model()
        self.verbose = verbose

        self.texts = []
        self.embeddings = None
        self.index = None

        # build on demand
        self.summary = self._run_pipeline()

    # ------- utils -------
    def chunk_text(self, text):
        words = text.split()
        chunks = []
        step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
        for i in range(0, len(words), step):
            chunks.append(" ".join(words[i:i+CHUNK_SIZE]))
        return chunks

    # ------- embeddings + index -------
    def process_embeddings_in_memory(self):
        if self.verbose:
            print(f"[RAG] Processing texts for {self.ticker}")
        cursor = self.docs_col.find({"_id": self.ticker})
        batch_texts = []

        for doc in tqdm(cursor, disable=not self.verbose):
            text = doc.get("sec_text_full_clean", "")
            if not text.strip():
                continue
            chunks = self.chunk_text(text)
            batch_texts.extend(chunks)

        if batch_texts:
            self.embeddings = self.embed_model.encode(
                batch_texts, convert_to_numpy=True, normalize_embeddings=True
            ).astype("float32")
            self.texts = batch_texts

    def build_faiss_in_memory(self):
        if self.embeddings is None or len(self.embeddings) == 0:
            raise ValueError("No embeddings available to build FAISS (empty docs?)")
        import faiss
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)
        if self.verbose:
            print(f"[RAG] FAISS ready for {self.ticker}")

    def retrieve(self, query, top_k=5):
        if self.index is None:
            raise ValueError("FAISS index is not built")
        query_emb = self.embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        distances, indices = self.index.search(query_emb, top_k)
        return [self.texts[i] for i in indices[0]]

    # ------- LLM -------
    def summarize_with_deepseek(self, prompt, model="deepseek-chat"):
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY not configured")
        messages = [
            {"role": "system", "content": (
                "You are a financial analyst. Summarize the company's financial performance clearly and concisely.\n"
                "- Include key figures (revenue, net income, gross margin, operating margin, ROE, ROA).\n"
                "- Explain trends over the years and interpret them.\n"
                "- End with a short conclusion.\n"
                "- Keep it under 250 words, no lists."
            )},
            {"role": "user", "content": prompt}
        ]
        resp = client_deepseek.chat.completions.create(model=model, messages=messages, stream=False)
        return resp.choices[0].message.content

    # ------- pipeline -------
    def rag_summary(self, query, top_k=5):
        chunks = self.retrieve(query, top_k=top_k)
        combined_text = "\n\n".join(chunks)
        return self.summarize_with_deepseek(combined_text)

    def _run_pipeline(self):
        self.process_embeddings_in_memory()
        self.build_faiss_in_memory()
        query = f"Summarize {self.ticker}'s financial performance for the last 5 years"
        return self.rag_summary(query)

# ============= Public helper for the dashboard =============
def generate_summary(symbol: str, *, persist: bool = True, verbose: bool = False) -> str:
    """
    Generates the RAG summary from `docs` (must exist). If `persist=True`,
    stores it in `analysis.summary` and returns the text.
    """
    summary = CompanyRAG(symbol, verbose=verbose).summary
    if persist:
        db["analysis"].update_one({"symbol": symbol.upper()}, {"$set": {"summary": summary}}, upsert=True)
    return summary

# ============= Manual entrypoint ============
if __name__ == "__main__":
    txt = generate_summary("AAPL", persist=False, verbose=True)
    print("\n--- Summary ---\n")
    print(txt)