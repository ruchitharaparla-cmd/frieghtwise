from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    users,
    health,
    vessels,
    ports,
    voyages,
    forecasts,
    recommendations,
    costs,
    risk,
    simulation
)


app = FastAPI(
    title="FreightWise API",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)

app.include_router(auth.router)

app.include_router(users.router)

app.include_router(vessels.router)

app.include_router(ports.router)

app.include_router(voyages.router)

app.include_router(forecasts.router)

app.include_router(recommendations.router)

app.include_router(costs.router)

app.include_router(risk.router)

app.include_router(simulation.router)


@app.get("/")
def root():
    return {
        "message": "FreightWise API is running"
    }