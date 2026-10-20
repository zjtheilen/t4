import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
from shapely.ops import linemerge, unary_union

gpkg_path = "experiments/graphic-spike/eldmere.gpkg"

# Define cost multipliers for different terrain types
TERRAIN_MULTIPLIERS = {
    "paved": 1.0,  # Standard well-maintained road
    "rough": 1.5,  # Dirt track or uneven terrain
    "mountain": 2.5,  # Steep ascents, high fatigue
    "swamp": 3.0,  # Mire, heavy movement penalty
    "open": 1.0,  # Default fallback
}


def build_routing_engine():
  print("=== T⁴ TERRAIN-AWARE ROUTING ENGINE ===")

  # 1. Load layers from GeoPackage
  settlements = gpd.read_file(gpkg_path, layer="settlements").reset_index()
  roads = gpd.read_file(gpkg_path, layer="roads").reset_index()

  # Build settlement lookup dictionary
  settlement_lookup = {}
  for idx, row in settlements.iterrows():
    s_id = row.get("fid", idx)
    settlement_lookup[s_id] = row.get("name", f"Settlement {s_id}")

  # 2. Initialize NetworkX Graph
  G = nx.Graph()

  for idx, row in settlements.iterrows():
    s_id = row.get("fid", idx)
    G.add_node(
        s_id, name=row.get("name", f"Settlement {s_id}"), geometry=row["geometry"]
    )

  print("\n--- Mapping Roads, DB State, & Terrain Costs ---")
  for idx, road in roads.iterrows():
    road_id = road.get("fid", idx)
    line = road.geometry
    start_pt = Point(line.coords[0])
    end_pt = Point(line.coords[-1])

    # Find closest settlement for start
    start_settlement = None
    min_start_dist = float("inf")
    for s_idx, s_row in settlements.iterrows():
      s_id = s_row.get("fid", s_idx)
      dist = start_pt.distance(s_row["geometry"])
      if dist < min_start_dist:
        min_start_dist = dist
        start_settlement = s_id

    # Find closest settlement for end
    end_settlement = None
    min_end_dist = float("inf")
    for s_idx, s_row in settlements.iterrows():
      s_id = s_row.get("fid", s_idx)
      dist = end_pt.distance(s_row["geometry"])
      if dist < min_end_dist:
        min_end_dist = dist
        end_settlement = s_id

    if start_settlement == end_settlement:
      for s_idx, s_row in settlements.iterrows():
        s_id = s_row.get("fid", s_idx)
        if s_id != start_settlement:
          end_settlement = s_id
          break

    length_km = line.length / 1000.0
    start_name = settlement_lookup.get(start_settlement, "Unknown")
    end_name = settlement_lookup.get(end_settlement, "Unknown")

    # Read 'status' column
    status_val = road.get("status", "open")
    if pd_is_blocked(status_val):
      print(
          f"Road {road_id} ({start_name} ➔ {end_name}): ❌ BLOCKED (DB Status:"
          f" {status_val})"
      )
      continue

    # Read 'terrain' column and calculate effort weight
    terrain_type = str(road.get("terrain", "paved")).strip().lower()
    multiplier = TERRAIN_MULTIPLIERS.get(terrain_type, 1.0)
    effort_distance = length_km * multiplier

    if (
        start_settlement is not None
        and end_settlement is not None
        and start_settlement != end_settlement
    ):
      # Store effort distance as weight for Dijkstra, keep raw length for ledger
      G.add_edge(
          start_settlement,
          end_settlement,
          weight=effort_distance,  # Dijkstra optimizes for effort/time
          length_km=length_km,  # Physical distance for display
          road_id=road_id,
          geometry=line,
      )
      print(
          f"Road {road_id}: {start_name} ➔ {end_name} [Len:"
          f" {length_km:.3f}km | Terrain: {terrain_type} (x{multiplier}) | Effort"
          f" Wt: {effort_distance:.2f}] ✅ Added"
      )

  print(
      f"\nSuccessfully built active graph: {G.number_of_nodes()} nodes,"
      f" {G.number_of_edges()} active edges."
  )

  # 3. Test Pathfinding from Oakhaven (ID 0) to Northgate (ID 2)
  source, target = 0, 2
  if source in G and target in G:
    source_name = G.nodes[source]["name"]
    target_name = G.nodes[target]["name"]

    print(f"\n--- Pathfinding: {source_name} ➔ {target_name} ---")
    try:
      path = nx.shortest_path(G, source=source, target=target, weight="weight")

      # Calculate total physical distance vs total effort weight
      total_physical_km = 0
      edge_geoms = []
      for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.get_edge_data(u, v)
        if edge_data:
          total_physical_km += edge_data["length_km"]
          if "geometry" in edge_data:
            edge_geoms.append(edge_data["geometry"])

      path_names = [G.nodes[n]["name"] for n in path]
      hexes_crossed = round(total_physical_km / 5.0, 1)
      days_traveled = round(total_physical_km / 25.0, 2)
      rations_consumed = max(1, round(days_traveled * 2))

      print(f"  - Optimal Route: {' ➔ '.join(path_names)}")
      print(f"  - Physical Distance: {total_physical_km * 1000:.2f} meters")
      print(f"  - Hexes Crossed: {hexes_crossed}")
      print(f"  - Travel Time: {days_traveled} days")
      print(f"  - Rations Consumed: {rations_consumed} units")

      # 4. ROUND-TRIP EXPORT
      if edge_geoms:
        combined_geom = unary_union(edge_geoms)
        try:
          combined_geom = linemerge(combined_geom)
        except Exception:
          pass

        route_gdf = gpd.GeoDataFrame(
            [{
                "route": f"{source_name} to {target_name}",
                "distance_m": total_physical_km * 1000,
                "days": days_traveled,
                "rations": rations_consumed,
                "geometry": combined_geom,
            }],
            crs=roads.crs,
        )

        route_gdf.to_file(gpkg_path, layer="active_routes", driver="GPKG")
        print(
            "  💾 Route successfully written back to GeoPackage layer"
            " 'active_routes'!"
        )

    except nx.NetworkXNoPath:
      print("  ⚠️ CRITICAL: No path found! The region is entirely cut off.")


def pd_is_blocked(val):
  if val is None:
    return False
  val_str = str(val).strip().lower()
  return val_str in ["washed_out", "blocked", "closed", "impassable"]


if __name__ == "__main__":
  build_routing_engine()