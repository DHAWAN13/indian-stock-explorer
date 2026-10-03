from app.services.company_resolver import CompanyResolver


def get_company_resolver() -> CompanyResolver:
    return CompanyResolver([])