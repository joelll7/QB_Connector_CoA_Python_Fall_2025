"""Utilities for writing JSON reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def write_report(payload: dict[str, Any], output_path: Path) -> Path:
    """Serialise the payload to JSON at output_path.

    The file is encoded as UTF-8 with an indent of two spaces. The payload is
    returned unchanged to ease chaining in higher-level functions.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return output_path


def iso_timestamp() -> str:
    """Return a UTC timestamp suitable for JSON serialisation."""
    return datetime.now(UTC).isoformat()


__all__ = ["write_report", "iso_timestamp"]
