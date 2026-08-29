from fastapi import FastAPI

from evidenceforge.api.routers.research_tasks import (
    router as research_tasks_router,
)

app = FastAPI(
    title="EvidenceForge API",
    version="0.1.0",
    description="A secure, evidence-backed web research agent.",
)

app.include_router(research_tasks_router)


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "evidenceforge",
    }
