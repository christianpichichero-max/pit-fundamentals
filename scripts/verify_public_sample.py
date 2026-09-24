"""Fail when the public sample and its trust-sensitive documentation drift apart."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pit_fundamentals_history.csv"
EXPECTED_CONCEPTS = {
    "Assets",
    "CapitalExpenditures",
    "CashAndCashEquivalents",
    "CurrentAssets",
    "CurrentLiabilities",
    "DilutedShares",
    "EPSDiluted",
    "GrossProfit",
    "IncomeTaxExpense",
    "NetIncome",
    "NetPPE",
    "OperatingCashFlow",
    "OperatingIncome",
    "PretaxIncome",
    "Revenue",
    "StockholdersEquity",
}
EXPECTED_HEADERS = [
    "ticker",
    "cik",
    "concept",
    "xbrl_tag",
    "fiscal_year",
    "period_end",
    "first_filed",
    "lag_days",
    "filed_reliable",
    "original_value",
    "latest_value",
    "restated",
    "qa_status",
]
EXPECTED_ROWS = 225
EXPECTED_TICKERS = 5
EXPECTED_RELIABLE = 224
EXPECTED_RESTATEMENTS = 17
EXPECTED_RELIABLE_MEAN_LAG = 35.2
EXPECTED_RELIABLE_MAX_LAG = 48
EXPECTED_TICKER_SET = {"AAPL", "HON", "NFLX", "NVDA", "WMT"}
EXPECTED_MAX_YEARS_PER_TICKER = 3


with DATA.open(newline="", encoding="utf-8-sig") as handle:
    reader = csv.DictReader(handle)
    headers = reader.fieldnames
    rows = list(reader)

tickers = {row["ticker"] for row in rows}
concepts = {row["concept"] for row in rows}
reliable = sum(row["filed_reliable"].strip().lower() == "true" for row in rows)
restated = sum(row["restated"].strip().lower() == "true" for row in rows)
unreliable = len(rows) - reliable

required = {
    ROOT / "README.md": [
        f"{len(tickers)} recognizable US companies",
        f"{len(rows):,} point-in-time rows",
    ],
    ROOT / "METHODOLOGY.md": [
        f"{len(rows):,} point-in-time rows",
        f"{reliable:,}/{len(rows):,} rows carry a reliable filing date",
        f"{restated:,} restatements detected",
        f"{unreliable} row{'s' if unreliable != 1 else ''} where only a later XBRL filing exists",
    ],
}

errors: list[str] = []
if headers != EXPECTED_HEADERS:
    errors.append(f"Schema mismatch: expected={EXPECTED_HEADERS}, got={headers}")
if len(rows) != EXPECTED_ROWS:
    errors.append(f"Row-count mismatch: expected={EXPECTED_ROWS:,}, got={len(rows):,}")
if len(tickers) != EXPECTED_TICKERS:
    errors.append(f"Ticker-count mismatch: expected={EXPECTED_TICKERS}, got={len(tickers)}")
if tickers != EXPECTED_TICKER_SET:
    errors.append(f"Ticker-set mismatch: expected={sorted(EXPECTED_TICKER_SET)}, got={sorted(tickers)}")
for ticker in sorted(tickers):
    years = {int(row["fiscal_year"]) for row in rows if row["ticker"] == ticker}
    if len(years) > EXPECTED_MAX_YEARS_PER_TICKER:
        errors.append(f"{ticker} has {len(years)} fiscal years; maximum is {EXPECTED_MAX_YEARS_PER_TICKER}")
if reliable != EXPECTED_RELIABLE:
    errors.append(f"Reliable-date mismatch: expected={EXPECTED_RELIABLE:,}, got={reliable:,}")
if restated != EXPECTED_RESTATEMENTS:
    errors.append(f"Restatement mismatch: expected={EXPECTED_RESTATEMENTS:,}, got={restated:,}")

seen: set[tuple[str, str, int]] = set()
reliable_lags: list[int] = []
for line_number, row in enumerate(rows, start=2):
    try:
        key = (row["ticker"], row["concept"], int(row["fiscal_year"]))
        if key in seen:
            errors.append(f"line {line_number}: duplicate ticker/concept/fiscal-year key {key}")
        seen.add(key)

        if not row["ticker"] or not row["cik"].isdigit() or not row["xbrl_tag"]:
            errors.append(f"line {line_number}: missing ticker, numeric CIK, or XBRL tag")
        if row["filed_reliable"] not in {"True", "False"}:
            errors.append(f"line {line_number}: invalid filed_reliable={row['filed_reliable']!r}")
        if row["restated"] not in {"True", "False"}:
            errors.append(f"line {line_number}: invalid restated={row['restated']!r}")

        period_end = date.fromisoformat(row["period_end"])
        first_filed = date.fromisoformat(row["first_filed"])
        lag = int(row["lag_days"])
        float(row["original_value"])
        float(row["latest_value"])
        if lag != (first_filed - period_end).days:
            errors.append(
                f"line {line_number}: lag_days={lag} but date difference is "
                f"{(first_filed - period_end).days}"
            )
        if row["filed_reliable"] == "True":
            reliable_lags.append(lag)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"line {line_number}: invalid typed field ({exc})")

if reliable_lags:
    mean_lag = round(sum(reliable_lags) / len(reliable_lags), 1)
    max_lag = max(reliable_lags)
    if mean_lag != EXPECTED_RELIABLE_MEAN_LAG:
        errors.append(
            f"Reliable mean-lag mismatch: expected={EXPECTED_RELIABLE_MEAN_LAG}, got={mean_lag}"
        )
    if max_lag != EXPECTED_RELIABLE_MAX_LAG:
        errors.append(
            f"Reliable max-lag mismatch: expected={EXPECTED_RELIABLE_MAX_LAG}, got={max_lag}"
        )

for document, phrases in required.items():
    text = document.read_text(encoding="utf-8")
    errors.extend(
        f"{document.name} is missing current metric: {phrase!r}"
        for phrase in phrases
        if phrase not in text
    )

if concepts != EXPECTED_CONCEPTS:
    errors.append(
        "Concept contract mismatch: "
        f"missing={sorted(EXPECTED_CONCEPTS - concepts)}, "
        f"unexpected={sorted(concepts - EXPECTED_CONCEPTS)}"
    )

if errors:
    raise SystemExit("\n".join(errors))

print(
    f"Verified {len(rows):,} rows · {len(tickers)} tickers · {len(concepts)} concepts · "
    f"{reliable:,} reliable dates · {restated:,} restatements"
)
