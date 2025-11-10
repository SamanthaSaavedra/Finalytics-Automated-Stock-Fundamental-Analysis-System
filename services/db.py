from pymongo import MongoClient
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

client = MongoClient(os.getenv("MONGODB_URI"))
DB_NAME=os.getenv("DB_NAME")
db = client[DB_NAME]  

DOCS_COLLECTION = os.getenv("DOCS_COLLECTION")
EMB_COLLECTION = os.getenv("EMB_COLLECTION")
ANALYSIS_COLLECTION = os.getenv("ANALYSIS_COLLECTION")

docs_col = db[DOCS_COLLECTION]
emb_col = db[EMB_COLLECTION]