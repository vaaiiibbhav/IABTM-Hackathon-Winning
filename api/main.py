from fastapi import FastAPI

app = FastAPI(title="PRAXIS API")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
