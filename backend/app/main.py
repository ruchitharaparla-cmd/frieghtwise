from fastapi import FastAPI

from app.api.routes import (
    auth,
    users,
    health,
    vessels,
    ports,
    voyages,
    forecasts,
    recommendations
)


app = FastAPI(
    title="FreightWise API",
    version="0.1.0"
)


app.include_router(health.router)

app.include_router(auth.router)

app.include_router(users.router)

app.include_router(vessels.router)

app.include_router(ports.router)

app.include_router(voyages.router)

app.include_router(forecasts.router)

app.include_router(recommendations.router)


@app.get("/")
def root():
    return {
        "message": "FreightWise API is running"
    }