from fastapi import FastAPI
from datetime import datetime, UTC



app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC),
    }
