from fastapi import FastAPI

from api.routes import router as api_router

app = FastAPI(title="PRAXIS API")
app.include_router(api_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
