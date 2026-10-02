\# System Architecture



\## 1. Purpose



Define the high-level architecture of Indian Stock Explorer before implementation.



The architecture must separate:



\- User interface

\- Application/API logic

\- Domain logic

\- External data providers

\- Deterministic calculations

\- Error handling



\---



\## 2. High-Level Architecture



&#x20;                   User

&#x20;                    |

&#x20;                    v

&#x20;             React Frontend

&#x20;                    |

&#x20;                    v

&#x20;              Backend API

&#x20;                    |

&#x20;         +----------+----------+

&#x20;         |                     |

&#x20;         v                     v

&#x20;  Company Resolution      Market Data Service

&#x20;         |                     |

&#x20;         v                     v

&#x20;    NSE / BSE             Market Data API

&#x20;         |

&#x20;         v

&#x20;  Listing Verification

&#x20;         |

&#x20;         v

&#x20;    Company Info

&#x20;  Official/Web Sources

