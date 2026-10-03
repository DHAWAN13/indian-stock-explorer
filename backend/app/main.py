from fastapi import FastAPI

from app.api.routes.companies import router as companies_router

app = FastAPI(
    title="Indian Stock Explorer API",
    version="0.1.0",
)

app.include_router(companies_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}