```
╭━━━━┳╮ ╭╮   ╭╮               ╭╮╭╮  ╭╮         ╭╮   ╭╮            ╭━╮     ╭╮
┃╭╮╭╮┃┃ ┃┃   ┃╰┳━┳━┳━┳━┳┳┳━╮╭━┫╰╋╋━╮┃╰┳━┳┳┳┳┳━╮┣╋━┳╮┃╰┳┳┳━┳━┳━┳━┳┳┫━╋━╮╭╮ ┃╰┳━┳━┳╮
╰╯┃┃╰┫╰━╯┃   ┃╭┫╋┃╋┃╋┃╋┃╭┫╋╰┫╋┃┃┃┃━┫┃╭┫┻┫╭┫╭┫╋╰┫┃┃┃┃┃╭┫╭┫╋╰╮┃╭┫┻┫╭╋━┃╋╰┫╰╮┃╭┫╋┃╋┃╰╮
  ┃┃ ╰━━╮┃   ╰━┻━┫╭┻━╋╮┣╯╰━━┫╭┻┻┻┻━╯╰━┻━┻╯╰╯╰━━┻┻┻━╯╰━┻╯╰━━┻━╯╰━┻╯╰━┻━━┻━╯╰━┻━┻━┻━╯
  ┃┃    ┃┃       ╰╯  ╰━╯    ╰╯
  ╰╯    ╰╯
```

# T⁴ — Topographic Terrain Traversal Tool

> A geospatial traversal and logistics tool for fictional tabletop worlds.

**T⁴** (Topographic Terrain Traversal Tool) explores what happens when geography becomes computationally meaningful rather than merely visual.

The project models a fictional world as spatial data and uses that geography to calculate traversal, routing, and logistical consequences.

The central idea is:

> **What happens when a game world actually understands where things are?**

A journey should not simply be a line drawn between two points. Geography, routes, terrain, and changing world conditions affect what that journey costs and how it unfolds across fantasy overworlds, dungeon crawls, and surreal survival environments.

## Current Status

**Active Prototype — Phase 2: Core Engine Stability & Itinerary Routing**

T⁴ has moved past initial concept validation. The core Python package (`src/t4/`) is established, featuring GeoPackage data ingestion, spatial endpoint snapping, effort-weighted Dijkstra routing, multi-stop itinerary sequencing, and automated round-trip persistence back to QGIS.

## Core Capabilities

- **Spatial Endpoint Snapping:** Automatically bridges coordinate offsets between road line endpoints and settlement nodes using tolerance-based matching.
- **Effort-Weighted Dijkstra Routing:** Computes optimal paths factoring in physical distance and terrain friction multipliers (paved, rough, mountain, swamp).
- **Two-Tier Blockage Model:** Handles hard structural blockages (`closed`, `destroyed`) by dropping edges from the graph to force dynamic detours, while supporting soft hazard penalties.
- **Multi-Stop Itinerary Chaining:** Calculates multi-node trade loops and journeys, accumulating total distance, travel time, and resource consumption across all legs.
- **GIS Round-Trip Persistence:** Exports computed route geometries and operational metadata directly back into the GeoPackage `active_routes` layer for visualization in QGIS.

## Guiding Principles

### Geography is data

Geographic features are represented as meaningful spatial data rather than decorative map elements.

### Geography affects computation

Location, terrain, routes, and geographic constraints influence calculations performed by the system.

### World state can change consequences

A change to the world alters traversal and logistical results.

### Results should be explainable

The system shows how it arrived at a route or logistical result rather than presenting unexplained numbers.

### Prefer explicit systems over autonomous simulation

T⁴ calculates consequences from an explicitly defined world state without requiring an autonomous civilization simulator.

## Technical Architecture

The active implementation stack consists of:

- **Geographic Authoring & Visualization:** QGIS + GeoPackage (`.gpkg`)
- **Spatial Data Handling:** GeoPandas / Shapely (`src/t4/db.py`)
- **Topological Graph & Snapping:** NetworkX (`src/t4/graph.py`)
- **Routing & Ledger Engine:** Python (`src/t4/engine.py`)
- **Interface/CLI:** Python execution runner (`run.py`)
- **Future Presentation Layer:** React + TypeScript + MapLibre GL JS + FastAPI backend

## Explicit Non-Goals

T⁴ is not intended to be:

- a virtual tabletop (VTT);
- a combat engine;
- a general RPG rules engine;
- a character-management system;
- a multiplayer game;
- a procedural world generator;
- an autonomous civilization simulator;
- a full economic or weather simulator.
