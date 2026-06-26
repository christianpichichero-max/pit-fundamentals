#!/usr/bin/env python3
"""
query_asof.py — point-in-time query helper for the Aboveboard sample dataset.

Answers the only question that makes a fundamental backtest honest:
"What did I ACTUALLY KNOW about this company as of date X?"

It returns, for each concept, the most recent value that had already been *filed*
(made public) on or before your as-of date — so you never trade on data that
didn't exist yet.

Usage:
  python3 query_asof.py AAPL 2024-06-30
  python3 query_asof.py MSFT 2020-01-15 Revenue
"""
import csv
import os
import sys

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pit_fundamentals_history.csv")


def load():
    with open(CSV) as f:
        return list(csv.DictReader(f))


def as_of(rows, ticker, as_of_date, concept=None, reliable_only=True):
    """Latest value per concept that was publicly known on/before as_of_date (ISO date string)."""
    ticker = ticker.upper()
    out = {}
    for r in rows:
        if r["ticker"] != ticker:
            continue
        if concept and r["concept"] != concept:
            continue
        if reliable_only and r["filed_reliable"] != "True":
            continue
        if r["first_filed"] > as_of_date:        # wasn't public yet as of the date
            continue
        c = r["concept"]
        if c not in out or r["period_end"] > out[c]["period_end"]:
            out[c] = r                            # keep the most recent knowable period
    return out


def fmt(concept, r):
    v = float(r["original_value"])
    if concept == "EPSDiluted":
        val = f"${v:,.2f}/sh"
    elif concept == "DilutedShares":
        val = f"{v/1e9:,.2f}B sh"
    else:
        val = f"${v/1e9:,.1f}B"
    note = "  [later restated]" if r["restated"] == "True" else ""
    return f"  {concept:<20}{val:>16}   (FY{r['fiscal_year']}, filed {r['first_filed']}){note}"


def main():
    if len(sys.argv) < 3:
        print("usage: python3 query_asof.py TICKER YYYY-MM-DD [Concept]")
        return
    ticker, as_of_date = sys.argv[1], sys.argv[2]
    concept = sys.argv[3] if len(sys.argv) > 3 else None
    res = as_of(load(), ticker, as_of_date, concept)
    if not res:
        print(f"No data knowable for {ticker.upper()} as of {as_of_date} "
              f"(check the ticker is in the sample and the date isn't before its history).")
        return
    print(f"\nWhat you could HONESTLY know about {ticker.upper()} as of {as_of_date}:\n")
    for c in sorted(res):
        print(fmt(c, res[c]))
    print()


if __name__ == "__main__":
    main()
