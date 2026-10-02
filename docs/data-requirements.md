\# Data Requirements



\## 1. Purpose



This document defines the data required by Indian Stock Explorer.



The purpose is to identify the information required by the product

before selecting specific external data providers.



\---



\## 2. Company Search Data



The system must support searching for an Indian company using

user-provided text.



Required information:



\- User search query

\- Normalized search query

\- Matched company name

\- Company identifier where available

\- Confidence or match status

\- Alternative matches when the query is ambiguous



Example:



User input:

TCS



Resolved company:

Tata Consultancy Services Limited



\---



\## 3. Company Identity Data



For an identified company, the system should be able to obtain:



\- Company name

\- Legal/company name where available

\- Unique identifier where available

\- Country

\- Industry or sector where available

\- Company description

\- Headquarters where available

\- Company website where available



The company identity data should not depend exclusively on stock-market

data because the system also needs to display information for

unlisted companies.



\---



\## 4. Listing Data



The system must determine the company's listing status in relation

to Indian public exchanges.



Required information:



\- Listing status

\- Exchange

\- Trading symbol

\- ISIN where available

\- Exchange-specific security identifier where available

\- Security status where available



Possible application states:



\- Listed on NSE

\- Listed on BSE

\- Listed on both NSE and BSE

\- Not listed on NSE/BSE

\- Unable to verify



Listing verification should be based on structured exchange/security

data rather than an LLM-generated answer.



Official exchange security files and market reports can provide

structured information for listed securities.



\---



\## 5. Current Market Data



For a listed company, the application requires:



\- Latest available price

\- Previous close

\- Absolute price change

\- Percentage price change

\- Currency

\- Exchange

\- Symbol

\- Market-data timestamp

\- Data freshness/status



The application must distinguish between:



\- Live/current market price

\- Delayed price

\- Most recently available trading price

\- Previous closing price



The interface must clearly communicate when the displayed value is

not a live price.



\---



\## 6. Historical Market Data



The chart requires historical OHLCV data where available.



Required fields:



\- Timestamp/date

\- Open

\- High

\- Low

\- Close

\- Volume where available



Supported user-selected ranges:



\- 1D

\- 5D

\- 1M

\- 6M

\- YTD

\- 1Y

\- 5Y

\- MAX



The backend should return normalized historical price data so that

the frontend does not need to understand provider-specific formats.



\---



\## 7. Company Information for Unlisted Companies



An identified company that is not listed on NSE/BSE must still be

able to receive basic company information.



The data source for this information must support companies that do

not have publicly traded securities.



Required information where available:



\- Company name

\- Description

\- Industry/sector

\- Headquarters

\- Country

\- Website

\- Other basic identifying information



The system must not assume that a company is non-existent simply

because it is absent from a market-data provider.



\---



\## 8. Data Freshness



Each data category has a different freshness requirement.



\### Listing Data



Should represent a current or recently refreshed view of exchange

security listings.



\### Company Information



Does not normally require real-time updates.



\### Current Market Data



Requires the provider's stated market-data timestamp and freshness

status.



\### Historical Data



Must contain timestamps or dates so the frontend can accurately

label the chart.



\---



\## 9. Data Quality Requirements



The system should validate external data before returning it to the

frontend.



Examples:



\- Price must be numeric where present.

\- Currency must be identified.

\- Exchange must be known for listed securities.

\- Symbol must correspond to the resolved security.

\- Historical timestamps must be ordered correctly.

\- Missing provider fields must be handled safely.

\- Provider responses must not be blindly trusted.



\---



\## 10. Source-of-Truth Principle



Different types of information may have different authoritative

sources.



\### Listing and security identity



Prefer official exchange/security reference data.



\### Market prices



Use a designated market-data provider with documented coverage.



\### Company information



Use a designated company-information source that can support

both listed and unlisted Indian companies.



The final providers will be selected during the provider-evaluation

phase.



\---



\## 11. Provider Failure



External providers may fail or return incomplete data.



The system must distinguish between:



\- Company not found

\- Company found but listing cannot be verified

\- Listing verified but market data unavailable

\- Provider timeout

\- Provider rate limit

\- Invalid provider response

\- Temporary provider outage



These cases must not be treated as the same condition.



\---



\## 12. Data Normalization



Provider-specific responses must be converted into internal

application models.



Example:



External provider:

provider-specific field names and formats



&#x20;       ↓



Normalization layer



&#x20;       ↓



Application model:



Company

Listing

MarketSnapshot

PricePoint



The frontend should consume the application's normalized response

rather than provider-specific JSON.



\---



\## 13. MVP Data Set



The minimum data required for V1 is:



\### Company



\- Name

\- Description

\- Industry/sector where available

\- Headquarters where available

\- Country



\### Listing



\- Listed/unlisted status

\- Exchange

\- Symbol

\- ISIN where available



\### Current Market Data



\- Latest available price

\- Price change

\- Percentage change

\- Currency

\- Timestamp



\### Historical Market Data



\- Timestamp/date

\- Close price

\- OHLC where available

\- Volume where available



\---



\## 14. Out of Scope



The following data is not required for V1:



\- Financial statements

\- P/E ratio

\- EPS

\- Balance sheet

\- News

\- Analyst ratings

\- Price targets

\- Insider transactions

\- Institutional holdings

\- AI-generated investment analysis



These may be considered in later releases.



\---



\## 15. Data Acceptance Criteria



\- \[ ] Required company data fields are defined.

\- \[ ] Required listing data fields are defined.

\- \[ ] Required current market fields are defined.

\- \[ ] Historical chart data requirements are defined.

\- \[ ] Unlisted-company data requirements are defined.

\- \[ ] Data freshness requirements are documented.

\- \[ ] Data quality requirements are documented.

\- \[ ] Provider failure states are documented.

\- \[ ] Provider-specific data can be normalized into internal models.

\- \[ ] Final providers are deferred to the provider-evaluation phase.

