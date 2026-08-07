#!/usr/bin/env python3
"""
check_your_data.py — measure how much lookahead is in YOUR fundamentals.

Everything else in this repo shows you our data. This points the question back at yours:
take whatever fundamentals you are already backtesting on, and find out how many of those
values were not public on the date your backtest reads them.

    python3 check_your_data.py mydata.csv

Your CSV needs three columns, named anything sensible — it will find them:
    ticker         AAPL
    period_end     2023-09-30      (or fiscal_year: 2023)
    value          383285000000    (revenue, net income, assets, ... one metric)

Tell it which concept you are comparing if it is not revenue:
    python3 check_your_data.py mydata.csv --concept NetIncome

It reports two separate problems, because they have different fixes:

  1. TIMING — you are reading a value before it was public. A period-end join grants your
     strategy every number weeks early. Fix: join on the filing date.
  2. VINTAGE — your value matches what the company reports NOW, not what it filed then.
     This one survives correct filing-date handling, because the date is right and the
     number underneath it was rewritten later.

Honest limits: this compares against the 40 large caps in the free sample, annual periods
only. Rows outside that coverage are counted and reported separately, never silently dropped.
It cannot tell you about companies we do not cover, and a clean result here is evidence about
these 40 names, not proof about your whole universe.

Stdlib only. Nothing leaves your machine.
"""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import date

SAMPLE = "data/pit_fundamentals_history.csv"

# Header guesses, most specific first so "period_end" wins over a bare "date".
COLUMN_GUESSES = {
    "ticker": ["ticker", "symbol", "sym", "permno_ticker", "act_symbol"],
    "period_end": ["period_end", "period", "date_end", "fiscal_period_end", "datadate", "report_date", "asof", "date"],
    "fiscal_year": ["fiscal_year", "fy", "year", "calendaryear"],
    "value": ["value", "revenue", "revenues", "total_revenue", "sales", "netincome", "net_income", "amount", "val"],
}


def find_column(fieldnames, kind):
    lowered = {f.lower().strip(): f for f in fieldnames}
    for guess in COLUMN_GUESSES[kind]:
        if guess in lowered:
            return lowered[guess]
    return None


def load_sample(concept):
    """{(ticker, fiscal_year): row} for one concept from the shipped sample."""
    try:
        rows = list(csv.DictReader(open(SAMPLE)))
    except FileNotFoundError:
        sys.exit(f"Could not find {SAMPLE}. Run this from the root of the pit-fundamentals repo.")
    out = {}
    for r in rows:
        if r["concept"] != concept:
            continue
        try:
            out[(r["ticker"].upper(), int(r["fiscal_year"]))] = {
                "reliable": r["filed_reliable"] == "True",
                "original": float(r["original_value"]),
                "latest": float(r["latest_value"]),
                "first_filed": r["first_filed"],
                "period_end": r["period_end"],
                "lag_days": int(r["lag_days"]),
                "restated": r["restated"] == "True",
                "qa": r["qa_status"],
            }
        except (ValueError, KeyError):
            continue
    return out


def fiscal_year_of(period_end_str):
    """Same rule the dataset uses: the year the period ENDS, with Jan 1-7 belonging to the
    prior fiscal year so 52/53-week calendars line up."""
    try:
        d = date.fromisoformat(period_end_str.strip()[:10])
    except ValueError:
        return None
    return d.year - (1 if d.month == 1 and d.day <= 7 else 0)


