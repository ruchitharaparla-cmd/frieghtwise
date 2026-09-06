from fastapi import FastAPI

from app.api.routes import (
    auth,
    users,
    health
)


app = FastAPI(
    title="FreightWise API",
    version="0.1.0"
)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {
        "message": "FreightWise API is running"
    }