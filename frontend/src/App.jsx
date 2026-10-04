import { useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

const QUICK_SEARCHES = [
  { symbol: 'RELIANCE', name: 'Reliance Industries' },
  { symbol: 'TCS', name: 'Tata Consultancy Services' },
  { symbol: 'INFY', name: 'Infosys' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank' },
]

async function apiGet(path) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`)
  } catch {
    throw new Error('Cannot reach FastAPI. Check that the backend is running.')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || 'Invalid request').join(', ')
          : `Request failed (${response.status})`

    throw new Error(message)
  }

  return data
}

function money(value, currency = 'INR') {
  if (value == null || !Number.isFinite(Number(value))) return '—'

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

function number(value, digits = 2) {
  if (value == null || !Number.isFinite(Number(value))) return '—'
  return Number(value).toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function dateLabel(value) {
  if (!value) return 'Timestamp unavailable'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Timestamp unavailable'

  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  })
}

function StateBadge({ value }) {
  const status = String(value || 'UNKNOWN').toUpperCase()
  const kind =
    status === 'LISTED' || status === 'RESOLVED'
      ? 'good'
      : status === 'AMBIGUOUS' || status === 'UNVERIFIED'
        ? 'warning'
        : 'neutral'

  return <span className={`state-badge ${kind}`}>{status.replaceAll('_', ' ')}</span>
}

function QuoteStatus({ quote }) {
  const freshness = String(quote?.freshness || 'unknown').toLowerCase()

  return (
    <span className={`quote-status ${freshness}`}>
      <span className="status-dot" />
      {freshness === 'fresh'
        ? 'Fresh'
        : freshness === 'stale'
          ? 'Potentially stale'
          : 'Freshness unknown'}
    </span>
  )
}

function QuoteCard({ listing, quote }) {
  return (
    <article className="quote-card">
      <div className="quote-card-heading">
        <div>
          <div className="micro-label">EXCHANGE LISTING</div>
          <h3>{listing.symbol}</h3>
        </div>
        <span className="exchange-tag">{listing.exchange}</span>
      </div>

      <p className="listing-name">{listing.company_name}</p>

      {listing.isin && (
        <p className="isin">ISIN · {listing.isin}</p>
      )}

      {quote ? (
        <>
          <div className="quote-card-divider" />

          <div className="quote-status-row">
            <span className="micro-label">LATEST AVAILABLE CLOSE</span>
            <QuoteStatus quote={quote} />
          </div>

          <div className="price">{money(quote.price, quote.currency)}</div>

          <div
            className={`price-change ${
              Number(quote.change) >= 0 ? 'up' : 'down'
            }`}
          >
            {Number(quote.change) > 0 ? '+' : ''}
            {money(quote.change, quote.currency)}
            {quote.change_percent != null &&
              ` (${Number(quote.change_percent) > 0 ? '+' : ''}${number(quote.change_percent)}%)`}
          </div>

          <div className="data-row">
            <span>Previous close</span>
            <strong>{money(quote.previous_close, quote.currency)}</strong>
          </div>

          <div className="data-row">
            <span>Quote time</span>
            <strong>{dateLabel(quote.as_of || quote.timestamp)}</strong>
          </div>

          <div className="quote-source">
            Source: {quote.source || 'Not supplied'}
          </div>
        </>
      ) : (
        <div className="quote-missing">
          <span className="status-dot muted" />
          <div>
            <strong>Quote unavailable</strong>
            <p>No quote was returned for this listing.</p>
          </div>
        </div>
      )}
    </article>
  )
}

function CloseComparison({ quote }) {
  if (!quote) {
    return (
      <section className="panel chart-panel">
        <div className="panel-heading">
          <div>
            <div className="micro-label">PRICE CONTEXT</div>
            <h3>Close comparison</h3>
          </div>
        </div>
        <div className="empty-chart">
          Select a company with an available quote to view the close comparison.
        </div>
      </section>
    )
  }

  const previous = Number(quote.previous_close)
  const current = Number(quote.price)

  if (
    !Number.isFinite(previous) ||
    !Number.isFinite(current) ||
    previous <= 0 ||
    current <= 0
  ) {
    return null
  }

  const low = Math.min(previous, current)
  const high = Math.max(previous, current)
  const spread = Math.max(high - low, high * 0.005, 0.01)
  const y = (value) => 111 - ((value - low) / spread) * 62
  const firstY = y(previous)
  const lastY = y(current)
  const trend = current >= previous

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <div className="micro-label">PRICE CONTEXT</div>
          <h3>Close comparison</h3>
          <p>Previous close compared with latest available close</p>
        </div>
        <span className={`trend-pill ${trend ? 'up' : 'down'}`}>
          {trend ? '↗' : '↘'} {number(quote.change_percent)}%
        </span>
      </div>

      <div className="comparison-chart">
        <svg
          viewBox="0 0 700 155"
          role="img"
          aria-label={`Previous close ${money(previous, quote.currency)}, latest close ${money(current, quote.currency)}`}
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="price-area" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor={trend ? '#27c78a' : '#ff6376'}
                stopOpacity="0.24"
              />
              <stop
                offset="100%"
                stopColor={trend ? '#27c78a' : '#ff6376'}
                stopOpacity="0"
              />
            </linearGradient>
          </defs>

          {[35, 75, 115].map((line) => (
            <line
              key={line}
              x1="25"
              x2="675"
              y1={line}
              y2={line}
              stroke="currentColor"
              strokeOpacity="0.11"
              strokeDasharray="4 5"
            />
          ))}

          <path
            d={`M 35 ${firstY} L 665 ${lastY} L 665 136 L 35 136 Z`}
            fill="url(#price-area)"
          />

          <path
            d={`M 35 ${firstY} L 665 ${lastY}`}
            fill="none"
            stroke={trend ? '#27c78a' : '#ff6376'}
            strokeWidth="2.5"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />

          <circle
            cx="35"
            cy={firstY}
            r="4"
            fill="#9ca3af"
            vectorEffect="non-scaling-stroke"
          />
          <circle
            cx="665"
            cy={lastY}
            r="5"
            fill={trend ? '#27c78a' : '#ff6376'}
            vectorEffect="non-scaling-stroke"
          />
        </svg>

        <div className="chart-axis">
          <div>
            <span>Previous close</span>
            <strong>{money(previous, quote.currency)}</strong>
          </div>
          <div className="axis-end">
            <span>Latest available close</span>
            <strong>{money(current, quote.currency)}</strong>
          </div>
        </div>
      </div>

      <p className="chart-disclaimer">
        Two observed closing values only. This is not an intraday or historical
        price chart.
      </p>
    </section>
  )
}

function App() {
  const [query, setQuery] = useState('')
  const [searchedQuery, setSearchedQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [overview, setOverview] = useState(null)
  const [research, setResearch] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [quoteError, setQuoteError] = useState('')
  const [lastSearches, setLastSearches] = useState([])

  async function runSearch(rawQuery) {
    const term = rawQuery.trim()

    if (!term) {
      setError('Enter a company name or ticker symbol.')
      return
    }

    setQuery(term)
    setSearchedQuery(term)
    setLoading(true)
    setError('')
    setQuoteError('')
    setSearchResult(null)
    setOverview(null)
    setResearch(null)

    setLastSearches((items) =>
      [term, ...items.filter((item) => item.toLowerCase() !== term.toLowerCase())].slice(
        0,
        5,
      ),
    )

    try {
      const q = encodeURIComponent(term)

      const [searchData, overviewData] = await Promise.all([
        apiGet(`/api/v1/companies/search?q=${q}`),
        apiGet(`/api/v1/companies/overview?q=${q}`),
      ])

      setSearchResult(searchData)
      setOverview(overviewData)

      if (String(searchData.resolution_status).toUpperCase() === 'RESOLVED') {
        try {
          setResearch(await apiGet(`/api/v1/companies/research?q=${q}`))
        } catch (researchFailure) {
          setQuoteError(researchFailure.message)
        }
      }
    } catch (requestFailure) {
      setError(requestFailure.message)
    } finally {
      setLoading(false)
    }
  }

  function submitSearch(event) {
    event.preventDefault()
    runSearch(query)
  }

  const resolution = String(searchResult?.resolution_status || '').toUpperCase()
  const isAmbiguous = resolution === 'AMBIGUOUS'
  const isNotFound = resolution === 'NOT_FOUND'

  const listings =
    research?.listings ||
    (overview?.listings || []).map((listing) => ({ listing, quote: null }))

  const primaryQuote =
    listings.find((item) => item.quote?.exchange === 'NSE' && item.quote)?.quote ||
    listings.find((item) => item.quote)?.quote ||
    null

  const companyName =
    research?.company_name || overview?.company_name || searchedQuery

  return (
    <div className="finance-app">
      <aside className="left-sidebar">
        <button
          type="button"
          className="brand"
          onClick={() => {
            setSearchResult(null)
            setOverview(null)
            setResearch(null)
            setError('')
            setQuery('')
            setSearchedQuery('')
          }}
        >
          <span className="brand-symbol" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path
                d="M4 18V6M4 18H21M7 14l4-4 3 2 5-6"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span>Indian Stock <strong>Explorer</strong></span>
        </button>

        <div className="side-section">
          <div className="side-label">WORKSPACE</div>
          <button
            className={!searchedQuery ? 'side-link active' : 'side-link'}
            type="button"
            onClick={() => {
              setSearchResult(null)
              setOverview(null)
              setResearch(null)
              setError('')
              setQuery('')
              setSearchedQuery('')
            }}
          >
            <span>◫</span> Discover
          </button>
          <button className="side-link" type="button" onClick={() => document.getElementById('company-search')?.focus()}>
            <span>⌕</span> Company search
          </button>
          <a className="side-link" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            <span>↗</span> API documentation
          </a>
        </div>

        <div className="side-section">
          <div className="side-heading">
            <span className="side-label">QUICK LOOKUP</span>
            <span className="side-count">{QUICK_SEARCHES.length}</span>
          </div>
          {QUICK_SEARCHES.map((item) => (
            <button
              type="button"
              className="watch-row"
              key={item.symbol}
              onClick={() => runSearch(item.symbol)}
              title={`Search ${item.name}`}
            >
              <span className="watch-icon">{item.symbol.slice(0, 1)}</span>
              <span className="watch-copy">
                <strong>{item.symbol}</strong>
                <small>{item.name}</small>
              </span>
              <span className="watch-arrow">↗</span>
            </button>
          ))}
        </div>

        <div className="side-section">
          <div className="side-label">RECENT SEARCHES</div>
          {lastSearches.length ? (
            lastSearches.map((item) => (
              <button
                className="recent-search"
                type="button"
                key={item}
                onClick={() => runSearch(item)}
              >
                <span>◷</span> {item}
              </button>
            ))
          ) : (
            <p className="muted-copy">Your recent searches will appear here.</p>
          )}
        </div>

        <div className="sidebar-footer">
          <span className="connection-indicator" />
          Local research workspace
          <small>India · NSE / BSE</small>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>MARKETS</span>
            <span className="breadcrumb-slash">/</span>
            <strong>INDIA</strong>
          </div>
          <div className="topbar-status">
            <span className="connection-indicator" />
            Research workspace
          </div>
        </header>

        <main className="dashboard">
          <section className="page-heading">
            <div>
              <div className="eyebrow">PUBLIC MARKETS / INDIA</div>
              <h1>
                Clarity before
                <br />
                <em>conviction.</em>
              </h1>
              <p>
                Resolve listed companies, compare their exchange quotes, and
                inspect the most recently available market data.
              </p>
            </div>
          </section>

          <form className="search-bar" onSubmit={submitSearch}>
            <span className="search-icon" aria-hidden="true">⌕</span>
            <input
              id="company-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search a company name or ticker…"
              maxLength={100}
              autoComplete="off"
              aria-label="Search company"
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Searching…' : 'Search'}
              <span aria-hidden="true">→</span>
            </button>
          </form>

          <div className="search-meta">
            <span>Try RELIANCE, TCS, INFY or TMPV</span>
            <span>Source: configured market-data provider</span>
          </div>

          {loading && (
            <div className="notice-panel" role="status" aria-live="polite">
              <span className="spinner" />
              Resolving company identity and retrieving available quotes…
            </div>
          )}

          {error && (
            <div className="notice-panel error-panel" role="alert">
              <strong>Search could not be completed</strong>
              <p>{error}</p>
              <button type="button" onClick={() => runSearch(query)}>Retry →</button>
            </div>
          )}

          {!loading && !error && isAmbiguous && (
            <section className="results-area">
              <div className="section-title">
                <div>
                  <div className="eyebrow">IDENTITY RESOLUTION</div>
                  <h2>Select the intended company</h2>
                  <p>More than one company matches “{searchedQuery}”.</p>
                </div>
                <StateBadge value="AMBIGUOUS" />
              </div>

              <div className="candidate-grid">
                {(searchResult?.matches || []).map((item, index) => (
                  <button
                    className="candidate-card"
                    type="button"
                    key={`${item.symbol}-${item.exchange}-${index}`}
                    onClick={() => runSearch(item.symbol)}
                  >
                    <span className="candidate-symbol">{item.symbol?.slice(0, 1)}</span>
                    <span className="candidate-name">
                      <strong>{item.company_name}</strong>
                      <small>{item.symbol} · {item.exchange}</small>
                    </span>
                    <span className="candidate-arrow">→</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {!loading && !error && isNotFound && (
            <section className="notice-panel">
              <StateBadge value={overview?.listing_status || 'UNVERIFIED'} />
              <h2>No matching listed company found</h2>
              <p>
                The configured listing data couldn't resolve “{searchedQuery}”.
                This does not independently prove that a company is unlisted.
              </p>
            </section>
          )}

          {!loading && !error && searchResult && !isAmbiguous && !isNotFound && overview && (
            <section className="results-area">
              <div className="section-title company-title">
                <div>
                  <div className="eyebrow">RESEARCH OVERVIEW</div>
                  <h2>{companyName}</h2>
                  <p className="result-query">Resolved from “{searchedQuery}”</p>
                </div>
                <StateBadge value={overview.listing_status} />
              </div>

              <div className="metric-strip">
                <div className="metric-item">
                  <span>IDENTITY</span>
                  <strong>{overview.resolution_status?.replaceAll('_', ' ') || 'UNKNOWN'}</strong>
                </div>
                <div className="metric-item">
                  <span>EXCHANGE LISTINGS</span>
                  <strong>{listings.length}</strong>
                </div>
                <div className="metric-item">
                  <span>EXCHANGES</span>
                  <strong>{[...new Set(listings.map((item) => (item.listing || item).exchange))].join(' / ') || '—'}</strong>
                </div>
              </div>

              {quoteError && (
                <div className="inline-warning" role="status">
                  <strong>Listing resolved, but quote retrieval failed.</strong>
                  <p>{quoteError}</p>
                  <button type="button" onClick={() => runSearch(searchedQuery)}>Retry quote lookup →</button>
                </div>
              )}

              <CloseComparison quote={primaryQuote} />

              <div className="listing-section-heading">
                <div>
                  <div className="eyebrow">LISTING DETAILS</div>
                  <h3>Exchange quotes</h3>
                </div>
                <span>{listings.length} listings</span>
              </div>

              <div className="quotes-grid">
                {listings.map((item, index) => {
                  const listing = item.listing || item
                  return (
                    <QuoteCard
                      key={`${listing.symbol}-${listing.exchange}-${index}`}
                      listing={listing}
                      quote={item.quote}
                    />
                  )
                })}
              </div>

              <div className="disclaimer">
                <span>ⓘ</span>
                <p>
                  Quotes may be delayed or stale and are not guaranteed to be
                  live. The close comparison uses only two observed values,
                  not intraday price history. For research purposes only; not
                  investment advice.
                </p>
              </div>
            </section>
          )}

          {!loading && !error && !searchResult && (
            <section className="discover-panel">
              <div className="discover-heading">
                <div>
                  <div className="eyebrow">START YOUR RESEARCH</div>
                  <h2>Explore Indian equities</h2>
                  <p>
                    Choose a quick lookup or enter a company name above. Quotes
                    appear only when the connected data source returns them.
                  </p>
                </div>
                <div className="discover-icon" aria-hidden="true">↗</div>
              </div>

              <div className="quick-grid">
                {QUICK_SEARCHES.map((item, index) => (
                  <button
                    type="button"
                    className="quick-card"
                    key={item.symbol}
                    onClick={() => runSearch(item.symbol)}
                  >
                    <span className="quick-card-top">
                      <span className="quick-number">0{index + 1}</span>
                      <span className="quick-arrow">↗</span>
                    </span>
                    <strong>{item.symbol}</strong>
                    <small>{item.name}</small>
                    <span className="quick-cta">Search company <span>→</span></span>
                  </button>
                ))}
              </div>

              <div className="discover-note">
                <span className="status-dot" />
                No market figures are displayed until a company lookup returns
                verified backend data.
              </div>
            </section>
          )}
        </main>

        <footer className="main-footer">
          <span>INDIAN STOCK EXPLORER</span>
          <span>Research carefully. Verify independently.</span>
        </footer>
      </div>

      <aside className="right-sidebar">
        <div className="rail-header">
          <div>
            <div className="eyebrow">RESEARCH DESK</div>
            <h2>Snapshot</h2>
          </div>
          <span className="rail-menu">···</span>
        </div>

        {overview ? (
          <>
            <div className="rail-company">
              <div className="eyebrow">CURRENT COMPANY</div>
              <h3>{companyName}</h3>
              <StateBadge value={overview.listing_status} />
            </div>

            <div className="rail-block">
              <div className="rail-block-heading">Listing coverage</div>
              {listings.length ? (
                listings.map((item, index) => {
                  const listing = item.listing || item
                  return (
                    <div className="rail-listing" key={`${listing.symbol}-${listing.exchange}-${index}`}>
                      <span className="rail-exchange">{listing.exchange}</span>
                      <div>
                        <strong>{listing.symbol}</strong>
                        <small>{item.quote ? 'Quote available' : 'No quote returned'}</small>
                      </div>
                      <span className="rail-arrow">↗</span>
                    </div>
                  )
                })
              ) : (
                <p className="muted-copy">No listings returned.</p>
              )}
            </div>

            <div className="rail-block">
              <div className="rail-block-heading">Data source</div>
              <div className="source-card">
                <span className="source-icon">◈</span>
                <div>
                  <strong>{primaryQuote?.source || 'Not available'}</strong>
                  <small>As reported by the API</small>
                </div>
              </div>
              {primaryQuote && (
                <div className="rail-data-time">
                  <span>Last quote timestamp</span>
                  <strong>{dateLabel(primaryQuote.as_of || primaryQuote.timestamp)}</strong>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="rail-welcome">
              <span className="rail-welcome-icon">⌕</span>
              <h3>Research with clarity.</h3>
              <p>
                Search a company to inspect listing identity, exchange coverage,
                and available market-data metadata.
              </p>
            </div>

            <div className="rail-block">
              <div className="rail-block-heading">What this workspace verifies</div>
              <div className="rail-check"><span>✓</span> Exchange listing identity</div>
              <div className="rail-check"><span>✓</span> NSE and BSE listing details</div>
              <div className="rail-check"><span>✓</span> Quote source and timestamp</div>
              <div className="rail-check"><span>✓</span> Quote freshness status</div>
            </div>
          </>
        )}

        <div className="rail-note">
          <div className="eyebrow">DATA POLICY</div>
          <p>
            Only returned backend fields are displayed. Missing data stays
            unavailable rather than being estimated.
          </p>
        </div>

        <div className="right-footer">
          <span className="connection-indicator" />
          Connected to local API when running
        </div>
      </aside>
    </div>
  )
}

export default App