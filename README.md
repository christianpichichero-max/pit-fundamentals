# Tradevo Data — honest point-in-time US equity fundamentals

*Fundamentals with nothing hidden — no lookahead, no silent restatements.*

A free sample dataset of **point-in-time** US equity fundamentals, built from SEC EDGAR.
Every value is stamped with the date it *first became public* — so you can backtest without
lookahead bias or silently-restated numbers.

## Run the proof in 3 minutes

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/christianpichichero-max/tradevodata-py/blob/main/examples/lookahead_bias_demo.ipynb)

The notebook joins the same fundamentals two ways at every month-end. The ordinary
period-end join uses a value that was **not public yet in 47 of 413 ticker-months (11%)**.
The point-in-time join removes those future values. No key, signup, or local setup required.

## Or check your own data

That notebook shows the problem on our numbers. This measures it on yours:

```bash
python3 check_your_data.py your_fundamentals.csv
```

Point it at whatever you already backtest on — any CSV with a ticker, a period or fiscal year,
and one value column. It finds the columns itself, needs no dependencies, and sends nothing
anywhere. It separates the two failures because they have different fixes:

- **Timing** — how many days early a period-end join hands you each number. Fixed by joining
  on the filing date.
- **Vintage** — rows where your value is what the company reports *now*, not what it filed at
  the time. This one **survives correct filing-date handling**, because the date is right and
  the number underneath it was rewritten later.

Run against a typical current-values source, it reports things like:

```
2. VINTAGE — values that are today's number, not the one filed at the time
   26 of 475 rows (5.5%) match the CURRENT value but not the as-filed one.

     MRK FY2019: you have 39,121,000,000 · as filed 46,840,000,000 (-16.5%)
     JNJ FY2021: you have 78,740,000,000 · as filed 93,775,000,000 (-16.0%)
     LMT FY2014: you have 39,946,000,000 · as filed 45,600,000,000 (-12.4%)
```

It only compares against the 40 companies in this sample, and it says so — rows outside that
coverage are counted and reported, never quietly dropped. A clean result is evidence about
these 40 names, not proof about your universe.

## Use it in Python

```bash
pip install tradevodata
```
```python
import tradevodata as tv

rows = tv.sample()                            # this sample — no key, no signup
knowable = tv.as_of_filter(rows, "2020-03-31")  # correct point-in-time join
```

`as_of` is a required argument everywhere in that package, so a lookahead-free join is the
only one you can write. The Colab notebook above runs the experiment on this data with zero
setup: it joins both ways at every month-end and finds **47 of 413 ticker-months (11%) where
the naive join uses a number that was not yet public.**

## The problem this fixes
A backtest that joins fundamentals on the **period-end** date is using numbers that weren't
public yet (the 10-K files weeks later) — classic **lookahead bias**. In this sample's
reliable-filing-date rows (3,240 of 3,280), fundamentals became public an average of
**43 days after** the period ended (max 61). That hidden future-peek inflates every
fundamental backtest.

The clean point-in-time vendors (Compustat PIT, FactSet) fix this but run **$10k–50k+/yr** —
out of reach for independent quants and small funds. This is the affordable, honest alternative.

## The free sample
- **40 large-cap US companies · 7 concepts** (Revenue, Net Income, Operating Cash Flow, Diluted EPS, Diluted Shares, Assets, Equity) · up to **12 years**
- **3,280 point-in-time rows** → [`data/pit_fundamentals_history.csv`](data/pit_fundamentals_history.csv)
- Every row carries: `period_end`, `first_filed` (the point-in-time stamp), `lag_days`,
  `original_value` vs `latest_value`, a `restated` flag, and a per-row `qa_status`.

See **[METHODOLOGY.md](METHODOLOGY.md)** for exactly how it's built, validated, and where its
limits are — because with data, showing your work *is* the product.

## Use it — point-in-time queries
`query_asof.py` answers the one question that keeps a backtest honest — *what could I actually
know on date X?*

```bash
python3 query_asof.py AAPL 2024-06-30
```
```
What you could HONESTLY know about AAPL as of 2024-06-30:
  Revenue              $383.3B   (FY2023, filed 2023-11-03)
  NetIncome             $97.0B   (FY2023, filed 2023-11-03)
  OperatingCashFlow    $110.5B   (FY2023, filed 2023-11-03)
  ...  (7 concepts)
```
Run it again as of `2025-01-15` and every line jumps to FY2024 — because that 10-K wasn't filed
until Nov 1, 2024. Same company, months apart, a different *known* reality. That gap is the
lookahead bias this dataset removes.

## Want the full thing?
## Python client

```bash
pip install tradevodata
```

```python
import tradevodata as tv

df = tv.sample()                              # this sample, no key needed
tv.as_of_filter(df, as_of="2020-03-31")       # correct point-in-time join
```

`as_of` is a required argument on every query — there is no way to accidentally ask for
today's numbers. Source: [tradevodata-py](https://github.com/christianpichichero-max/tradevodata-py)

The full US universe is live: **5,000+ companies · 300,000+ point-in-time rows**, served as
a JSON query API with server-side `as_of` semantics — **$49/mo**, key issued instantly,
cancel anytime. The exact totals update with each EDGAR refresh and are published on the
[live status page](https://tradevodata.com/status).

> 🌐 **[tradevodata.com](https://tradevodata.com/?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08)** · docs at
> [tradevodata.com/docs](https://tradevodata.com/docs?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08)

Honest limits, stated up front: annual (10-K/10-K/A) only for now — quarterly (10-Q) is on the
roadmap. Bulk is included in the $49 plan: `GET /v1/download` (full dataset, one gzipped CSV) and
`GET /v1/snapshot?as_of=` (whole-universe cross-section); only the Parquet format is roadmap. If you need quarterly or delisted coverage today, a research-grade
vendor will fit you better; this is the affordable tier for lookahead-safe annual fundamentals.

Waiting on quarterly? [Join the waitlist](https://tradevodata.com/?utm_source=github&utm_medium=repo&utm_campaign=quarterly-waitlist#waitlist) — one email when
10-Q data ships, nothing else.

## Data
Source data is U.S. SEC EDGAR (public domain). **Tradevo Data** is a product of Tradevo Technologies Inc.
