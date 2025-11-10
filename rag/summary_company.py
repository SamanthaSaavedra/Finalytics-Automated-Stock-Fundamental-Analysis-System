import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import torch
from tqdm import tqdm
from openai import OpenAI
import requests
from services.db import *

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# ===================== Config =====================
BATCH_SIZE = 16
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMB_MODEL = "ohsuz/k-finance-sentence-transformer"

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if HUGGINGFACE_TOKEN:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACE_TOKEN
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

device = "cuda:0" if torch.cuda.is_available() else "cpu"

embed_model = SentenceTransformer(
    EMB_MODEL,
    device=device,
    use_auth_token=HUGGINGFACE_TOKEN
)

class CompanyRAG:
    def __init__(self, ticker: str, *, verbose: bool = False):
        
        self.ticker = ticker.upper()
        self.verbose = verbose 
        self.docs_api = requests.get("http://controller:8100/all-docs")
        self.emb_api = requests.get("http://controller:8100/all-embeddings")

        if self.docs_api.status_code != 200:
            raise RuntimeError(f"Error al obtener documentos: {self.docs_api.status_code} {self.docs_api.text}")
        if self.emb_api.status_code != 200:
            raise RuntimeError(f"Error al obtener embeddings: {self.emb_api.status_code} {self.emb_api.text}")

        self.docs_col = self.docs_api.json().get("documents", [])
        self.emb_col = self.emb_api.json().get("embeddings", [])

        self.embed_model = embed_model
        self.texts = []
        self.embeddings = None
        self.index = None

        self.summary = self._run_pipeline()

    # ------- utils -------
    def chunk_text(self, text):
        words = text.split()
        chunks = []
        step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
        for i in range(0, len(words), step):
            chunks.append(" ".join(words[i:i+CHUNK_SIZE]))
        return chunks

    # ------- emb + index -------
    def process_embeddings_in_memory(self):
        print(f"[STEP A] Procesando documentos para {self.ticker}")
        docs_for_ticker = [d for d in self.docs_col if d.get("_id") == self.ticker]
        if self.verbose:
            print(f"[RAG] Procesando textos para {self.ticker}")
        batch_texts = []

        for doc in tqdm(docs_for_ticker):
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
            raise ValueError("No hay embeddings para construir FAISS")

        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)
        if self.verbose:
            print(f"[RAG] FAISS listo para {self.ticker}")

    def retrieve(self, query, top_k=5):
        if self.index is None:
            raise ValueError("El índice FAISS no está construido")
        query_emb = self.embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        distances, indices = self.index.search(query_emb, top_k)
        return [self.texts[i] for i in indices[0]]

    # ------- LLM -------
    def summarize_with_deepseek(self, prompt, model="deepseek-chat"):
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
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

# ============= Helper público para el dashboard =============
def generate_summary(symbol: str, *, persist: bool = True, verbose: bool = False) -> str:
    summary = CompanyRAG(symbol, verbose=verbose).summary
    if persist:
        db["analysis"].update_one({"symbol": symbol.upper()}, {"$set": {"summary": summary}}, upsert=True)
    return summary


if __name__ == "__main__":
    txt = generate_summary("AAPL", persist=False, verbose=True)
    print("\n--- Summary ---\n")
    print(txt)
