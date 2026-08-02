"""Fail when the public sample and its trust-sensitive documentation drift apart."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pit_fundamentals_history.csv"


with DATA.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))

tickers = {row["ticker"] for row in rows}
concepts = {row["concept"] for row in rows}
reliable = sum(row["filed_reliable"].strip().lower() == "true" for row in rows)
restated = sum(row["restated"].strip().lower() == "true" for row in rows)
unreliable = len(rows) - reliable

required = {
    ROOT / "README.md": [
        f"{len(tickers)} large-cap US companies",
        f"{len(rows):,} point-in-time rows",
    ],
    ROOT / "METHODOLOGY.md": [
        f"{len(rows):,} point-in-time rows",
        f"{reliable:,}/{len(rows):,} rows carry a reliable filing date",
        f"{restated:,} restatements detected",
        f"{unreliable} rows where only a later XBRL filing exists",
    ],
}

errors: list[str] = []
for document, phrases in required.items():
    text = document.read_text(encoding="utf-8")
    errors.extend(
        f"{document.name} is missing current metric: {phrase!r}"
        for phrase in phrases
        if phrase not in text
    )

if len(concepts) != 7:
    errors.append(f"Expected 7 concepts, found {len(concepts)}")

if errors:
    raise SystemExit("\n".join(errors))

print(
    f"Verified {len(rows):,} rows · {len(tickers)} tickers · {len(concepts)} concepts · "
    f"{reliable:,} reliable dates · {restated:,} restatements"
)
