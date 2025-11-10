from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
DB_NAME=os.getenv("DB_NAME")
db = client[DB_NAME]  # SINCE THERE IS NOT .ENV YOU NEED TO ADD IT, THIS IS DONE TO USE LESS API REQUEST FROM THE APY

DOCS_COLLECTION = os.getenv("DOCS_COLLECTION", "rag_documents")
EMB_COLLECTION = os.getenv("EMB_COLLECTION", "rag_embeddings")

docs_col = db[DOCS_COLLECTION]
emb_col = db[EMB_COLLECTION]