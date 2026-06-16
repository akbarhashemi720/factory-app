from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import HealthResponse
from app.routes import projects

app = FastAPI(
    title="AI Factory Backend",
    description="کارخانه ساخت هوشمند — Sprint 1",
    version=settings.app_version,
)

# Allow the local HTML prototype to call the API during development.
# Tighten origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],  # set ALLOWED_ORIGINS env var for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(projects.router)


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    """Simple liveness check."""
    return HealthResponse(
        status="ok",
        service="ai-factory-backend",
        version=settings.app_version,
    )
