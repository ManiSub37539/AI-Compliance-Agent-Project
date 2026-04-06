import json
from pathlib import Path
from typing import Any, Dict

HISTORY_PATH = Path("memory/history.json")


def save_run(data: Dict[str, Any]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]", encoding="utf-8")

    history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    history.append(data)
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
