from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from t4.api.routes import router as api_router
from t4.db import load_geopackage
from t4.engine import RoutingEngine
from t4.graph import build_road_graph

GPKG_PATH = "experiments/graphic-spike/eldmere.gpkg"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cache the RoutingEngine in app.state on startup using exact engine loaders."""
    try:
        print(f"--- [API Startup] Loading GeoPackage from {GPKG_PATH} ---")
        settlements, roads = load_geopackage(GPKG_PATH)
        G, settlement_lookup = build_road_graph(settlements, roads)
        print(
            f"--- [API Startup] Graph built successfully: {G.number_of_nodes()} nodes, {G.number_of_edges()} active edges ---"
        )
        print(f"--- [API Startup] Settlement Lookup: {settlement_lookup} ---")

        # Store singleton engine instance in app state
        app.state.engine = RoutingEngine(
            gpkg_path=GPKG_PATH,
            G=G,
            settlement_lookup=settlement_lookup,
            profile_key="dcc_death_sport",
        )
    except Exception as e:
        print(f"[Startup Error] Could not load spatial data: {e}")

    yield


app = FastAPI(
    title="T4 Spatial Logistics API",
    description="API-driven backend for topographic terrain traversal and pathfinding.",
    version="0.3.0",
    lifespan=lifespan,
)

# Enable CORS for local development (React / MapLibre frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
def read_root():
    return {"status": "online", "system": "T4 Spatial Logistics Engine", "phase": 3}
