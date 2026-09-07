# Tradevo Data — honest point-in-time US equity fundamentals

*Fundamentals with filed-date stamps, so a backtest only sees what was public — and restatements are flagged, not silently applied.*

A free sample dataset of **point-in-time** US equity fundamentals, built from SEC EDGAR.
Every value is stamped with the date it *first became public* (`first_filed`), so a join that
filters by `first_filed <= as_of` only sees what was knowable on that date — and later
revisions are kept alongside the original number with a `restated` flag rather than silently
overwriting it.

> **Using this? I'd genuinely like to know what for.**
> I'm one person, and GitHub tells me this repo gets cloned but not by whom — so unless you say
> something, I'm building in the dark. What are you testing it against? What's missing that
> would make it useful? One line to **christianpichichero@gmail.com**, or
> [open an issue](https://github.com/christianpichichero-max/pit-fundamentals/issues/new),
> and I'll read it and reply.
>
> No signup, no list, nothing gated. The data is CC0 whether you answer or not.

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

`as_of` is a required argument everywhere in that package, so every join you write filters by
`first_filed <= as_of` — there is no way to ask it for today's numbers by accident. The Colab notebook above runs the experiment on this data with zero
setup: it joins both ways at every month-end and finds **47 of 413 ticker-months (11%) where
the naive join uses a number that was not yet public.**

## The problem this fixes
A backtest that joins fundamentals on the **period-end** date is using numbers that weren't
public yet (the 10-K files weeks later) — classic **lookahead bias**. In this sample's
reliable-filing-date rows (6,823 of 6,969), fundamentals became public an average of
**43 days after** the period ended (max 61). That hidden future-peek inflates every
fundamental backtest.

Point-in-time products exist at the institutional vendors —
[S&P Global's Compustat](https://www.spglobal.com/market-intelligence/) and
[FactSet](https://www.factset.com/) among them — but their pricing is quote-based and aimed at
funds with a data budget; check their sites for current terms. This is the small-budget tier
for lookahead-safe annual fundamentals: a free CC0 sample here, and a $29/mo API for the full
universe (details below).

## The free sample
Figures below were measured on the CSV in this repo (last rebuilt 2026-09-07):

- **40 large-cap US companies · 16 concepts** (Revenue, Net Income, Assets, Equity, Operating Cash Flow, Diluted EPS, Diluted Shares, Gross Profit, Operating Income, Pretax Income, Income Tax Expense, Capital Expenditures, Cash and Cash Equivalents, Current Assets, Current Liabilities, and Net PP&E) · revenue history runs **about 12 years** per company, measured on the sample (475 revenue rows across 40 companies)
- **6,969 point-in-time rows** → [`data/pit_fundamentals_history.csv`](data/pit_fundamentals_history.csv)
- Browse it, and the API it previews, on the [sample page](https://tradevodata.com/sample?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08&utm_content=readme-sample)
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
  ...  (16 concepts)
```
Run it again as of `2025-01-15` and every line jumps to FY2024 — because that 10-K wasn't filed
until Nov 1, 2024. Same company, months apart, a different *known* reality. That gap is the
lookahead the `first_filed` stamp lets you filter out.

## Want the full universe?

The full US universe is live: **5,189 companies · 312,751 point-in-time rows · 18,723 flagged
restatements** as of the 2026-07-23 load, served as a JSON query API with server-side `as_of`
semantics — **$29/mo**, key issued instantly, cancel anytime. Totals move with each EDGAR
refresh; the current ones are on the
[live status page](https://tradevodata.com/status?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08).

The same `tradevodata` package above talks to the API — `Client(api_key=...).fundamentals("AAPL", as_of="2024-06-30")` —
with `as_of` required on every query. Source: [tradevodata-py](https://github.com/christianpichichero-max/tradevodata-py).

> 🌐 **[tradevodata.com](https://tradevodata.com/?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08)** ·
> [sample page](https://tradevodata.com/sample?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08&utm_content=readme-sample) ·
> [docs](https://tradevodata.com/docs?utm_source=github&utm_medium=repo&utm_campaign=pit-proof-2026-08)

Honest limits, stated up front: annual (10-K/10-K/A) only for now — quarterly (10-Q) is on the
roadmap. Bulk is included in the $29 plan: `GET /v1/download` (full dataset, one gzipped CSV) and
`GET /v1/snapshot?as_of=` (whole-universe cross-section); only the Parquet format is roadmap.
Across the full universe, filing lag on reliable rows is mean 66 / median 60 / 90th percentile
90 days (rows are QA-capped at 120), measured 2026-07-23. If you need quarterly or delisted
coverage today, a research-grade vendor will fit you better; this is the small-budget tier for
lookahead-safe annual fundamentals.

Waiting on quarterly? [Join the waitlist](https://tradevodata.com/?utm_source=github&utm_medium=repo&utm_campaign=quarterly-waitlist#waitlist) — one email when
10-Q data ships, nothing else.

## Data
Source data is U.S. SEC EDGAR (public domain). **Tradevo Data** is a product of Tradevo Technologies Inc.
