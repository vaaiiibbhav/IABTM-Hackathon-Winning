"""PRAXIS FastAPI Main Application.

Configures application middleware, registers endpoint routers, and runs database schema initialisation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import init_db
from api.routes import self, feed, signals, interventions, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise schemas on server startup."""
    try:
        await init_db()
        print("Database schema successfully initialised.")
    except Exception as e:
        print(f"Error during database startup schema initialisation: {e}")
    yield


app = FastAPI(
    title="PRAXIS API",
    description="Explainable curation agent backend",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo ease, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route sub-modules
app.include_router(self.router)
app.include_router(feed.router)
app.include_router(signals.router)
app.include_router(interventions.router)
app.include_router(demo.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
