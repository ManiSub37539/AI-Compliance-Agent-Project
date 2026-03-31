from pathlib import Path
import json
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
INDEX = ROOT / "backend" / "data" / "licensing" / "index" / "ri_licensing.faiss"
META = ROOT / "backend" / "data" / "licensing" / "index" / "ri_licensing_meta.json"

def main(query: str, k: int = 3) -> None:
    client = OpenAI()
    emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    vector = np.array([emb], dtype="float32")

    index = faiss.read_index(str(INDEX))
    distances, indices = index.search(vector, k)

    with open(META, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), start=1):
        chunk = metadata[idx]
        print(f"#{rank} (score={dist:.4f}) {chunk['file_name']} p.{chunk['page_number']}")
        print(chunk["text"][:400] + "…\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Query text, e.g., 'How do I register a mobile food truck in Tiverton?'")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    main(args.query, args.k)