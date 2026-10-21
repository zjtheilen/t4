# run.py
from src.t4.db import load_geopackage
from src.t4.engine import RoutingEngine
from src.t4.graph import build_road_graph

GPKG_PATH = "experiments/graphic-spike/eldmere.gpkg"


def main():
    print("=== T⁴ MODULAR ROUTING ENGINE (PHASE 2) ===")

    settlements, roads = load_geopackage(GPKG_PATH)
    G, settlement_lookup = build_road_graph(settlements, roads)
    print(
        f"Successfully built active graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} active edges."
    )
    # print(f"Zach test 1: {settlements}")
    # print(f"Zach test 2: {roads}")

    # Fantasy Mode
    # engine = RoutingEngine(GPKG_PATH, G, settlement_lookup, profile_key="fantasy_overland")

    # DCC Death-Sport Mode
    engine = RoutingEngine(GPKG_PATH, G, settlement_lookup, profile_key="dcc_death_sport")

    # Test a multi-stop trade loop itinerary!
    # Adjust these names based on the settlements in your eldmere.gpkg
    itinerary_stops = ["Oakhaven", "Riverbend", "Northgate"]

    print(f"\n--- Calculating Multi-Stop Itinerary: {' ➔ '.join(itinerary_stops)} ---")
    try:
        result = engine.find_itinerary(itinerary_stops)

        print(f"  - Full Route Sequence: {' ➔ '.join(result['path_names'])}")
        print(f"  - Total Distance: {result['total_physical_km'] * 1000:.2f} meters")
        print(f"  - Total Hexes Crossed: {result['hexes_crossed']}")
        print(f"  - Total Travel Time: {result['time_units_traveled']} {result['time_unit_name']}")
        print(f"  - Cumulative Resource Required: {result['resources_consumed']} units ({result['resource_name']})")

        # Export loop back to QGIS
        engine.export_route_to_gpkg(
            result, route_name="Trade Loop: Oakhaven-Riverbend-Northgate"
        )
        print(
            "  💾 Multi-stop itinerary successfully written to GeoPackage layer 'active_routes'!"
        )

    except Exception as e:
        print(f"  ❌ Itinerary Error: {e}")


if __name__ == "__main__":
    main()
