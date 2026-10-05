import { useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

const QUICK_SEARCHES = [
  { symbol: 'RELIANCE', name: 'Reliance Industries' },
  { symbol: 'TCS', name: 'Tata Consultancy Services' },
  { symbol: 'INFY', name: 'Infosys' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank' },
]

const HISTORY_RANGES = ['1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'MAX']

async function apiGet(path, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options)
  } catch (error) {
    if (error?.name === 'AbortError') throw error
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

function chartTimeLabel(value, range) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'

  if (range === '1D' || range === '5D') {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Kolkata',
    })
  }

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    ...(range === '5Y' || range === 'MAX' ? { year: '2-digit' } : {}),
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

  return (
    <span className={`state-badge ${kind}`}>
      {status.replaceAll('_', ' ')}
    </span>
  )
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

      {listing.isin && <p className="isin">ISIN · {listing.isin}</p>}

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
            Source: {quote.source || 'Not provided'}
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

function HistoricalPriceChart({
  symbol,
  exchange,
  quote,
  range,
  onRangeChange,
  data,
  loading,
  error,
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null)

  const bars = Array.isArray(data?.bars) ? data.bars : []
  const validBars = bars
    .map((bar, index) => ({ bar, index, value: Number(bar.close) }))
    .filter((point) => Number.isFinite(point.value) && point.value > 0)

  const width = 800
  const left = 76
  const right = 782
  const top = 23
  const bottom = 226

  let points = []
  let ticks = []
  let linePath = ''
  let areaPath = ''

  if (validBars.length) {
    const rawMin = Math.min(...validBars.map((point) => point.value))
    const rawMax = Math.max(...validBars.map((point) => point.value))
    const spread = Math.max(rawMax - rawMin, Math.abs(rawMax) * 0.01, 0.01)
    const minValue = rawMin - spread * 0.12
    const maxValue = rawMax + spread * 0.12

    points = validBars.map((point, index) => ({
      ...point,
      x:
        left +
        (validBars.length === 1
          ? 0
          : (index / (validBars.length - 1)) * (right - left)),
      y:
        bottom -
        ((point.value - minValue) / (maxValue - minValue)) * (bottom - top),
    }))

    ticks = Array.from({ length: 4 }, (_, index) => {
      const value = minValue + ((maxValue - minValue) * index) / 3
      return {
        value,
        y: bottom - ((value - minValue) / (maxValue - minValue)) * (bottom - top),
      }
    })

    linePath = points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ')

    areaPath =
      `${linePath} L ${points[points.length - 1].x} ${bottom}` +
      ` L ${points[0].x} ${bottom} Z`
  }

  const activeIndex =
    hoveredIndex == null
      ? points.length - 1
      : Math.min(hoveredIndex, points.length - 1)

  const activePoint = points[activeIndex]
  const firstPoint = points[0]
  const lastPoint = points[points.length - 1]

  const rangeChange =
    firstPoint && lastPoint && firstPoint.value !== 0
      ? ((lastPoint.value - firstPoint.value) / firstPoint.value) * 100
      : null

  const chartIsUp = rangeChange == null || rangeChange >= 0
  const chartColor = chartIsUp ? '#22c55e' : '#ef4444'
  const chartFillId = chartIsUp ? 'history-fill-green' : 'history-fill-red'

  function selectNearestPoint(event) {
    if (!points.length) return

    const rect = event.currentTarget.getBoundingClientRect()
    const chartX = ((event.clientX - rect.left) / rect.width) * width

    let nearestIndex = 0
    let distance = Infinity

    points.forEach((point, index) => {
      const candidateDistance = Math.abs(point.x - chartX)

      if (candidateDistance < distance) {
        distance = candidateDistance
        nearestIndex = index
      }
    })

    setHoveredIndex(nearestIndex)
  }

  const axisIndices = [
    ...new Set(
      points.length > 1
        ? [0, Math.floor((points.length - 1) / 2), points.length - 1]
        : points.length
          ? [0]
          : [],
    ),
  ]

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <div className="micro-label">HISTORICAL MARKET DATA</div>
          <h3>Price history</h3>
          <p>
            {symbol && exchange ? `${symbol} · ${exchange}` : 'Company history'}
            {data && ` · ${validBars.length} observations`}
          </p>
        </div>

        {quote && <QuoteStatus quote={quote} />}
      </div>

      <div className="history-range-bar" aria-label="Historical time range">
        {HISTORY_RANGES.map((item) => (
          <button
            key={item}
            type="button"
            className={range === item ? 'selected' : ''}
            aria-pressed={range === item}
            disabled={loading || !symbol || !exchange}
            onClick={() => {
              setHoveredIndex(null)
              onRangeChange(item)
            }}
          >
            {item}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="history-state" role="status" aria-live="polite">
          <span className="spinner" />
          Loading {range} historical prices…
        </div>
      ) : error ? (
        <div className="history-state history-error" role="alert">
          <strong>Historical prices unavailable</strong>
          <p>{error}</p>
          <button type="button" onClick={() => onRangeChange(range)}>
            Retry this range
          </button>
        </div>
      ) : !validBars.length ? (
        <div className="history-state">
          No historical observations were returned for {range}. Try another
          range or check back later.
        </div>
      ) : (
        <>
          <div className="history-current-value">
            <strong>{money(activePoint.value, quote?.currency || 'INR')}</strong>
            <span>{dateLabel(activePoint.bar.timestamp)}</span>
            {rangeChange != null && (
              <span className={rangeChange >= 0 ? 'up' : 'down'}>
                {rangeChange > 0 ? '+' : ''}
                {rangeChange.toFixed(2)}% over selected range
              </span>
            )}
          </div>

          <div className="historical-chart">
            <svg
              viewBox="0 0 800 278"
              role="img"
              aria-label={`${symbol} historical closing prices for ${range}`}
              onPointerMove={selectNearestPoint}
              onPointerLeave={() => setHoveredIndex(null)}
            >
              <defs>
                <linearGradient
                  id={chartFillId}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="0%" stopColor={chartColor} stopOpacity="0.23" />
                  <stop offset="100%" stopColor={chartColor} stopOpacity="0.01" />
                </linearGradient>
              </defs>

              {ticks.map((tick, index) => (
                <g key={index}>
                  <line
                    x1={left}
                    x2={right}
                    y1={tick.y}
                    y2={tick.y}
                    className="chart-gridline"
                  />
                  <text
                    x={left - 12}
                    y={tick.y + 4}
                    textAnchor="end"
                    className="chart-y-label"
                  >
                    {number(tick.value)}
                  </text>
                </g>
              ))}

              <path d={areaPath} fill={`url(#${chartFillId})`} />

              <path
                d={linePath}
                fill="none"
                stroke={chartColor}
                strokeWidth="2.3"
                strokeLinejoin="round"
                strokeLinecap="round"
                vectorEffect="non-scaling-stroke"
              />

              {activePoint && (
                <>
                  <line
                    x1={activePoint.x}
                    x2={activePoint.x}
                    y1={top}
                    y2={bottom}
                    className="chart-crosshair"
                  />
                  <circle
                    cx={activePoint.x}
                    cy={activePoint.y}
                    r="5"
                    fill={chartColor}
                    stroke="#0e151b"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                </>
              )}

              {axisIndices.map((index) => (
                <text
                  key={index}
                  x={points[index].x}
                  y="257"
                  textAnchor={
                    index === 0
                      ? 'start'
                      : index === points.length - 1
                        ? 'end'
                        : 'middle'
                  }
                  className="chart-x-label"
                >
                  {chartTimeLabel(points[index].bar.timestamp, range)}
                </text>
              ))}
            </svg>
          </div>

          <div className="historical-ohlc">
            <div>
              <span>Open</span>
              <strong>{money(activePoint.bar.open, quote?.currency || 'INR')}</strong>
            </div>
            <div>
              <span>High</span>
              <strong>{money(activePoint.bar.high, quote?.currency || 'INR')}</strong>
            </div>
            <div>
              <span>Low</span>
              <strong>{money(activePoint.bar.low, quote?.currency || 'INR')}</strong>
            </div>
            <div>
              <span>Close</span>
              <strong>{money(activePoint.bar.close, quote?.currency || 'INR')}</strong>
            </div>
            <div>
              <span>Volume</span>
              <strong>
                {activePoint.bar.volume == null
                  ? '—'
                  : Number(activePoint.bar.volume).toLocaleString('en-IN')}
              </strong>
            </div>
          </div>

          <p className="chart-disclaimer">
            Source: {data?.source || 'Configured market-data provider'}. Chart
            points use the actual observations returned by the provider.
            Intraday history may be delayed or unavailable.
          </p>
        </>
      )}
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

  const [historyRange, setHistoryRange] = useState('1M')
  const [historyData, setHistoryData] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const historyRequestRef = useRef(null)

  async function loadHistory(symbol, exchange, range) {
    historyRequestRef.current?.abort()

    if (!symbol || !exchange) {
      historyRequestRef.current = null
      setHistoryData(null)
      setHistoryError('')
      setHistoryLoading(false)
      return
    }

    const controller = new AbortController()
    historyRequestRef.current = controller
    setHistoryLoading(true)
    setHistoryData(null)
    setHistoryError('')

    const params = new URLSearchParams({ symbol, exchange, range })

    try {
      const result = await apiGet(
        `/api/v1/companies/history?${params.toString()}`,
        { signal: controller.signal },
      )

      if (historyRequestRef.current === controller) {
        setHistoryData(result)
      }
    } catch (requestError) {
      if (
        historyRequestRef.current === controller &&
        requestError.name !== 'AbortError'
      ) {
        setHistoryData(null)
        setHistoryError(requestError.message)
      }
    } finally {
      if (historyRequestRef.current === controller) {
        historyRequestRef.current = null
        setHistoryLoading(false)
      }
    }
  }

  async function runSearch(rawQuery) {
    const term = rawQuery.trim()

    if (!term) {
      setError('Enter a company name or ticker symbol.')
      return
    }

    setQuery(term)
    setSearchedQuery(term)
    historyRequestRef.current?.abort()
    historyRequestRef.current = null
    setHistoryLoading(false)
    setLoading(true)
    setError('')
    setQuoteError('')
    setSearchResult(null)
    setOverview(null)
    setResearch(null)
    setHistoryData(null)
    setHistoryError('')

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
        let researchData = null

        try {
          researchData = await apiGet(`/api/v1/companies/research?q=${q}`)
          setResearch(researchData)
        } catch (researchFailure) {
          setQuoteError(researchFailure.message)
        }

        const researchListings =
          researchData?.listings ||
          (overviewData.listings || []).map((listing) => ({ listing, quote: null }))
        const historyItem =
          researchListings.find(
            (item) => (item.listing || item).exchange === 'NSE' && item.quote,
          ) ||
          researchListings.find((item) => item.quote) ||
          researchListings[0]
        const listing = historyItem?.listing || historyItem

        if (listing?.symbol && listing?.exchange) {
          void loadHistory(listing.symbol, listing.exchange, historyRange)
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
    (overview?.listings || []).map((listing) => ({
      listing,
      quote: null,
    }))

  const primaryItem =
    listings.find(
      (item) => (item.listing || item).exchange === 'NSE' && item.quote,
    ) ||
    listings.find((item) => item.quote) ||
    listings[0] ||
    null

  const primaryListing = primaryItem
    ? primaryItem.listing || primaryItem
    : null

  const primaryQuote = primaryItem?.quote || null
  const historySymbol = primaryListing?.symbol || ''
  const historyExchange = primaryListing?.exchange || ''
  const companyName =
    research?.company_name || overview?.company_name || searchedQuery

  function resetWorkspace() {
    historyRequestRef.current?.abort()
    historyRequestRef.current = null
    setHistoryLoading(false)
    setSearchResult(null)
    setOverview(null)
    setResearch(null)
    setHistoryData(null)
    setHistoryError('')
    setError('')
    setQuoteError('')
    setQuery('')
    setSearchedQuery('')
  }

  return (
    <div className="finance-app">
      <aside className="left-sidebar">
        <button type="button" className="brand" onClick={resetWorkspace}>
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
          <span>
            Indian Stock <strong>Explorer</strong>
          </span>
        </button>

        <div className="side-section">
          <div className="side-label">WORKSPACE</div>
          <button
            className={!searchedQuery ? 'side-link active' : 'side-link'}
            type="button"
            onClick={resetWorkspace}
          >
            <span>◫</span> Discover
          </button>
          <button
            className="side-link"
            type="button"
            onClick={() => document.getElementById('company-search')?.focus()}
          >
            <span>⌕</span> Company search
          </button>
          <a
            className="side-link"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
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
          <section className={`page-heading ${searchedQuery ? 'has-results' : ''}`}>
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
              <button type="button" onClick={() => runSearch(query)}>
                Retry →
              </button>
            </div>
          )}

          {!loading && !error && isAmbiguous && (
            <section className="results-area">
              <div className="section-title">
                <div>
                  <div className="eyebrow">IDENTITY RESOLUTION</div>
                  <h2>Select the intended company</h2>
                  <p>More than one company matches &quot;{searchedQuery}&quot;.</p>
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
                    <span className="candidate-symbol">
                      {item.symbol?.slice(0, 1)}
                    </span>
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
                The configured listing data couldn&apos;t resolve &quot;{searchedQuery}&quot;.
                This does not independently prove that a company is unlisted.
              </p>
            </section>
          )}

          {!loading &&
            !error &&
            searchResult &&
            !isAmbiguous &&
            !isNotFound &&
            overview && (
              <section className="results-area">
                <div className="section-title company-title">
                  <div>
                    <div className="eyebrow">RESEARCH OVERVIEW</div>
                    <h2>{companyName}</h2>
                    <p className="result-query">
                      Resolved from &quot;{searchedQuery}&quot;
                    </p>
                  </div>
                  <StateBadge value={overview.listing_status} />
                </div>

                <div className="metric-strip">
                  <div className="metric-item">
                    <span>IDENTITY</span>
                    <strong>
                      {overview.resolution_status?.replaceAll('_', ' ') || 'UNKNOWN'}
                    </strong>
                  </div>
                  <div className="metric-item">
                    <span>EXCHANGE LISTINGS</span>
                    <strong>{listings.length}</strong>
                  </div>
                  <div className="metric-item">
                    <span>EXCHANGES</span>
                    <strong>
                      {[...new Set(listings.map((item) => (item.listing || item).exchange))]
                        .join(' / ') || '—'}
                    </strong>
                  </div>
                </div>

                {quoteError && (
                  <div className="inline-warning" role="status">
                    <strong>Listing resolved, but quote retrieval failed.</strong>
                    <p>{quoteError}</p>
                    <button
                      type="button"
                      onClick={() => runSearch(searchedQuery)}
                    >
                      Retry quote lookup →
                    </button>
                  </div>
                )}

                <HistoricalPriceChart
                  symbol={historySymbol}
                  exchange={historyExchange}
                  quote={primaryQuote}
                  range={historyRange}
                  onRangeChange={(nextRange) => {
                    setHistoryRange(nextRange)
                    void loadHistory(historySymbol, historyExchange, nextRange)
                  }}
                  data={historyData}
                  loading={historyLoading}
                  error={historyError}
                />

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
                    live. The chart displays observations returned by Yahoo
                    Finance; it is not an exchange-authoritative feed. For
                    research purposes only, not investment advice.
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
                    <span className="quick-cta">
                      Search company <span>→</span>
                    </span>
                  </button>
                ))}
              </div>

              <div className="discover-note">
                <span className="status-dot" />
                No market figures are displayed until a company lookup returns
                backend data.
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
                    <div
                      className="rail-listing"
                      key={`${listing.symbol}-${listing.exchange}-${index}`}
                    >
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
                  <strong>
                    {dateLabel(primaryQuote.as_of || primaryQuote.timestamp)}
                  </strong>
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
