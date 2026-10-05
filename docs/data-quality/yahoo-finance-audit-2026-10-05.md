# Yahoo Finance OHLCV Quality Audit

**Audit date:** 2026-10-05
**Provider:** Yahoo Finance via `yfinance`
**Scope:** 25 NSE symbols across all eight application history ranges

## 1. Objective

Evaluate the internal consistency of raw OHLCV observations returned
by Yahoo Finance before the application's historical-price provider
filters invalid candles.

This is a one-time data-quality audit. It is not an independent
verification of prices against official NSE or BSE records.

## 2. Coverage

- Companies sampled: 25
- History ranges: 1D, 5D, 1M, 6M, YTD, 1Y, 5Y, MAX
- Company/range checks: 200
- Raw observations inspected: 39,300
- Request pause: 2 seconds between completed requests
- Maximum attempts per request: 3

The audit completed all 200 planned company/range checks.
The summary reported 195 `OK` checks and 5 `ISSUES` checks,
with no `EMPTY` or `ERROR` results.

## 3. Results

| Measure | Result |
|---|---:|
| Company/range checks | 200 |
| Checks with no detected issues | 195 |
| Checks flagged with issues | 5 |
| Raw observations | 39,300 |
| Invalid OHLC candles | 6 |
| Missing OHLC values in flagged checks | 0 |
| Non-numeric or non-finite OHLC values | 0 |
| Non-positive OHLC values | 0 |
| Duplicate timestamp rows in flagged checks | 0 |
| Missing volume rows in flagged checks | 0 |
| Negative volume rows in flagged checks | 0 |

## 4. Flagged observations

All five flagged company/range checks were in the `MAX` range.
The six invalid candles were:

| Symbol | Timestamp | Violation |
|---|---|---|
| INFY | 1996-06-01 | Open below Low |
| HDFCBANK | 1996-02-01 | Open below Low |
| ITC | 1996-02-01 | Open below Low |
| SUNPHARMA | 1996-01-01 | Open above High |
| SUNPHARMA | 1996-02-01 | Open below Low |
| TATACONSUM | 1996-02-01 | Open below Low |

Expected OHLC relationships are:

- `Low <= Open <= High`
- `Low <= Close <= High`

The recorded values and issue flags are available in the raw-bar audit CSV.

## 5. Interpretation and limitations

The detected anomalies are isolated to very old monthly observations
from early 1996. This distribution suggests a historical-data anomaly,
but the audit does not establish its cause.

The audit measures internal consistency only. It does not prove that
prices match official exchange records, that every expected observation
is present, or that intraday data is real-time.

The `1D` audit request uses a five-day, five-minute Yahoo Finance
window. Its raw observation count therefore represents the wider
intraday response, not necessarily the single-session subset shown
by the application chart.

The results are a snapshot of the provider response at the audit time.
Yahoo Finance data can change or become unavailable.

## 6. Application behavior

The market-data provider skips individual candles with missing,
non-finite, non-positive, or inconsistent OHLC prices rather than
failing the entire historical response because of a bad candle.

Invalid prices must not be repaired by inventing replacement values.
The regression test in
`backend/tests/test_yahoo_finance_ohlc_validation.py` verifies
that invalid candles are skipped while valid candles are retained.

## 7. Reports

The audit reports were written outside the repository to:

`C:\Users\ASUS\Desktop\indian_stock_explorer_yfinance_audit`

Summary CSV:

`yfinance_audit_summary_20261005_032052.csv`

Raw observations CSV:

`yfinance_raw_bars_20261005_032052.csv`

Metadata JSON:

`yfinance_audit_metadata_20261005_032052.json`

These generated reports are intentionally not committed as source
code artifacts; this document preserves the key findings.
