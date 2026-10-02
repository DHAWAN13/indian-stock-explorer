\# Provider Evaluation



\## 1. Purpose



This document evaluates external data providers and sources for the Indian Stock Explorer application.



The purpose is to identify reliable sources for:



\- Indian company identification

\- NSE/BSE listing status

\- Security identifiers

\- Current market data

\- Historical price data

\- Basic company information for unlisted companies



The application should use authoritative and structured sources wherever possible and should avoid treating general web search or LLM-generated information as the source of truth for financial data.



\---



\## 2. Data Source Strategy



The application separates data acquisition into three major categories:



1\. \*\*Exchange and security reference data\*\*

2\. \*\*Market data\*\*

3\. \*\*Company information\*\*



\### 2.1 Exchange and Security Reference Data



NSE and BSE should be treated as the primary sources for determining whether an Indian security is listed on an Indian stock exchange.



The system should use exchange-published security/reference data to determine:



\- Whether a security is listed

\- Exchange

\- Trading symbol

\- Security code

\- ISIN

\- Security name

\- Other relevant identifiers



NSE/BSE data should take precedence over general web search for listing-related information.



\---



\### 2.2 Market Data



Market data is required only after a company has been successfully resolved to a listed security.



Required data includes:



\- Latest available price

\- Previous closing price

\- Daily change

\- Daily percentage change

\- Timestamp

\- Historical OHLCV data

\- Trading date



Historical data will be used to construct price charts for supported ranges such as:



\- 1D

\- 5D

\- 1M

\- 6M

\- YTD

\- 1Y

\- 5Y

\- MAX



Market data should come from a structured financial-market data source rather than general web search or an LLM.



\---



\### 2.3 Company Information



Company information is required for both listed and unlisted companies.



For listed companies, information should preferably be associated with the verified security and exchange data.



For companies that cannot be matched to an NSE/BSE security, the system may search for additional company information.



Preferred information sources are:



1\. Official company website

2\. Government or regulatory sources

3\. Reputable public databases

4\. General web search as a discovery mechanism



Search results must not be treated as authoritative merely because they appear in search results.



\---



\## 3. Candidate Providers and Sources



| Provider / Source | Primary Purpose | Strength | Limitation | Proposed Role |

|---|---|---|---|---|

| NSE | Listing/security reference data | Official Indian exchange source | Exchange-specific | Primary listing source |

| BSE | Listing/security reference data | Official Indian exchange source | Exchange-specific | Primary listing source |

| Market-data API | Price and historical OHLCV | Structured API | Coverage/licensing varies | Market-data source |

| Google Search / Gemini Search | Company information discovery | Broad web coverage | Search results are not authoritative financial records | Unlisted-company discovery |

| Official company websites | Company information | First-party information | Not standardized | Preferred company-information source |

| Government/regulatory sources | Company information | High authority | APIs/data access may vary | Verification source |



\---



\## 4. NSE and BSE



\### 4.1 NSE



NSE provides exchange-published information about securities available for trading.



Potentially useful information includes:



\- Security name

\- Trading symbol

\- ISIN

\- Security type

\- Trading status

\- Exchange-related reference information



NSE should therefore be one of the primary sources used by the application when resolving an Indian company to a listed security.



\---



\### 4.2 BSE



BSE provides exchange and security-related information including identifiers such as:



\- BSE scrip code

\- Security name

\- ISIN

\- NSE symbol where applicable

\- Listing-related information



BSE should be used alongside NSE because a company may have different exchange coverage and identifiers.



\---



\### 4.3 Why Both Exchanges Are Required



Using only one exchange could produce an incomplete listing result.



The system should therefore conceptually perform:



Company

&#x20;  |

&#x20;  +----> NSE lookup

&#x20;  |

&#x20;  +----> BSE lookup

