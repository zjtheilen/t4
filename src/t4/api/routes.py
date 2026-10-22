from typing import List

import geopandas as gpd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from shapely.affinity import affine_transform

router = APIRouter(prefix="/api/v1", tags=["T4 Engine"])


class RouteRequest(BaseModel):
    source: int
    target: int
    profile: str = "fantasy_overland"


class ItineraryRequest(BaseModel):
    stops: List[str]
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

        raw_edge_geoms = result.get("edge_geoms", [])
        safe_result = {k: v for k, v in result.items() if k != "edge_geoms"}
        safe_result["edge_count"] = len(raw_edge_geoms)

        return {"status": "success", "data": safe_result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/itinerary")
def calculate_itinerary(request: Request, payload: ItineraryRequest):
    """Calculate a multi-stop itinerary, chaining segments and accumulating ledger resources."""
    try:
        engine = request.app.state.engine
        result = engine.find_itinerary(stop_names=payload.stops)

        # 1. Load GeoPackage layers for normalization
        gpkg_path = engine.gpkg_path
        settlements_gdf = gpd.read_file(gpkg_path, layer="settlements")
        roads_gdf = gpd.read_file(gpkg_path, layer="roads")
        
        all_geoms = list(settlements_gdf.geometry.dropna()) + list(
            roads_gdf.geometry.dropna()
        )

        minx = min(g.bounds[0] for g in all_geoms)
        miny = min(g.bounds[1] for g in all_geoms)
        maxx = max(g.bounds[2] for g in all_geoms)
        maxy = max(g.bounds[3] for g in all_geoms)

        span_x = max(maxx - minx, 1e-5)
        span_y = max(maxy - miny, 1e-5)
        lon_min, lon_max = -117.4, -116.8
        lat_min, lat_max = 33.2, 33.8

        scale_x = (lon_max - lon_min) / span_x
        scale_y = (lat_max - lat_min) / span_y
        xoff = lon_min - minx * scale_x
        yoff = lat_min - miny * scale_y

        def normalize_geom(geom):
            if geom.is_empty:
                return geom
            return affine_transform(geom, [scale_x, 0, 0, scale_y, xoff, yoff])

        # 2. Extract and normalize edge geometries into coordinate list for MapLibre
        raw_edge_geoms = result.get("edge_geoms", [])
        coordinates = []
        for geom in raw_edge_geoms:
            norm_geom = normalize_geom(geom)
            if not norm_geom.is_empty:
                if norm_geom.geom_type == "LineString":
                    coordinates.extend(list(norm_geom.coords))
                elif norm_geom.geom_type == "MultiLineString":
                    for part in norm_geom.geoms:
                        coordinates.extend(list(part.coords))

        safe_result = {k: v for k, v in result.items() if k != "edge_geoms"}
        safe_result["edge_count"] = len(raw_edge_geoms)
        safe_result["geometry"] = {"type": "LineString", "coordinates": coordinates}

        return {"status": "success", "data": safe_result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/geojson/world")
def get_world_geojson(request: Request):
    """Return settlements and roads as normalized GeoJSON for MapLibre rendering."""
    try:
        gpkg_path = request.app.state.engine.gpkg_path
        settlements_gdf = gpd.read_file(gpkg_path, layer="settlements")
        roads_gdf = gpd.read_file(gpkg_path, layer="roads")

        all_geoms = list(settlements_gdf.geometry.dropna()) + list(
            roads_gdf.geometry.dropna()
        )
        if not all_geoms:
            raise ValueError("No valid geometries found in GeoPackage.")

        minx = min(g.bounds[0] for g in all_geoms)
        miny = min(g.bounds[1] for g in all_geoms)
        maxx = max(g.bounds[2] for g in all_geoms)
        maxy = max(g.bounds[3] for g in all_geoms)

        span_x = max(maxx - minx, 1e-5)
        span_y = max(maxy - miny, 1e-5)

        lon_min, lon_max = -117.4, -116.8
        lat_min, lat_max = 33.2, 33.8

        scale_x = (lon_max - lon_min) / span_x
        scale_y = (lat_max - lat_min) / span_y
        xoff = lon_min - minx * scale_x
        yoff = lat_min - miny * scale_y

        def normalize_geom(geom):
            if geom.is_empty:
                return geom
            return affine_transform(geom, [scale_x, 0, 0, scale_y, xoff, yoff])

        settlements_gdf["geometry"] = settlements_gdf["geometry"].apply(normalize_geom)
        roads_gdf["geometry"] = roads_gdf["geometry"].apply(normalize_geom)

        return {
            "settlements": settlements_gdf.__geo_interface__,
            "roads": roads_gdf.__geo_interface__,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))