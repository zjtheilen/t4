import json
import math
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="T4 Spatial Logistics Engine", version="1.9.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



DATA_PATH = Path(__file__).parent.parent / "data" / "world.json"


def load_world_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        # Fallback empty structure if file doesn't exist yet
        return {"nodes": {}, "roads": {}, "overrides": {}}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_world_data(data: Dict[str, Any]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Initialize in-memory or request-time state from world.json
world_state = load_world_data()
NODES = world_state.get("nodes", {})
ROADS = world_state.get("roads", {})
ACTIVE_OVERRIDES = world_state.get("overrides", {})

# ACTIVE_OVERRIDES: Dict[str, Dict[str, Any]] = {
#     "r2": {"status": "closed", "reason": "Bridge Collapse / Washout"},
# }

# NODES = {
#     "oakhaven": {
#         "id": "oakhaven",
#         "name": "Oakhaven",
#         "coordinates": [251, 492],
#         "type": "major_hub",
#     },
#     "northgate": {
#         "id": "northgate",
#         "name": "Northgate",
#         "coordinates": [484, 92],
#         "type": "minor_settlement",
#     },
#     "highbridge": {
#         "id": "highbridge",
#         "name": "Highbridge",
#         "coordinates": [508, 391],
#         "type": "major_hub",
#     },
#     "eastwatch": {
#         "id": "eastwatch",
#         "name": "Eastwatch",
#         "coordinates": [870, 452],
#         "type": "minor_settlement",
#     },
#     "ironhold": {
#         "id": "ironhold",
#         "name": "Ironhold",
#         "coordinates": [1023, 341],
#         "type": "major_hub",
#     },
#     "riverbend": {
#         "id": "riverbend",
#         "name": "Riverbend",
#         "coordinates": [649, 642],
#         "type": "minor_settlement",
#     },
#     "valeside": {
#         "id": "valeside",
#         "name": "Valeside",
#         "coordinates": [867, 661],
#         "type": "minor_settlement",
#     },
#     "ruined_tower": {
#         "id": "ruined_tower",
#         "name": "Ruined Tower",
#         "coordinates": [804, 244],
#         "type": "minor_settlement",
#     },
#     "king_junction": {
#         "id": "king_junction",
#         "name": "King Junction",
#         "coordinates": [366, 319],
#         "type": "fork"
#     },
#     "river_crossing": {
#         "id": "river_crossing",
#         "name": "River Crossing",
#         "coordinates": [579, 648],
#         "type": "fork"
#     },
#     "highbridge_fork": {
#         "id": "highbridge_fork",
#         "name": "Highbridge Fork",
#         "coordinates": [688, 407],
#         "type": "fork"
#     }
# }

# ROADS = {
#     # King's Road (Split into segments via king_junction)
#     "r1_north": {"nodes": {"northgate", "king_junction"}, "type": "primary", "coords": [[484, 92], [399, 178], [392, 218], [407, 257], [366, 319]]},
#     "r1_south": {"nodes": {"king_junction", "oakhaven"}, "type": "primary", "coords": [[366, 319], [251, 492]]},

#     # Perpendicular Fork from King's Junction toward Highbridge
#     "r_fork_east": {"nodes": {"king_junction", "highbridge"}, "type": "trail", "coords": [[366, 319], [462, 351], [508, 391]]},

#     # Oakhaven to Highbridge Direct
#     "r2": {"nodes": {"oakhaven", "highbridge"}, "type": "primary", "coords": [[251, 492], [381, 455], [508, 391]]},

#     # Highbridge to Eastwatch (Split at Highbridge Crossing)
#     "r3_west": {"nodes": {"highbridge", "highbridge_fork"}, "type": "primary", "coords": [[508, 391], [622, 391], [688, 407]]},
#     "r3_east": {"nodes": {"highbridge_fork", "eastwatch"}, "type": "primary", "coords": [[688, 407], [683, 402], [793, 440], [870, 452]]},

#     # Eastwatch to Ironhold (Mountain Pass)
#     "r4": {"nodes": {"eastwatch", "ironhold"}, "type": "mountain_pass", "coords": [[870, 452], [912, 428], [883, 380], [1023, 341]]},

#     # Riverbend to Eastwatch
#     "r5": {"nodes": {"riverbend", "eastwatch"}, "type": "trail", "coords": [[649, 642], [726, 635], [753, 585], [870, 452]]},

#     # TODO: correct path
#     # Oakhaven to Riverbend (Split at River Crossing Bridge)
#     "r6_north": {"nodes": {"oakhaven", "river_crossing"}, "type": "primary", "coords": [[251, 492], [320, 478], [469, 535], [502, 605], [561, 618],  [579, 648]]},
#     "r6_south": {"nodes": {"river_crossing", "riverbend"}, "type": "primary", "coords": [[579, 648], [649, 642]]},

#     # TODO: correct path
#     # Older, less maintained parallel trail between Oakhaven and Riverbend (Lower Gate)
#     "r_old_track": {"nodes": {"oakhaven", "river_crossing"}, "type": "trail", "coords": [[251, 492], [289, 531], [388, 576], [432, 607], [461, 611], [472, 631], [546, 651], [579, 648]]},

#     # Northgate to Ruined Tower (Note: crosses river via guarded ferry/ford)
#     "r7": {"nodes": {"northgate", "ruined_tower"}, "type": "trail", "coords": [[484, 92], [667, 158], [733, 184], [767, 203], [804, 244]]},

#     # Valeside to Riverbend
#     "r8": {"nodes": {"valeside", "riverbend"}, "type": "trail", "coords": [[867, 661], [813, 681], [752, 713], [680, 668], [649, 642]]},

#     # Ruined Tower to Eastwatch
#     "r9": {"nodes": {"ruined_tower", "eastwatch"}, "type": "trail", "coords": [[804, 244], [808, 306], [815, 351], [840, 377], [847, 441], [870, 452]]},

#     # TODO: correct path
#     # Trail: Highbridge Crossing to Ruined Tower
#     "r_crossing_to_tower": {"nodes": {"highbridge_fork", "ruined_tower"}, "type": "trail", "coords": [[688, 407], [687, 401], [770, 360], [804, 292], [804, 244]]},

#     # TODO: correct path
#     # Mountain Pass: Ruined Tower to Ironhold
#     "r_tower_to_ironhold": {"nodes": {"ruined_tower", "ironhold"}, "type": "mountain_pass", "coords": [[804, 244], [842, 249], [919, 304], [958, 346], [1023, 341]]}
# }

PROFILES = {
    "dcc_death_sport": {
        "id": "dcc_death_sport",
        "name": "DCC Death Sport (Post-Apoc / Fast)",
        "speed_mult": 1.5,
        "color": "#f43f5e",
        "dasharray": [1, 0],
        "dist_unit": "Leagues",
        "time_unit": "Watch Shifts",
    },
    "foot_march": {
        "id": "foot_march",
        "name": "Standard Foot March",
        "speed_mult": 1.0,
        "color": "#3b82f6",
        "dasharray": [1, 0],
        "dist_unit": "Miles",
        "time_unit": "Hours",
    },
    "heavy_wagon": {
        "id": "heavy_wagon",
        "name": "Heavy Trade Wagon (Slow / Rugged)",
        "speed_mult": 0.6,
        "color": "#d97706",
        "dasharray": [4, 3],
        "dist_unit": "Miles",
        "time_unit": "Hours",
    },
}


class RouteRequest(BaseModel, extra="ignore"):
    origin: str
    stops: List[str]
    profile: str = "dcc_death_sport"


class OverrideToggleRequest(BaseModel):
    road_id: str
    status: str
    reason: str = ""


class HandoutExportRequest(BaseModel):
    origin: str
    stops: List[str]
    profile: str
    route_result: Dict[str, Any]


def get_road_between(node_a, node_b):
    for rid, rdata in ROADS.items():
        if rdata["nodes"] == {node_a, node_b}:
            return rid, rdata
    return None, None


def find_path_between(start_node, end_node, active_overrides):
    if start_node == end_node:
        return [start_node]

    adj = {}
    for rid, rdata in ROADS.items():
        if active_overrides.get(rid, {}).get("status") == "closed":
            continue
        n_list = list(rdata["nodes"])
        if len(n_list) == 2:
            u, v = n_list[0], n_list[1]
            adj.setdefault(u, []).append(v)
            adj.setdefault(v, []).append(u)

    queue = deque([[start_node]])
    visited = {start_node}

    while queue:
        path = queue.popleft()
        curr = path[-1]
        if curr == end_node:
            return path
        for neighbor in adj.get(curr, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def calculate_distance(coord1, coord2):
    dx = coord2[0] - coord1[0]
    dy = coord2[1] - coord1[1]
    pixel_distance = math.sqrt(dx * dx + dy * dy)
    return round(pixel_distance * 0.1, 1)


@app.get("/api/health")
def health_check():
    return {"status": "active", "engine": "T4 Topographic Terrain Traversal Tool"}


@app.get("/api/nodes")
def get_nodes():
    return list(NODES.values())


@app.get("/api/profiles")
def get_profiles():
    return list(PROFILES.values())


@app.get("/api/roads")
def get_roads():
    features = []
    for rid, rdata in ROADS.items():
        override = ACTIVE_OVERRIDES.get(rid, {"status": "open", "reason": ""})
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": rdata["coords"]},
                "properties": {
                    "road_id": rid,
                    "type": rdata["type"],
                    "status": override["status"],
                    "reason": override["reason"],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/overrides")
def get_overrides():
    return ACTIVE_OVERRIDES


@app.post("/api/overrides/toggle")
def toggle_override(req: OverrideToggleRequest):
    if req.status == "open":
        if req.road_id in ACTIVE_OVERRIDES:
            del ACTIVE_OVERRIDES[req.road_id]
    else:
        ACTIVE_OVERRIDES[req.road_id] = {
            "status": req.status,
            "reason": req.reason or "Active Campaign Hazard",
        }
    return {"status": "success", "active_overrides": ACTIVE_OVERRIDES}


@app.post("/api/optimize-route")
def optimize_route(req: RouteRequest):
    profile_cfg = PROFILES.get(req.profile, PROFILES["foot_march"])
    raw_itinerary = [req.origin] + req.stops + [req.origin]

    resolved_path_nodes = [raw_itinerary[0]]
    total_dist = 0.0
    rerouted = False
    notices = []
    route_coordinates = []

    for i in range(len(raw_itinerary) - 1):
        u = raw_itinerary[i]
        v = raw_itinerary[i + 1]

        sub_path = find_path_between(u, v, ACTIVE_OVERRIDES)
        if not sub_path:
            raise HTTPException(
                status_code=400,
                detail=f"Route blocked: No open road path between {NODES[u]['name']} and {NODES[v]['name']} due to active road closures.",
            )

        if len(sub_path) > 2:
            rerouted = True
            detour_names = ", ".join([NODES[n]["name"] for n in sub_path[1:-1]])
            notices.append(
                f"Leg {NODES[u]['name']} ➔ {NODES[v]['name']} re-routed via {detour_names}."
            )

        for node_idx in range(1, len(sub_path)):
            prev_node = sub_path[node_idx - 1]
            curr_node = sub_path[node_idx]
            resolved_path_nodes.append(curr_node)

            rid, rdata = get_road_between(prev_node, curr_node)
            if rdata:
                road_coords = list(rdata["coords"])
                # Ensure correct direction (if road coords start at curr_node, reverse them)
                if road_coords[0] != NODES[prev_node]["coordinates"]:
                    road_coords = list(reversed(road_coords))

                # Append coordinates (avoiding duplicate points at junction nodes)
                if route_coordinates:
                    route_coordinates.extend(road_coords[1:])
                else:
                    route_coordinates.extend(road_coords)

                # Sum distance across all bend segments
                for idx in range(1, len(road_coords)):
                    total_dist += calculate_distance(
                        road_coords[idx - 1], road_coords[idx]
                    )

    # Fallback if no route coordinates accumulated
    if not route_coordinates:
        route_coordinates = [NODES[n]["coordinates"] for n in resolved_path_nodes]

    mult = profile_cfg["speed_mult"]
    final_dist = round(
        total_dist * (0.85 if profile_cfg["dist_unit"] == "Leagues" else 1.0), 1
    )
    final_time = round(final_dist / mult, 1)

    return {
        "profile": req.profile,
        "profile_name": profile_cfg["name"],
        "color": profile_cfg["color"],
        "dasharray": profile_cfg["dasharray"],
        "dist_unit": profile_cfg["dist_unit"],
        "time_unit": profile_cfg["time_unit"],
        "itinerary": resolved_path_nodes,
        "rerouted": rerouted,
        "notice": " | ".join(notices) if notices else None,
        "total_distance": final_dist,
        "estimated_travel_time": final_time,
        "geojson": {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": route_coordinates},
            "properties": {
                "profile": req.profile,
                "stops": resolved_path_nodes,
                "rerouted": rerouted,
            },
        },
    }


@app.post("/api/export-handout")
def export_handout(req: HandoutExportRequest):
    origin_name = NODES.get(req.origin, {}).get("name", req.origin)
    path_names = [
        NODES.get(n, {}).get("name", n) for n in req.route_result.get("itinerary", [])
    ]

    md_lines = [
        "# T⁴ Spatial Logistics — Campaign Handout",
        f"**Travel Profile:** {req.route_result.get('profile_name')}",
        f"**Origin / Base:** {origin_name}",
        f"**Itinerary Path:** {' ➔ '.join(path_names)}",
        "",
        "## Travel Metrics",
        f"- **Total Distance:** {req.route_result.get('total_distance')} {req.route_result.get('dist_unit')}",
        f"- **Estimated Duration:** {req.route_result.get('estimated_travel_time')} {req.route_result.get('time_unit')}",
        "",
    ]

    if req.route_result.get("notice"):
        md_lines.extend(
            [
                "## World-State Re-Routing Notices",
                f"> {req.route_result.get('notice')}",
                "",
            ]
        )

    if ACTIVE_OVERRIDES:
        md_lines.extend(
            [
                "## Active Campaign Road Hazards",
                "| Road ID | Status | Reason / Note |",
                "| :--- | :--- | :--- |",
            ]
        )
        for rid, odata in ACTIVE_OVERRIDES.items():
            md_lines.append(
                f"| `{rid}` | {odata['status'].upper()} | {odata['reason']} |"
            )
        md_lines.append("")

    md_lines.append("--- *Generated by T⁴ Topographic Terrain Traversal Tool*")

    return {"markdown": "\n".join(md_lines)}
