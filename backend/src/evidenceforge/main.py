from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evidenceforge.api.routers.research_tasks import (
    router as research_tasks_router,
)

app = FastAPI(
    title="EvidenceForge API",
    version="0.1.0",
    description="A secure, evidence-backed web research agent.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(research_tasks_router)


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "evidenceforge",
    }