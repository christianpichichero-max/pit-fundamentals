# Aboveboard — honest point-in-time US equity fundamentals

*Fundamentals with nothing hidden — no lookahead, no silent restatements.*

A free sample dataset of **point-in-time** US equity fundamentals, built from SEC EDGAR.
Every value is stamped with the date it *first became public* — so you can backtest without
lookahead bias or silently-restated numbers.

## The problem this fixes
A backtest that joins fundamentals on the **period-end** date is using numbers that weren't
public yet (the 10-K files weeks later) — classic **lookahead bias**. In this sample,
fundamentals became public an average of **41 days after** the period ended. That hidden
future-peek inflates every fundamental backtest.

The clean point-in-time vendors (Compustat PIT, FactSet) fix this but run **$10k–50k+/yr** —
out of reach for independent quants and small funds. This is the affordable, honest alternative.

## The free sample
- **20 large-cap US companies · 7 concepts** (Revenue, Net Income, Operating Cash Flow, Diluted EPS, Diluted Shares, Assets, Equity) · up to **12 years**
- **1,588 point-in-time rows** → [`data/pit_fundamentals_history.csv`](data/pit_fundamentals_history.csv)
- Every row carries: `period_end`, `first_filed` (the point-in-time stamp), `lag_days`,
  `original_value` vs `latest_value`, a `restated` flag, and a per-row `qa_status`.

See **[METHODOLOGY.md](METHODOLOGY.md)** for exactly how it's built, validated, and where its
limits are — because with data, showing your work *is* the product.

## Want the full thing?
The **full US universe, quarterly (10-Q) point-in-time history, and extra fields** are in the
works. If clean, affordable, point-in-time fundamentals would be useful to you — or you want a
specific ticker added so you can sanity-check it against your own data — get in touch:

> 📨 **[sign-up / contact link — add before posting]**

Tell me what you'd need it to cover (ratios? segments? international?) and what format you want
(CSV, Parquet, Python API).

## Data
Source data is U.S. SEC EDGAR (public domain). **Aboveboard** is a product of Tradevo Technologies Inc.
