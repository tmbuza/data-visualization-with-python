#!/usr/bin/env python3
"""Validate DVP 17 figure artifacts and update their release status."""

from __future__ import annotations

import csv
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "results/17-publishing-success-rate.metadata.json"
INDEX = ROOT / "results/17-figure-index.csv"
REPORT = ROOT / "results/17-figure-validation.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")
    return struct.unpack(">II", header[16:24])


def main() -> None:
    checks: list[dict[str, object]] = []
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(INDEX.open(newline="", encoding="utf-8")))

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    check("index_rows", len(rows) == 2, f"found {len(rows)} format rows")
    check("alt_text", len(metadata.get("alt_text", "")) >= 40, "alternative text is descriptive")
    for artifact in metadata["artifacts"]:
        path = ROOT / artifact["path"]
        check(f"exists:{artifact['format']}", path.is_file() and path.stat().st_size > 0, artifact["path"])
        check(f"digest:{artifact['format']}", path.is_file() and digest(path) == artifact["sha256"], "SHA-256 matches metadata")
        if artifact["format"] == "png":
            width, height = png_dimensions(path)
            check("png_dimensions", width >= 1000 and height >= 600, f"{width}x{height} pixels")
        elif artifact["format"] == "svg":
            root = ET.parse(path).getroot()
            check("svg_structure", root.tag.endswith("svg"), "SVG root element present")

    passed = all(bool(item["passed"]) for item in checks)
    metadata["validation_status"] = "passed" if passed else "failed"
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": metadata["validation_status"],
        "validated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Figure release validation: {report['status'].upper()} ({len(checks)} checks)")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
