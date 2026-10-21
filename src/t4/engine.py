# src/t4/engine.py
import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.ops import unary_union


class RoutingEngine:
    def __init__(self, gpkg_path: str, G: nx.Graph, settlement_lookup: dict):
        self.gpkg_path = gpkg_path
        self.G = G
        self.settlement_lookup = settlement_lookup

    def find_route(self, source, target):
        """Finds the optimal route between source and target using effort-weighted Dijkstra."""
        source_name = self.settlement_lookup.get(source, f"Node {source}")
        target_name = self.settlement_lookup.get(target, f"Node {target}")

        if source not in self.G or target not in self.G:
            raise ValueError(
                f"Source ({source_name}) or target ({target_name}) not found in graph topology."
            )

        # Run Dijkstra optimization using effort weights
        path = nx.shortest_path(self.G, source=source, target=target, weight="weight")

        # Calculate metrics along the path
        total_physical_km = 0
        total_effort_weight = 0
        edge_geoms = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.G.get_edge_data(u, v)
            if edge_data:
                total_physical_km += edge_data["length_km"]
                total_effort_weight += edge_data["weight"]
                if "geometry" in edge_data:
                    edge_geoms.append(edge_data["geometry"])

        path_names = [self.settlement_lookup.get(n, str(n)) for n in path]
        hexes_crossed = round(total_physical_km / 5.0, 1)
        days_traveled = round(
            total_physical_km / 25.0, 2
        )  # Assuming 25km per day baseline
        rations_consumed = max(1, round(days_traveled * 2))

        return {
            "path": path,
            "path_names": path_names,
            "total_physical_km": total_physical_km,
            "total_effort_weight": total_effort_weight,
            "hexes_crossed": hexes_crossed,
            "days_traveled": days_traveled,
            "rations_consumed": rations_consumed,
            "edge_geoms": edge_geoms,
        }

    def export_route_to_gpkg(self, route_result: dict, route_name: str = None):
        """Writes the computed route geometry and ledger back to the GeoPackage active_routes layer."""
        edge_geoms = route_result["edge_geoms"]
        if not edge_geoms:
            return False

        path_names = route_result["path_names"]
        if not route_name:
            route_name = f"{path_names[0]} to {path_names[-1]}"

        combined_geom = unary_union(edge_geoms)

        try:
            existing_routes = gpd.read_file(self.gpkg_path, layer="active_routes")
        except Exception:
            existing_routes = None

        route_gdf = gpd.GeoDataFrame(
            [
                {
                    "route": route_name,
                    "distance_m": route_result["total_physical_km"] * 1000,
                    "days": route_result["days_traveled"],
                    "rations": route_result["rations_consumed"],
                    "geometry": combined_geom,
                }
            ],
            crs="EPSG:4326",
        )

        if existing_routes is not None and not existing_routes.empty:
            combined_gdf = gpd.GeoDataFrame(
                pd.concat([existing_routes, route_gdf], ignore_index=True)
            )
        else:
            combined_gdf = route_gdf

        combined_gdf.to_file(self.gpkg_path, layer="active_routes", driver="GPKG")
        return True

    def find_itinerary(self, stop_names: list):
        """Calculates a multi-stop route, chaining segments and accumulating ledger resources."""
        # Create a forward lookup from name to node ID
        name_to_id = {v: k for k, v in self.settlement_lookup.items()}

        # Convert names to node IDs
        stop_ids = []
        for name in stop_names:
            if name not in name_to_id:
                raise ValueError(f"Settlement '{name}' not found in graph topology.")
            stop_ids.append(name_to_id[name])

        if len(stop_ids) < 2:
            raise ValueError("An itinerary requires at least 2 stops.")

        full_path = []
        full_path_names = []
        total_physical_km = 0.0
        total_effort_weight = 0.0
        all_edge_geoms = []

        # Chain segments together sequentially (e.g., A->B, then B->C)
        for i in range(len(stop_ids) - 1):
            seg_source = stop_ids[i]
            seg_target = stop_ids[i + 1]

            # Run single-segment find_route logic under the hood
            # (or extract directly)
            seg_result = self.find_route(seg_source, seg_target)

            # Append path nodes (avoiding duplicate nodes at segment junctions)
            if i == 0:
                full_path.extend(seg_result["path"])
                full_path_names.extend(seg_result["path_names"])
            else:
                full_path.extend(seg_result["path"][1:])
                full_path_names.extend(seg_result["path_names"][1:])

            total_physical_km += seg_result["total_physical_km"]
            total_effort_weight += seg_result["total_effort_weight"]
            all_edge_geoms.extend(seg_result["edge_geoms"])

        hexes_crossed = round(total_physical_km / 5.0, 1)
        days_traveled = round(total_physical_km / 25.0, 2)
        rations_consumed = max(len(stop_ids), round(days_traveled * 2))

        return {
            "path": full_path,
            "path_names": full_path_names,
            "total_physical_km": total_physical_km,
            "total_effort_weight": total_effort_weight,
            "hexes_crossed": hexes_crossed,
            "days_traveled": days_traveled,
            "rations_consumed": rations_consumed,
            "edge_geoms": all_edge_geoms,
        }
