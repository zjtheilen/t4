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


# src/t4/db.py


def evaluate_road_status(status_val):
    """
    Classifies road status into:
      - 'blocked': drop edge entirely
      - 'hazard': keep edge, apply effort penalty
      - 'open': standard traversal
    """
    if status_val is None:
        return "open", 1.0

    val_str = str(status_val).strip().lower()

    # Hard structural blocks (force detours)
    if val_str in ["blocked", "closed", "destroyed", "impassable", "sealed"]:
        return "blocked", 0.0

    # Soft operational hazards (impose penalties)
    elif val_str in [
        "washed_out",
        "hazard",
        "mudslide",
        "debris",
        "flooded",
        "checkpoint",
    ]:
        return "hazard", 2.0  # 2.0x hazard penalty multiplier

    return "open", 1.0
