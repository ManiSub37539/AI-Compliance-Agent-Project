from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from guardrail_engine import evaluate_user_prompt


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

INDEX_PATH = ROOT_DIR / "backend" / "data" / "licensing" / "index" / "ri_licensing.faiss"
META_PATH = ROOT_DIR / "backend" / "data" / "licensing" / "index" / "ri_licensing_meta.json"
EMBED_MODEL = "text-embedding-3-small"
ANSWER_MODEL = "gpt-4o-mini"


def _load_index() -> faiss.Index:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing FAISS index at {INDEX_PATH}")
    return faiss.read_index(str(INDEX_PATH))


def _load_metadata() -> List[Dict[str, Any]]:
    if not META_PATH.exists():
        raise FileNotFoundError(f"Missing metadata at {META_PATH}")
    with open(META_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def retrieve_licensing_chunks(query: str, k: int = 3) -> List[Dict[str, Any]]:
    client = OpenAI()
    emb = client.embeddings.create(model=EMBED_MODEL, input=query).data[0].embedding
    vector = np.array([emb], dtype="float32")

    index = _load_index()
    metadata = _load_metadata()
    distances, indices = index.search(vector, k)

    chunks: List[Dict[str, Any]] = []
    for distance, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        source = metadata[idx]
        chunks.append(
            {
                "score": float(distance),
                "file_name": source.get("file_name", "unknown"),
                "page_number": source.get("page_number"),
                "source_url": source.get("source_url"),
                "text": source.get("text", ""),
            }
        )
    return chunks


def _build_context_block(chunks: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        header = f"[{i}] {chunk['file_name']} page {chunk.get('page_number')}"
        lines.append(header)
        lines.append(chunk.get("text", ""))
        lines.append("")
    return "\n".join(lines).strip()


def generate_grounded_answer(user_prompt: str, chunks: List[Dict[str, Any]]) -> str:
    context = _build_context_block(chunks)

    instruction = (
        "You are a Rhode Island licensing research assistant for small businesses. "
        "Use only the provided context snippets. "
        "If the answer is not present, say that clearly and suggest what document type to check next. "
        "Do not provide legal advice. Include a brief disclaimer that this is informational only."
    )

    prompt = f"""
USER QUESTION:
{user_prompt}

RETRIEVED CONTEXT:
{context}

RESPONSE FORMAT:
1) Direct answer in plain language.
2) Bullet list of cited sources with file and page.
3) One-line disclaimer: informational only, not legal advice.
""".strip()

    client = OpenAI()
    response = client.chat.completions.create(
        model=ANSWER_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def handle_licensing_prompt(user_prompt: str, k: int = 3) -> Dict[str, Any]:
    guardrail = evaluate_user_prompt(user_prompt)
    decision = guardrail.get("final_decision", "ALERT")

    result: Dict[str, Any] = {
        "decision": decision,
        "guardrail": guardrail,
        "retrieval": [],
        "answer": None,
        "user_message": None,
    }

    if decision == "BLOCK":
        result["user_message"] = (
            "I cannot process that request because it violates safety policy. "
            "Please remove sensitive data or restricted professional advice requests and try again."
        )
        return result

    if decision == "ALERT":
        result["user_message"] = (
            "Your prompt looks risky or out of scope. "
            "Please rephrase with a focused Rhode Island licensing question and avoid sensitive details."
        )
        return result

    chunks = retrieve_licensing_chunks(user_prompt, k=k)
    result["retrieval"] = chunks

    if not chunks:
        result["user_message"] = (
            "I could not find relevant licensing passages in the index. "
            "Please refine your question or update the document corpus."
        )
        return result

    result["answer"] = generate_grounded_answer(user_prompt, chunks)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full guardrail + licensing retrieval assistant flow.")
    parser.add_argument("query", help="End-user licensing question")
    parser.add_argument("--k", type=int, default=3, help="Top-k chunks to retrieve")
    args = parser.parse_args()

    result = handle_licensing_prompt(args.query, k=args.k)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()