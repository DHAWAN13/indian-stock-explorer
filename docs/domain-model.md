\# Domain Model



\## 1. Purpose



Define the core domain entities and relationships used by Indian Stock Explorer.



The domain model should remain independent of specific external providers.



\---



\## 2. Core Entities



\### 2.1 Company



Represents an Indian company.



Fields:



\- `company\_id`

\- `legal\_name`

\- `display\_name`

\- `description`

\- `website`

\- `sector`

\- `industry`



A company may be listed on one or more supported exchanges.



\---



\### 2.2 Security



Represents a tradable security associated with a company.



Fields:



\- `security\_id`

\- `company\_id`

\- `isin`

\- `exchange`

\- `symbol`

\- `exchange\_security\_code`

\- `security\_name`

\- `status`



A company may have multiple securities/listings.



\---



\### 2.3 Listing



Represents a company's listing on an exchange.



Fields:



\- `listing\_id`

\- `company\_id`

\- `security\_id`

\- `exchange`

\- `symbol`

\- `isin`

\- `listing\_status`



Supported exchanges:



NSE

BSE

