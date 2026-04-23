import os
from dotenv import load_dotenv

load_dotenv()

MODE = os.getenv("MODE", "local").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", os.getenv("MODEL", "gpt-5")).strip()
DATA_PATH = os.getenv("DATA_PATH", "data/sample_data.csv").strip()

if MODE not in {"local", "openai"}:
    raise ValueError("MODE must be one of: 'local' or 'openai'.")

if MODE == "openai":
    MODEL = OPENAI_MODEL
else:
    MODEL = "local-rule-based"
