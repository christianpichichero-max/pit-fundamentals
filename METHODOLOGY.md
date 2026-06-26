# Aboveboard — Methodology

*Point-in-time US equity fundamentals, built honestly from SEC EDGAR.*

A small, honest fundamentals dataset built entirely from free SEC EDGAR filings.
Every value is stamped with the date it *first became public*, so a backtest can only
ever use what was actually knowable at each point in time.

This document exists because, with data, **transparency is the product.** If you can't
see how it was built and validated, you can't trust it — so here's exactly how it's built.

---

## Problem 1 — Lookahead bias (the silent backtest killer)

A company's fiscal year has a *period end* (e.g. Apple's FY2024 ended **2024-09-28**) but
the numbers aren't *public* until the 10-K is filed weeks later (Apple's was filed
**2024-11-01**). A backtest that joins fundamentals on the period-end date is using
information that didn't exist yet — it's peeking into the future.

In this sample, on rows with a reliable filing date, fundamentals became public on
average **41 days after** the period ended (max 60). That's the future-peek a naive
join silently grants you on *every data point*. It makes strategies look better in
testing than they are in life.

**Live example, straight from the data:**

| As of date | Newest AAPL annual revenue you could *honestly* know | Filed |
|---|---|---|
| 2024-10-15 | FY2023 — $383.3B | 2023-11-03 |
| 2024-11-15 | FY2024 — $391.0B | 2024-11-01 |

Same company, one month apart, a different "latest known" number. This dataset encodes
that; a naive one hands you FY2024 too early.

## Problem 2 — Dirty / inconsistent raw data

EDGAR is free but messy: companies tag the same concept under different XBRL labels and
switch them over time (e.g. revenue under `Revenues` in older years, then
`RevenueFromContractWithCustomerExcludingAssessedTax`). A naive pull locks onto whichever
tag it sees first and can return a *stale year* or the *wrong number*. We resolve tags
to the most recent reporting and validate every row (see below).

---

## How it's built

1. **Source** — SEC EDGAR `companyfacts` API (`data.sec.gov`). Public domain, free, no key.
2. **Annual figures** — only `10-K` filings; for flow items (revenue, net income) only
   ~full-year durations (345–385 days) are kept, so quarters and stub periods can't leak in.
3. **Tag resolution** — among candidate XBRL tags for each concept, we choose the one whose
   data extends to the *most recent* period (ties broken by priority). This kills the
   stale-tag bug.
4. **Point-in-time stamping** — `first_filed` = the *earliest* filing that reported a given
   period. That is the first date the number was knowable. `lag_days` = first_filed − period_end.
5. **Restatement detection** — if a later filing revised a period's value by >0.5%, the row is
   marked `restated = True`, and we keep both `original_value` (first knowable) and
   `latest_value` (most recent).
6. **QA + reliability** — every row is checked (filing-lag range, value magnitude). Rows whose
   only available filing is a much-later one (common for the oldest years, where the original
   10-K predates XBRL) are marked `filed_reliable = False` rather than shipped with a
   misleading date.

## Columns

| column | meaning |
|---|---|
| `ticker`, `cik` | company identity |
| `concept` | Revenue / NetIncome / OperatingCashFlow / EPSDiluted / DilutedShares / Assets / StockholdersEquity |
| `xbrl_tag` | the exact SEC tag the value came from (full provenance) |
| `fiscal_year`, `period_end` | the period the value covers |
| `first_filed` | date it first became public (the point-in-time stamp) |
| `lag_days` | first_filed − period_end (the lookahead gap) |
| `filed_reliable` | True if the original 10-K is in XBRL (trust the date) |
| `original_value` | value as first reported |
| `latest_value` | value as most recently reported |
| `restated` | True if later revised >0.5% |
| `qa_status` | `clean` or the specific flag raised |

## This sample's coverage

- 20 large-cap US companies, 7 concepts (revenue, net income, operating cash flow, diluted EPS, diluted shares, assets, equity), up to 12 fiscal years each
- 1,588 point-in-time rows; revenue history depth averages 11.6 years
- 1,503/1,588 rows carry a reliable filing date; 85 oldest-year/edge rows flagged for resolution
- 105 restatements detected

## Known limitations (we mark them, we don't hide them)

- **Oldest-year filing dates**: 85 rows where only a later XBRL filing exists; flagged, not faked.
  (Resolvable by cross-referencing the EDGAR submissions index — on the roadmap.)
- **Annual only** for now; quarterly (10-Q) point-in-time is the next build.
- **Banks/insurers**: "revenue" is an approximate concept for financials; treat JPM-type names with care.
- **20-company sample**: the full US universe is a pipeline run away — gated on demand, not on capability.

The entire pitch is the line above each of these: a clean dataset *tells you what it doesn't know.*
