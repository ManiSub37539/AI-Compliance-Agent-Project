from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT_DIR / "Licensing_Docs"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "backend" / "data" / "licensing"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "raw_text.jsonl"


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def load_source_map(path: Optional[Path]) -> Dict[str, str]:
    if not path:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Missing source map file: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def clean_text(raw: str) -> str:
    return " ".join(raw.split())


def extract_pdf(pdf_path: Path, min_chars: int) -> Iterator[Dict[str, object]]:
    reader = PdfReader(str(pdf_path))
    for page_idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = clean_text(text)
        if len(cleaned) < min_chars:
            continue
        yield {
            "file_name": pdf_path.name,
            "page_number": page_idx,
            "char_count": len(cleaned),
            "text": cleaned,
        }


def ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from Rhode Island licensing PDFs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing source PDFs (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="JSONL file to write cleaned text chunks (default: %(default)s)",
    )
    parser.add_argument(
        "--source-map",
        type=Path,
        help="Optional JSON file mapping PDF file names to source URLs.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Drop page snippets shorter than this length (default: %(default)s characters)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    configure_logging(args.verbose)

    if not args.input_dir.exists():
        logging.error("Input directory %s does not exist", args.input_dir)
        return 1

    source_map = load_source_map(args.source_map)
    pdf_files: List[Path] = sorted(args.input_dir.glob("*.pdf"))

    if not pdf_files:
        logging.error("No PDF files found in %s", args.input_dir)
        return 1

    ensure_output_dir(args.output)

    written = 0
    with open(args.output, "w", encoding="utf-8") as handle:
        for pdf_path in pdf_files:
            logging.info("Processing %s", pdf_path.name)
            try:
                for chunk in extract_pdf(pdf_path, args.min_chars):
                    chunk["source_url"] = source_map.get(pdf_path.name)
                    handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    written += 1
            except Exception as exc:  # pragma: no cover
                logging.exception("Failed to process %s: %s", pdf_path.name, exc)

    logging.info("Wrote %d chunks to %s", written, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())