import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
PORT = int(os.getenv("PORT", "8000"))
COLLECTION_NAME = "ellie_care_journey"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required — add it to backend/.env")
