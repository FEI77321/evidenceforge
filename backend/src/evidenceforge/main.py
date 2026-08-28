from fastapi import FastAPI

app = FastAPI(
    title="EvidenceForge API",
    version="0.1.0",
    description="A secure, evidence-backed web research agent.",
)


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "evidenceforge",
    }
