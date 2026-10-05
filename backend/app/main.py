
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.companies import router as companies_router

app = FastAPI(
    title="Indian Stock Explorer API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://indian-stock-explorer.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
