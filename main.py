from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from routers import router as auth_router

app = FastAPI(
    title="Hackathon API",
    description="API dla aplikacji hackathonowej",
    version="1.0.0"
)

app.include_router(auth_router)

@app.get("/")
async def read_root():
    return {
        "message": "Witaj w Hackathon API!",
        "status": "działa",
        "endpoints": {
            "health": "/health",
            "database": "/database/status",
            "docs": "/docs"
        }
    }


