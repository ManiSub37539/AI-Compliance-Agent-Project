from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from dotenv import load_dotenv

import faiss
import numpy as np
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
DEFAULT_INPUT = ROOT_DIR / "backend" / "data" / "licensing" / "raw_text.jsonl"
DEFAULT_INDEX_DIR = ROOT_DIR / "backend" / "data" / "licensing" / "index"
DEFAULT_INDEX_PATH = DEFAULT_INDEX_DIR / "ri_licensing.faiss"
DEFAULT_METADATA_PATH = DEFAULT_INDEX_DIR / "ri_licensing_meta.json"
DEFAULT_MODEL = "text-embedding-3-small"


def configure_logging(verbose: bool) -> None:
	level = logging.DEBUG if verbose else logging.INFO
	logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def load_chunks(path: Path, max_chunks: int | None = None) -> List[Dict[str, object]]:
	chunks: List[Dict[str, object]] = []
	with open(path, "r", encoding="utf-8") as handle:
		for line_number, line in enumerate(handle, start=1):
			line = line.strip()
			if not line:
				continue
			try:
				payload = json.loads(line)
				chunks.append(payload)
			except json.JSONDecodeError as exc:
				logging.warning("Skipping malformed JSON on line %d: %s", line_number, exc)
				continue

			if max_chunks and len(chunks) >= max_chunks:
				break
	return chunks


def chunk_batches(items: Sequence[str], batch_size: int) -> Iterable[Sequence[str]]:
	for idx in range(0, len(items), batch_size):
		yield items[idx : idx + batch_size]


def embed_texts(texts: Sequence[str], model: str, client: OpenAI) -> List[List[float]]:
	response = client.embeddings.create(model=model, input=list(texts))
	return [item.embedding for item in response.data]


def build_index(vectors: np.ndarray) -> faiss.Index:
	dim = vectors.shape[1]
	index = faiss.IndexFlatL2(dim)
	index.add(vectors)
	return index


def parse_arguments() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Embed RI licensing documents into a FAISS index.")
	parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to raw_text.jsonl file.")
	parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH, help="Output FAISS index path.")
	parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Output metadata JSON path.")
	parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI embedding model name.")
	parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size (default: %(default)s).")
	parser.add_argument("--max-chunks", type=int, help="Optional cap on number of chunks to embed.")
	parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
	return parser.parse_args()


def main() -> int:
	args = parse_arguments()
	configure_logging(args.verbose)

	if not args.input.exists():
		logging.error("Input file %s does not exist", args.input)
		return 1

	chunks = load_chunks(args.input, args.max_chunks)
	if not chunks:
		logging.error("No chunks loaded from %s", args.input)
		return 1

	texts = [chunk["text"] for chunk in chunks]
	client = OpenAI()

	vectors: List[List[float]] = []
	for batch in chunk_batches(texts, args.batch_size):
		embeddings = embed_texts(batch, args.model, client)
		vectors.extend(embeddings)
		logging.info("Embedded %d/%d chunks", len(vectors), len(texts))

	vector_array = np.array(vectors, dtype="float32")

	index = build_index(vector_array)
	args.index.parent.mkdir(parents=True, exist_ok=True)
	faiss.write_index(index, str(args.index))

	args.metadata.parent.mkdir(parents=True, exist_ok=True)
	with open(args.metadata, "w", encoding="utf-8") as handle:
		json.dump(chunks, handle, ensure_ascii=False)

	logging.info("Stored %d embeddings in %s", index.ntotal, args.index)
	logging.info("Wrote metadata to %s", args.metadata)
	return 0


if __name__ == "__main__":
	sys.exit(main())
