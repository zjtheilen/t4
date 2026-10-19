import geopandas as gpd
import networkx as nx
from shapely.geometry import Point

gpkg_path = "experiments/graphic-spike/eldmere.gpkg"


def build_routing_engine():
  print("=== T⁴ NETWORK ROUTING ENGINE ===")

  # 1. Load layers and reset index
  settlements = gpd.read_file(gpkg_path, layer="settlements").reset_index()
  roads = gpd.read_file(gpkg_path, layer="roads").reset_index()

  # Build settlement lookup dictionary using the reliable pandas index or fid
  settlement_lookup = {}
  for idx, row in settlements.iterrows():
    s_id = row.get("fid", idx)
    s_name = row.get("name", f"Settlement {s_id}")
    settlement_lookup[s_id] = s_name

  # 2. Initialize NetworkX Graph
  G = nx.Graph()

  for idx, row in settlements.iterrows():
    s_id = row.get("fid", idx)
    G.add_node(s_id, name=row.get("name", f"Settlement {s_id}"), geometry=row["geometry"])

  print("\n--- Mapping Roads to Settlements ---")
  for idx, road in roads.iterrows():
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
      # Avoid snapping both ends to the exact same settlement if possible
      dist = end_pt.distance(s_row["geometry"])
      if dist < min_end_dist:
        min_end_dist = dist
        end_settlement = s_id

    # If both ends snapped to the same settlement, find the second closest for the end
    if start_settlement == end_settlement:
      second_min_end_dist = float("inf")
      second_end_settlement = None
      for s_idx, s_row in settlements.iterrows():
        s_id = s_row.get("fid", s_idx)
        if s_id == start_settlement:
          continue
        dist = end_pt.distance(s_row["geometry"])
        if dist < second_min_end_dist:
          second_min_end_dist = dist
          second_end_settlement = s_id
      if second_end_settlement is not None:
        end_settlement = second_end_settlement
        min_end_dist = second_min_end_dist

    length_km = line.length / 1000.0
    start_name = settlement_lookup.get(start_settlement, "Unknown")
    end_name = settlement_lookup.get(end_settlement, "Unknown")

    print(
        f"Road {idx}: {start_name} (ID {start_settlement}) ➔ {end_name} (ID {end_settlement})"
        f" [Len: {length_km:.3f}km]"
    )

    if start_settlement is not None and end_settlement is not None and start_settlement != end_settlement:
      G.add_edge(start_settlement, end_settlement, weight=length_km)
      print("  ✅ Added to graph.")
    else:
      print("  ⚠️ Skipped: Invalid edge connection.")

  print(
      f"\nSuccessfully built graph: {G.number_of_nodes()} nodes,"
      f" {G.number_of_edges()} edges."
  )

  # 3. Test Pathfinding
  if G.number_of_edges() > 0:
    nodes = list(G.nodes)
    source, target = nodes[0], nodes[-1]
    source_name = G.nodes[source]["name"]
    target_name = G.nodes[target]["name"]

    print(f"\n--- Pathfinding: {source_name} ➔ {target_name} ---")
    try:
      path = nx.shortest_path(G, source=source, target=target, weight="weight")
      path_length_km = nx.shortest_path_length(
          G, source=source, target=target, weight="weight"
      )

      path_names = [G.nodes[n]["name"] for n in path]
      hexes_crossed = round(path_length_km / 5.0, 1)
      days_traveled = round(path_length_km / 25.0, 2)
      rations_consumed = max(1, round(days_traveled * 2))

      print(f"  - Optimal Route: {' ➔ '.join(path_names)}")
      print(f"  - Total Distance: {path_length_km * 1000:.2f} meters")
      print(f"  - Hexes Crossed: {hexes_crossed}")
      print(f"  - Travel Time: {days_traveled} days")
      print(f"  - Rations Consumed: {rations_consumed} units")

    except nx.NetworkXNoPath:
      print("  - No path found between these settlements!")
  else:
    print("\n⚠️ Graph has no edges. Check your road geometry connections in QGIS.")


if __name__ == "__main__":
  build_routing_engine()