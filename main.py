from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from routers import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from fundraiser_router import router as fundraiser_router
from users_router import router as users_router
from users_router import router_chuj as charity_router


app = FastAPI(
    title="Hackathon API",
    description="API dla aplikacji hackathonowej",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(fundraiser_router)
app.include_router(users_router)
app.include_router(charity_router)

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


