# src/t4/db.py
import geopandas as gpd


def load_geopackage(gpkg_path: str):
    """Loads settlements and roads layers from the T4 GeoPackage."""
    settlements = gpd.read_file(gpkg_path, layer="settlements").reset_index()
    roads = gpd.read_file(gpkg_path, layer="roads").reset_index()
    return settlements, roads


def is_road_blocked(status_val) -> bool:
    """Helper to check if a database status string represents a blockage."""
    if status_val is None:
        return False
    val_str = str(status_val).strip().lower()
    return val_str in ["blocked", "closed", "destroyed", "impassable"]
