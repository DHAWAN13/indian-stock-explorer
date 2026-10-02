\# Product Requirements Document (PRD)



\## 1. Product Name



Indian Stock Explorer



\## 2. Product Overview



Indian Stock Explorer is a web application that allows users to search

for an Indian company, identify the company, determine whether it is

listed on NSE/BSE, and display relevant company information.



For listed companies, the application also displays the latest available

stock price, daily price movement, and historical price charts.



For unlisted companies, the application displays available company

information and clearly indicates that the company is not listed on

NSE/BSE.



\## 3. Problem Statement



Information about Indian companies and their stock-listing status can

require users to search across multiple sources.



A user may know only the company name and may want to quickly determine:



\- What company this is

\- Whether it is publicly listed

\- Which exchange it is listed on

\- What its latest stock price is

\- How its stock price has moved historically

\- Basic information about the company



The product aims to provide this information through a single,

simple interface.



\## 4. Target User



The primary user is a person who wants to quickly look up an Indian

company and understand its listing status and basic market information.



\## 5. MVP Goal



The MVP should allow a user to:



1\. Enter an Indian company name.

2\. Resolve the company.

3\. Determine its NSE/BSE listing status.

4\. View basic company information.

5\. View market information when the company is listed.

6\. View historical price movement when market data is available.



\## 6. Functional Requirements



\### FR-01: Company Search



The user must be able to enter a company name.



\### FR-02: Input Validation



The system must validate the search input and handle empty,

invalid, or excessively long input.



\### FR-03: Company Resolution



The system must identify the intended Indian company from the

user's input.



\### FR-04: Listing Verification



The system must determine whether the identified company is:



\- Listed on NSE

\- Listed on BSE

\- Listed on both NSE and BSE

\- Not listed on NSE/BSE

\- Unable to be verified



\### FR-05: Company Information



The system must display available basic company information,

including where applicable:



\- Company name

\- Description

\- Industry/sector

\- Headquarters

\- Country



\### FR-06: Current Market Information



For listed companies, the system must display:



\- Company name

\- Exchange

\- Stock symbol

\- Latest available price

\- Daily price change

\- Daily percentage change

\- Currency

\- Last-updated timestamp



\### FR-07: Historical Price Chart



For listed companies, the system should provide historical

price visualization with selectable periods:



\- 1D

\- 5D

\- 1M

\- 6M

\- YTD

\- 1Y

\- 5Y

\- MAX



\### FR-08: Unlisted Company Handling



If a company is identified but is not listed on NSE/BSE, the system

must still display available company information and clearly state

that it is not listed.



\### FR-09: Company Not Found



If the system cannot identify the company, it must display a clear

not-found message.



\### FR-10: Ambiguous Company



If the user's search matches multiple possible companies, the system

should ask the user to select or clarify the intended company.



\### FR-11: External Data Failure



If a third-party data provider is unavailable or returns invalid data,

the application must handle the failure gracefully.



\## 7. User Flow



User enters company name

&#x20;   ↓

Input validation

&#x20;   ↓

Company resolution

&#x20;   ↓

Listing verification

&#x20;   ↓

&#x20;   ├── Listed

&#x20;   │     ↓

&#x20;   │   Company information

&#x20;   │     +

&#x20;   │   Market data

&#x20;   │     +

&#x20;   │   Historical chart

&#x20;   │

&#x20;   └── Unlisted

&#x20;         ↓

&#x20;       Company information

&#x20;         +

&#x20;       "Not listed on NSE/BSE"



\## 8. Out of Scope for MVP



The following are explicitly excluded from the first release:



\- Stock trading

\- Buy/sell recommendations

\- Investment advice

\- Stock price prediction

\- Portfolio management

\- User accounts

\- Watchlists

\- News analysis

\- AI research agents

\- Automated investment decisions



\## 9. Data Accuracy Principle



Financial market information must come from designated market-data

sources rather than being generated or guessed by an AI model.



AI, if introduced in future versions, must not be treated as the

source of truth for stock prices or exchange-listing facts.



\## 10. MVP Success Criteria



The MVP is considered functionally complete when a user can:



\- Search for a valid Indian company.

\- Correctly identify the company.

\- Determine its NSE/BSE listing status.

\- View company information.

\- View current market information for listed companies.

\- View historical price data for listed companies.

\- Receive a clear result for an unlisted company.

\- Receive useful error messages for invalid or unavailable requests.

