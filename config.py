import os
from dotenv import load_dotenv

load_dotenv()

MODE = os.getenv("MODE", "local").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("MODEL", "gpt-5").strip()
DATA_PATH = os.getenv("DATA_PATH", "data/sample_data.csv").strip()

if MODE not in {"local", "openai"}:
    raise ValueError("MODE must be either 'local' or 'openai'.")
