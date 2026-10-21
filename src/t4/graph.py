# src/t4/graph.py
import networkx as nx
from shapely.geometry import Point
from .db import is_road_blocked, evaluate_road_status

TERRAIN_MULTIPLIERS = {
    "paved": 1.0,
    "rough": 1.5,
    "mountain": 2.5,
    "swamp": 3.0,
    "open": 1.0,
}


def build_road_graph(settlements, roads, tolerance=50000.0) -> tuple[nx.Graph, dict]:
    """Builds a NetworkX graph by spatially matching road endpoints to settlements."""
    G = nx.Graph()

    # 1. Map settlements
    settlement_lookup = {}
    settlement_nodes = []
    for idx, row in settlements.iterrows():
        s_id = row.get("index", row.get("fid", idx))
        name = row.get("name", f"Settlement {s_id}")
        geom = row["geometry"]
        settlement_lookup[s_id] = name
        G.add_node(s_id, name=name, geometry=geom)
        settlement_nodes.append((s_id, name, geom))

    print(f"\n--- [DEBUG] Settlements ---")
    for s_id, name, geom in settlement_nodes:
        print(f"  ID {s_id}: {name} -> X: {geom.x:.2f}, Y: {geom.y:.2f}")

    print(f"\n--- [DEBUG] Evaluating Roads ---")

    def find_nearest_settlement(point: Point):
        closest_id = None
        closest_name = None
        min_dist = float("inf")
        for s_id, s_name, s_geom in settlement_nodes:
            dist = point.distance(s_geom)
            if dist < min_dist:
                min_dist = dist
                closest_id = s_id
                closest_name = s_name
        return closest_id, closest_name, min_dist

    # 2. Process roads
    for idx, road in roads.iterrows():
        road_id = road.get("index", road.get("fid", idx))
        road_name = road.get("name", f"Road {road_id}")
        status = road.get("status", "open")
        condition_type, hazard_multiplier = evaluate_road_status(status)

        if condition_type == "blocked":
            print(f"  [{road_name}] Skipped: hard blockage ('{status}')")
            continue

        line = road.geometry
        if line is None or line.is_empty:
            print(f"  [{road_name}] Skipped: empty geometry")
            continue

        coords = list(line.coords)
        start_point = Point(coords[0])
        end_point = Point(coords[-1])

        u, u_name, u_dist = find_nearest_settlement(start_point)
        v, v_name, v_dist = find_nearest_settlement(end_point)

        print(f"  [{road_name}]")
        print(
            f"    Start endpoint ({start_point.x:.2f}, {start_point.y:.2f}) -> Nearest: {u_name} (dist: {u_dist:.1f}m)"
        )
        print(
            f"    End endpoint   ({end_point.x:.2f}, {end_point.y:.2f}) -> Nearest: {v_name} (dist: {v_dist:.1f}m)"
        )

        # Check tolerance (using a massive default tolerance of 50km for now to test linkage)
        if u_dist <= tolerance and v_dist <= tolerance and u != v:
            length_km = line.length / 1000.0
            terrain_type = str(road.get("terrain", "paved")).strip().lower()
            terrain_multiplier = TERRAIN_MULTIPLIERS.get(terrain_type, 1.0)
            multiplier = TERRAIN_MULTIPLIERS.get(terrain_type, 1.0)
            effort_distance = length_km * multiplier
            final_effort_weight = length_km * terrain_multiplier
            if condition_type == "hazard":
                final_effort_weight *= hazard_multiplier
                print(f"  ⚠️ [{road_name}] Soft Hazard Active ({status}): Effort weight multiplied by {hazard_multiplier}x")

            if G.has_edge(u, v):
                if effort_distance >= G[u][v]["weight"]:
                    continue

            G.add_edge(
                u, v,
                weight=final_effort_weight,
                length_km=length_km,
                road_id=road_id,
                geometry=line,
                terrain=terrain_type,
                condition=condition_type,
                status_text=status,
                hazard_multiplier=hazard_multiplier if condition_type == "hazard" else 1.0
            )
            print(f"    ✅ Connected: {u_name} <---> {v_name}")
        else:
            print(
                f"    ❌ Failed to connect (Exceeds tolerance or connects to same node)"
            )

    return G, settlement_lookup
