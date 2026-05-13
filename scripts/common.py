"""Shared utilities for the digest-technical-paper pipeline."""
from __future__ import annotations

import json
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Any


def setup_logging(out_dir: Path) -> logging.Logger:
    """Configure root logger to write to stdout AND debug/run.log."""
    log_path = out_dir / "debug" / "run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Suppress noisy library logs
    for noisy in ("docling", "transformers", "huggingface_hub", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.ERROR)

    return logging.getLogger("digest")


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    """Write JSON with 2-space indent, trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.rename(path)


def read_json(path: Path) -> Any:
    """Read JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
