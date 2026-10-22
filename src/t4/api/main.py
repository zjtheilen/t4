from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from collections import deque
import math

app = FastAPI(title="T4 Spatial Logistics Engine", version="1.9.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "r2": {"status": "closed", "reason": "Bridge Collapse / Washout"},
}

NODES = {
    "oakhaven": {"id": "oakhaven", "name": "Oakhaven", "coordinates": [-117.1611, 32.7157], "type": "settlement"},
    "riverbend": {"id": "riverbend", "name": "Riverbend", "coordinates": [-117.2500, 32.7500], "type": "settlement"},
    "northgate": {"id": "northgate", "name": "Northgate", "coordinates": [-117.1000, 32.8000], "type": "settlement"},
    "ironhold": {"id": "ironhold", "name": "Ironhold", "coordinates": [-117.0500, 32.6800], "type": "settlement"},
}

ROADS = {
    "r1": {"nodes": {"oakhaven", "riverbend"}, "type": "primary", "coords": [[-117.1611, 32.7157], [-117.2500, 32.7500]]},
    "r2": {"nodes": {"riverbend", "northgate"}, "type": "primary", "coords": [[-117.2500, 32.7500], [-117.1000, 32.8000]]},
    "r3": {"nodes": {"oakhaven", "northgate"}, "type": "secondary", "coords": [[-117.1611, 32.7157], [-117.1000, 32.8000]]},
    "r4": {"nodes": {"oakhaven", "ironhold"}, "type": "secondary", "coords": [[-117.1611, 32.7157], [-117.0500, 32.6800]]},
    "r5": {"nodes": {"northgate", "ironhold"}, "type": "trail", "coords": [[-117.1000, 32.8000], [-117.0500, 32.6800]]}
}

PROFILES = {
    "dcc_death_sport": {
        "id": "dcc_death_sport",
        "name": "DCC Death Sport (Post-Apoc / Fast)",
        "speed_mult": 1.5,
        "color": "#f43f5e",
        "dasharray": [1, 0],
        "dist_unit": "Leagues",
        "time_unit": "Watch Shifts"
    },
    "foot_march": {
        "id": "foot_march",
        "name": "Standard Foot March",
        "speed_mult": 1.0,
        "color": "#3b82f6",
        "dasharray": [1, 0],
        "dist_unit": "Miles",
        "time_unit": "Hours"
    },
    "heavy_wagon": {
        "id": "heavy_wagon",
        "name": "Heavy Trade Wagon (Slow / Rugged)",
        "speed_mult": 0.6,
        "color": "#d97706",
        "dasharray": [4, 3],
        "dist_unit": "Miles",
        "time_unit": "Hours"
    }
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
    dx = (coord2[0] - coord1[0]) * 53.0
    dy = (coord2[1] - coord1[1]) * 69.0
    return math.sqrt(dx * dx + dy * dy)

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
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": rdata["coords"]
            },
            "properties": {
                "road_id": rid,
                "type": rdata["type"],
                "status": override["status"],
                "reason": override["reason"]
            }
        })
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
            "reason": req.reason or "Active Campaign Hazard"
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
    
    for i in range(len(raw_itinerary) - 1):
        u = raw_itinerary[i]
        v = raw_itinerary[i+1]
        
        sub_path = find_path_between(u, v, ACTIVE_OVERRIDES)
        if not sub_path:
            raise HTTPException(
                status_code=400,
                detail=f"Route blocked: No open road path between {NODES[u]['name']} and {NODES[v]['name']} due to active road closures."
            )
            
        if len(sub_path) > 2:
            rerouted = True
            detour_names = ", ".join([NODES[n]["name"] for n in sub_path[1:-1]])
            notices.append(f"Leg {NODES[u]['name']} ➔ {NODES[v]['name']} re-routed via {detour_names}.")
            
        for node_idx in range(1, len(sub_path)):
            prev_node = sub_path[node_idx - 1]
            curr_node = sub_path[node_idx]
            resolved_path_nodes.append(curr_node)
            
            _, rdata = get_road_between(prev_node, curr_node)
            if rdata:
                total_dist += calculate_distance(rdata["coords"][0], rdata["coords"][1])

    coordinates = [NODES[n]["coordinates"] for n in resolved_path_nodes]
    mult = profile_cfg["speed_mult"]
    
    final_dist = round(total_dist * (0.85 if profile_cfg["dist_unit"] == "Leagues" else 1.0), 1)
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
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "profile": req.profile,
                "stops": resolved_path_nodes,
                "rerouted": rerouted
            }
        }
    }

@app.post("/api/export-handout")
def export_handout(req: HandoutExportRequest):
    origin_name = NODES.get(req.origin, {}).get("name", req.origin)
    path_names = [NODES.get(n, {}).get("name", n) for n in req.route_result.get("itinerary", [])]
    
    md_lines = [
        "# T⁴ Spatial Logistics — Campaign Handout",
        f"**Travel Profile:** {req.route_result.get('profile_name')}",
        f"**Origin / Base:** {origin_name}",
        f"**Itinerary Path:** {' ➔ '.join(path_names)}",
        "",
        "## Travel Metrics",
        f"- **Total Distance:** {req.route_result.get('total_distance')} {req.route_result.get('dist_unit')}",
        f"- **Estimated Duration:** {req.route_result.get('estimated_travel_time')} {req.route_result.get('time_unit')}",
        ""
    ]
    
    if req.route_result.get("notice"):
        md_lines.extend([
            "## World-State Re-Routing Notices",
            f"> {req.route_result.get('notice')}",
            ""
        ])
        
    if ACTIVE_OVERRIDES:
        md_lines.extend([
            "## Active Campaign Road Hazards",
            "| Road ID | Status | Reason / Note |",
            "| :--- | :--- | :--- |"
        ])
        for rid, odata in ACTIVE_OVERRIDES.items():
            md_lines.append(f"| `{rid}` | {odata['status'].upper()} | {odata['reason']} |")
        md_lines.append("")
        
    md_lines.append("--- *Generated by T⁴ Topographic Terrain Traversal Tool*")
    
    return {"markdown": "\n".join(md_lines)}