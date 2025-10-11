from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="Kerala Courts Case Search API",
    description="REST API wrapper for Kerala Courts case information system",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Kerala Courts Case Search API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