def main():
    ap = argparse.ArgumentParser(description="Measure lookahead bias in your own fundamentals CSV.")
    ap.add_argument("csv_path")
    ap.add_argument("--concept", default="Revenue",
                    help="Revenue, NetIncome, OperatingCashFlow, EPSDiluted, DilutedShares, Assets, StockholdersEquity")
    ap.add_argument("--tolerance", type=float, default=0.005,
                    help="relative difference treated as a match (default 0.5%%)")
    args = ap.parse_args()

    sample = load_sample(args.concept)
    if not sample:
        sys.exit(f"No rows for concept '{args.concept}' in the sample. "
                 f"Valid: Revenue, NetIncome, OperatingCashFlow, EPSDiluted, DilutedShares, Assets, StockholdersEquity")

    try:
        reader = csv.DictReader(open(args.csv_path))
        yours = list(reader)
    except FileNotFoundError:
        sys.exit(f"Could not open {args.csv_path}")
    if not yours:
        sys.exit("That CSV has no rows.")

    fields = reader.fieldnames or []
    c_ticker = find_column(fields, "ticker")
    c_value = find_column(fields, "value")
    c_period = find_column(fields, "period_end")
    c_fy = find_column(fields, "fiscal_year")

    missing = [n for n, c in (("ticker", c_ticker), ("value", c_value)) if not c]
    if missing or not (c_period or c_fy):
        print(f"Could not identify the columns I need in {args.csv_path}.")
        print(f"  found headers: {', '.join(fields)}")
        print(f"  need: a ticker column, a value column, and either period_end or fiscal_year")
        sys.exit(1)

    print(f"Reading {args.csv_path}  ({len(yours)} rows)")
    print(f"  ticker={c_ticker}  value={c_value}  period={c_period or c_fy}  concept={args.concept}\n")

    matched = 0
    uncovered = defaultdict(int)
    vintage_mismatch = []       # your value == today's number, not the as-filed one
    unexplained = []            # matches neither
    lags = []

    for row in yours:
        tkr = (row.get(c_ticker) or "").strip().upper()
        raw = (row.get(c_value) or "").strip().replace(",", "").replace("$", "")
        if not tkr or not raw:
            continue
        try:
            val = float(raw)
        except ValueError:
            continue

        fy = None
        if c_period and row.get(c_period):
            fy = fiscal_year_of(row[c_period])
        if fy is None and c_fy and row.get(c_fy):
            try:
                fy = int(float(row[c_fy]))
            except ValueError:
                fy = None
        if fy is None:
            continue

        ref = sample.get((tkr, fy))
        if not ref:
            uncovered[tkr] += 1
            continue

        matched += 1
        # Only rows whose filing date we can actually stand behind. Including the flagged ones
        # puts a 782-day outlier in the headline, and a number that obviously wrong discredits
        # the accurate ones next to it — the reader stops reading, correctly.
        if ref["reliable"]:
            lags.append(ref["lag_days"])

        def close(a, b):
            return abs(a - b) <= args.tolerance * max(abs(b), 1e-9)

        if close(val, ref["original"]):
            continue                                   # you already hold the as-filed value
        if close(val, ref["latest"]):
            vintage_mismatch.append((tkr, fy, val, ref))
        else:
            unexplained.append((tkr, fy, val, ref))

    if not matched:
        print("None of your rows overlap the 40 companies and annual periods in this sample.")
        print("That is not a clean bill of health — it means this check could not see your data.")
        if uncovered:
            print(f"  {sum(uncovered.values())} rows across {len(uncovered)} tickers were outside coverage.")
        return

    print("=" * 64)
    print(f"CHECKED {matched} of your rows against the as-filed record")
    print("=" * 64)

    # --- 1. timing ---
    if lags:
        lags.sort()
        mean_lag = sum(lags) / len(lags)
        p90 = lags[min(len(lags) - 1, int(len(lags) * 0.9))]
        print(f"\n1. TIMING — how early a period-end join would hand you these numbers")
        print(f"   Mean gap between period end and the filing that first disclosed it: "
              f"{mean_lag:.0f} days (median {lags[len(lags)//2]}, 90th percentile {p90}).")
        print(f"   If your backtest keys these rows on period end, every one of them arrives")
        print(f"   about {mean_lag:.0f} days before the market had it.")
        print(f"   (Measured on the {len(lags)} matched rows with a filing date we can verify.)")
    else:
        mean_lag = 0

    # --- 2. vintage ---
    n_v = len(vintage_mismatch)
    print(f"\n2. VINTAGE — values that are today's number, not the one filed at the time")
    if n_v:
        pct = 100.0 * n_v / matched
        print(f"   {n_v} of {matched} rows ({pct:.1f}%) match the CURRENT value but not the")
        print(f"   as-filed one. Correct filing-date handling does not fix these — the date is")
        print(f"   right and the number was rewritten afterwards.\n")
        vintage_mismatch.sort(key=lambda x: abs(x[2] - x[3]["original"]) / max(abs(x[3]["original"]), 1), reverse=True)
        for tkr, fy, val, ref in vintage_mismatch[:8]:
            drift = (val - ref["original"]) / abs(ref["original"]) * 100 if ref["original"] else float("inf")
            print(f"     {tkr} FY{fy}: you have {val:,.0f} · as filed {ref['original']:,.0f} "
                  f"({drift:+.1f}%)")
        if n_v > 8:
            print(f"     ... and {n_v - 8} more")
    else:
        print(f"   None. Every matched row already holds the as-filed value — your source is")
        print(f"   vintaged correctly for these companies.")

    if unexplained:
        print(f"\n3. NEITHER — {len(unexplained)} rows match neither the as-filed nor the current value")
        print(f"   Could be a different definition, units, or a genuine discrepancy. Worth a look:")
        for tkr, fy, val, ref in unexplained[:5]:
            print(f"     {tkr} FY{fy}: you have {val:,.0f} · as filed {ref['original']:,.0f} "
                  f"· today {ref['latest']:,.0f}")

    if uncovered:
        # The one moment a user feels this sample's limit rather than reading about it: they
        # ran the tool on their own file and most of it came back unchecked. Saying only "not
        # checked" leaves them thinking the tool is weak, when the honest answer is that the
        # coverage is deliberately small and a wider one exists. Stated as a fact with the
        # proportion, not as a pitch.
        n_rows = sum(uncovered.values())
        pct = 100.0 * n_rows / (n_rows + matched)
        print(f"\nNot checked: {n_rows} rows across {len(uncovered)} tickers outside this "
              f"sample's 40 companies")
        print(f"  — {pct:.0f}% of your file. This sample is 40 large caps by design; the full "
              f"set covers")
        print(f"  5,000+ US companies with the same first_filed / original_value columns "
              f"(tradevodata.com).")
        print(f"  Everything above was measured only on the {matched} rows that overlap.")

    print(f"\n{'-' * 64}")
    if n_v:
        print(f"The vintage rows are the ones worth caring about. They are invisible to every")
        print(f"check that only looks at dates, and they make a backtest look better than it was.")
    print(f"Full universe ({args.concept} and six other concepts, 5,000+ US companies) with")
    print(f"first_filed and original_value on every row: https://tradevodata.com")
    print()
    # The one place a user of this tool has just seen a concrete, personal result. If they are
    # ever going to say something, it is here — not on a landing page.
    print(f"Built by one person. If this found something in your data, I'd like to hear what:")
    print(f"christianpichichero@gmail.com — one line is plenty, and I reply.")
    print(f"Not investment advice.")


if __name__ == "__main__":
    main()
