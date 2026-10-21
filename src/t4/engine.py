# src/t4/engine.py
import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.ops import unary_union
from .profiles import PROFILES


class RoutingEngine:
    def __init__(
        self,
        gpkg_path: str,
        G: nx.Graph,
        settlement_lookup: dict,
        profile_key: str = "fantasy_overland",
    ):
        self.gpkg_path = gpkg_path
        self.G = G
        self.settlement_lookup = settlement_lookup
        self.profile = PROFILES.get(profile_key, PROFILES["fantasy_overland"])

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
        hazard_warnings = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.G.get_edge_data(u, v)
            if edge_data:
                total_physical_km += edge_data["length_km"]
                total_effort_weight += edge_data["weight"]
                if "geometry" in edge_data:
                    edge_geoms.append(edge_data["geometry"])

                # Collect soft hazards for explanation
                if edge_data.get("condition") == "hazard":
                    r_id = edge_data.get("road_id")
                    s_text = edge_data.get("status_text")
                    hazard_warnings.append(
                        f"Road {r_id} encounter: {s_text} (Hazard penalty applied)"
                    )

        path_names = [self.settlement_lookup.get(n, str(n)) for n in path]
        hex_scale = self.profile["hex_scale_km"]
        hexes_crossed = round(total_physical_km / hex_scale, 1)

        time_units = round(total_physical_km / self.profile["km_per_time_unit"], 2)
        resources_consumed = round(time_units * self.profile["resource_burn_rate"], 1)

        return {
            "path": path,
            "path_names": path_names,
            "total_physical_km": total_physical_km,
            "total_effort_weight": total_effort_weight,
            "hexes_crossed": hexes_crossed,
            "time_units_traveled": time_units,
            "time_unit_name": self.profile["time_unit"],
            "resources_consumed": resources_consumed,
            "resource_name": self.profile["resource_name"],
            "edge_geoms": edge_geoms,
            "hazard_warnings": hazard_warnings,
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
                    "time_val": route_result["time_units_traveled"],
                    "res_val": route_result["resources_consumed"],
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
        name_to_id = {v: k for k, v in self.settlement_lookup.items()}

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
        all_hazard_warnings = []

        for i in range(len(stop_ids) - 1):
            # seg_source = stop_ids[i]
            # seg_target = stop_ids[i + 1]

            seg_result = self.find_route(stop_ids[i], stop_ids[i + 1])

            if i == 0:
                full_path.extend(seg_result["path"])
                full_path_names.extend(seg_result["path_names"])
            else:
                full_path.extend(seg_result["path"][1:])
                full_path_names.extend(seg_result["path_names"][1:])

            total_physical_km += seg_result["total_physical_km"]
            total_effort_weight += seg_result["total_effort_weight"]
            all_edge_geoms.extend(seg_result["edge_geoms"])

            all_hazard_warnings.extend(seg_result.get("hazard_warnings", []))

        hex_scale = self.profile["hex_scale_km"]
        hexes_crossed = round(total_physical_km / hex_scale, 1)
        time_units = round(total_physical_km / self.profile["km_per_time_unit"], 2)
        resources_consumed = round(time_units * self.profile["resource_burn_rate"], 1)

        return {
            "path": full_path,
            "path_names": full_path_names,
            "total_physical_km": total_physical_km,
            "total_effort_weight": total_effort_weight,
            "hexes_crossed": hexes_crossed,
            "time_units_traveled": time_units,
            "time_unit_name": self.profile["time_unit"],
            "resources_consumed": resources_consumed,
            "resource_name": self.profile["resource_name"],
            "edge_geoms": all_edge_geoms,
            "hazard_warnings": all_hazard_warnings,
        }
