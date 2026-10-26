# tests/test_t4.py
import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
import networkx as nx

from src.t4.db import evaluate_road_status, is_road_blocked
from src.t4.profiles import PROFILES
from src.t4.graph import build_road_graph, TERRAIN_MULTIPLIERS
from src.t4.engine import RoutingEngine


def test_evaluate_road_status():
    """Verify that road statuses correctly classify into blocked, hazard, or open."""
    # Hard blocks
    assert evaluate_road_status("closed") == ("blocked", 0.0)
    assert evaluate_road_status("destroyed") == ("blocked", 0.0)
    assert evaluate_road_status("BLOCKED") == ("blocked", 0.0)

    # Soft hazards
    assert evaluate_road_status("washed_out") == ("hazard", 2.0)
    assert evaluate_road_status("flooded") == ("hazard", 2.0)

    # Open / Default
    assert evaluate_road_status("open") == ("open", 1.0)
    assert evaluate_road_status(None) == ("open", 1.0)
    assert evaluate_road_status("unknown_status") == ("open", 1.0)


def test_is_road_blocked():
    """Verify legacy block helper works correctly."""
    assert is_road_blocked("closed") is True
    assert is_road_blocked("open") is False
    assert is_road_blocked(None) is False


def test_profiles_structure():
    """Verify required resource profiles exist and have correct schema keys."""
    assert "fantasy_overland" in PROFILES
    assert "dcc_death_sport" in PROFILES
    assert "backrooms_survival" in PROFILES

    fantasy = PROFILES["fantasy_overland"]
    assert fantasy["time_unit"] == "Days"
    assert fantasy["resource_name"] == "Rations"
    assert fantasy["km_per_time_unit"] > 0


def test_synthetic_graph_and_routing():
    """Test graph construction, spatial snapping, and routing with synthetic data."""
    # 1. Create synthetic settlements
    settlements_df = gpd.GeoDataFrame(
        [
            {"id": 0, "name": "Settlement Alpha", "geometry": Point(0.0, 0.0)},
            {
                "id": 1,
                "name": "Settlement Beta",
                "geometry": Point(10000.0, 0.0),
            },  # 10 km away
            {
                "id": 2,
                "name": "Settlement Gamma",
                "geometry": Point(10000.0, 10000.0),
            },  # 10 km away
        ],
        crs="EPSG:4326",
    )

    # 2. Create synthetic roads connecting Alpha -> Beta -> Gamma
    roads_df = gpd.GeoDataFrame(
        [
            {
                "index": 1,
                "name": "Alpha-Beta Road",
                "terrain": "paved",
                "status": "open",
                "geometry": LineString([(0.0, 0.0), (10000.0, 0.0)]),
            },
            {
                "index": 2,
                "name": "Beta-Gamma Road",
                "terrain": "mountain",  # 1.5x multiplier
                "status": "washed_out",  # 2.0x hazard multiplier
                "geometry": LineString([(10000.0, 0.0), (10000.0, 10000.0)]),
            },
        ],
        crs="EPSG:4326",
    )

    # 3. Build graph with generous tolerance for testing
    G, settlement_lookup = build_road_graph(settlements_df, roads_df, tolerance=50000.0)

    assert len(G.nodes) == 3
    assert len(G.edges) == 2

    # 4. Instantiate RoutingEngine with DCC Death-Sport profile
    # Using a dummy gpkg path since synthetic tests don't require writing back
    engine = RoutingEngine(
        "dummy.gpkg", G, settlement_lookup, profile_key="dcc_death_sport"
    )

    # Override export method to prevent file I/O during unit test
    engine.export_route_to_gpkg = lambda res, name=None: True

    # Find route between Alpha (0) and Gamma (2)
    result = engine.find_route(0, 2)

    assert result["path"] == [0, 1, 2]
    assert result["path_names"] == [
        "Settlement Alpha",
        "Settlement Beta",
        "Settlement Gamma",
    ]
    assert result["total_physical_km"] == pytest.approx(20.0, rel=1e-2)
    assert len(result["hazard_warnings"]) == 1
    assert "washed_out" in result["hazard_warnings"][0]

    # Verify DCC profile calculations (5 km per hour, 4.5% battery burn rate)
    # Total km = 20. Total effort includes mountain (1.5x) and hazard (2.0x) on leg 2.
    assert result["time_unit_name"] == "Hours"
    assert result["resource_name"] == "Battery Charge (%)"
