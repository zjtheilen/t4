from typing import List, Optional

import geopandas as gpd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from shapely.geometry import mapping, shape
from shapely.ops import transform

router = APIRouter(prefix="/api/v1", tags=["T4 Engine"])


class RouteRequest(BaseModel):
    source: int  # Node ID matching graph nodes
    target: int
    profile: str = "fantasy_overland"


class ItineraryRequest(BaseModel):
    stops: List[str]  # Settlement names (e.g. ["Oakhaven", "Riverbend"])
    profile: str = "fantasy_overland"


@router.get("/profiles")
def get_profiles():
    """Retrieve available traversal profiles and their configuration parameters."""
    return {"profiles": ["fantasy_overland", "default", "dcc", "backrooms"]}


@router.post("/route")
def calculate_route(request: Request, payload: RouteRequest):
    """Calculate the optimal path between source and target using effort-weighted Dijkstra."""
    try:
        engine = request.app.state.engine
        result = engine.find_route(source=payload.source, target=payload.target)

        safe_result = {k: v for k, v in result.items() if k != "edge_geoms"}
        safe_result["edge_count"] = len(result.get("edge_geoms", []))

        return {"status": "success", "data": safe_result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/itinerary")
def calculate_itinerary(request: Request, payload: ItineraryRequest):
    """Calculate a multi-stop itinerary, chaining segments and accumulating ledger resources."""
    try:
        engine = request.app.state.engine
        result = engine.find_itinerary(stop_names=payload.stops)

        safe_result = {k: v for k, v in result.items() if k != "edge_geoms"}
        safe_result["edge_count"] = len(result.get("edge_geoms", []))

        return {"status": "success", "data": safe_result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/geojson/world")
def get_world_geojson(request: Request):
    """Return settlements and roads as normalized GeoJSON for MapLibre rendering."""
    try:
        gpkg_path = request.app.state.engine.gpkg_path
        settlements_gdf = gpd.read_file(gpkg_path, layer="settlements")
        roads_gdf = gpd.read_file(gpkg_path, layer="roads")

        # If coordinates are massive local/projected units, normalize them to a clean local geographic span around [0,0]
        # Let's extract all points to find the bounding box
        total_geom = list(settlements_gdf.geometry) + list(roads_gdf.geometry)

        minx = min(g.bounds[0] for g in total_geom if not g.is_empty)
        miny = min(g.bounds[1] for g in total_geom if not g.is_empty)
        maxx = max(g.bounds[2] for g in total_geom if not g.is_empty)
        maxy = max(g.bounds[3] for g in total_geom if not g.is_empty)

        span_x = max(maxx - minx, 1.0)
        span_y = max(maxy - miny, 1.0)

        # Normalization function to map custom units into a nice [-10 to 10] range
        def normalize_geom(geom):
            if geom.is_empty:
                return geom

            def scale_coords(x, y, z=None):
                nx = ((x - minx) / span_x) * 20.0 - 10.0
                ny = ((y - miny) / span_y) * 20.0 - 10.0
                return (nx, ny)

            return transform(scale_coords, geom)

        settlements_gdf["geometry"] = settlements_gdf["geometry"].apply(normalize_geom)
        roads_gdf["geometry"] = roads_gdf["geometry"].apply(normalize_geom)

        return {
            "settlements": settlements_gdf.__geo_interface__,
            "roads": roads_gdf.__geo_interface__,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
