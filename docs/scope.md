# T⁴ Scope

This document defines the current scope boundaries for **T⁴ — Topographic Terrain Traversal Tool**.

Its purpose is to protect the project's central idea from being gradually replaced by adjacent systems that are interesting but unnecessary.

Scope may change as experimentation produces new evidence.

---

## 1. Core Purpose

T⁴ explores how a fictional world's geography can become computationally meaningful.

The initial system should answer questions such as:

> **Given a party, a destination, and the current state of the world, how does geography affect the journey?**

The project is primarily concerned with:

- geography;
- traversal;
- routing;
- logistics;
- changing world conditions;
- explainable consequences.

---

## 2. Initial Scope

The initial T⁴ system should contain:

### Geographic World

- hand-authored fictional geography;
- settlements;
- roads;
- meaningful geographic features;
- at least one chokepoint such as a bridge or mountain pass.

### Traversal

- starting location;
- destination;
- route calculation;
- route distance;
- traversal time;
- geographic or route-based movement modifiers.

### Party Logistics

At minimum, the system should be capable of representing constraints such as:

- movement capability;
- food consumption;
- carrying capacity.

The exact logistics model remains subject to experimentation.

### World State

A small number of explicit mutable facts may affect traversal.

The canonical example is:

> **A bridge is closed.**

The resulting route and logistical consequences should change accordingly.

### Explainability

T⁴ should be able to communicate why a result occurred.

For example:

- which route was selected;
- which segments were traversed;
- how distance was calculated;
- which conditions affected traversal;
- how those conditions affected time or supplies.

---

## 3. Architectural Boundary

The initial architecture should maintain a clear separation of responsibilities.

### Spatial Layer

Responsible for:

- geographic geometry;
- spatial relationships;
- spatial queries;
- geographic persistence.

**Candidate technology:** PostgreSQL + PostGIS

### Domain Layer

Responsible for:

- routing;
- traversal rules;
- logistics;
- world-state effects;
- consequence calculations.

**Candidate technology:** Python + FastAPI

### Presentation Layer

Responsible for:

- interactive map;
- geographic visualization;
- route visualization;
- world-state interaction;
- displaying calculations and explanations.

**Candidate technology:** React + TypeScript + MapLibre GL JS

These boundaries are intended to prevent the project from becoming a collection of tightly coupled map, database, and game logic.

---

## 4. Explicit Non-Goals

The following are **not part of the initial T⁴ scope**.

### Not a VTT

T⁴ is not intended to replace tools such as virtual tabletops.

There is no initial requirement for:

- tokens;
- battle maps;
- initiative tracking;
- dice rolling;
- character sheets;
- combat encounters.

### Not an RPG Rules Engine

T⁴ does not initially attempt to model:

- character classes;
- levels;
- abilities;
- combat;
- spells;
- inventories as a complete RPG system;
- arbitrary tabletop rulesets.

### Not a Civilization Simulator

T⁴ does not initially simulate autonomous:

- populations;
- nations;
- factions;
- settlements;
- economies;
- political systems.

The world may have state, but that state is explicitly defined rather than autonomously generated.

### Not a Procedural World Generator

The initial world will be hand-authored.

There is no requirement for:

- procedural terrain;
- procedural settlements;
- procedural roads;
- procedural civilizations;
- procedural histories.

### Not a General-Purpose GIS

T⁴ uses geospatial technology, but it is not intended to become a general GIS application.

Features should serve the traversal/logistics problem rather than exist simply because GIS software can provide them.

### Not a Multiplayer Game

Multiplayer and real-time synchronization are outside the initial scope.

### Not a Complete Economy Simulator

Resources, trade networks, markets, production chains, and economic simulation are deferred.

---

## 5. Deferred Systems

The following ideas may become relevant later, but should not shape the initial architecture.

### Terrain-Based Off-Road Movement

Potential future capability:

- forests;
- mountains;
- swamps;
- wilderness;
- cross-country movement;
- continuous terrain cost surfaces.

Initial traversal should begin with a manageable network model.

### Weather

Potential future effects:

- rain;
- snow;
- flooding;
- storms;
- seasonal conditions.

### Factions and Political Geography

Potential future effects:

- borders;
- controlled territory;
- permissions;
- hostile regions;
- checkpoints;
- closed borders.

### Resources and Trade

Potential future systems:

- resource locations;
- supply chains;
- trade routes;
- markets;
- scarcity;
- economic consequences.

### Technology

Potential future changes to capabilities:

- pack animals;
- improved roads;
- bridges;
- vehicles;
- navigation technology.

### Events

Potential future world-state changes:

- bridge destruction;
- road construction;
- flooding;
- political closures;
- disasters.

### Multiplayer

Potential future capabilities:

- shared worlds;
- multiple players;
- synchronized state;
- collaborative planning.

### Autonomous Simulation

Potential future capability:

- factions reacting to world conditions;
- economies changing over time;
- settlements responding to resource availability;
- dynamic world evolution.

Such systems should only be considered after the core consequence engine is proven.

---

## 6. Scope Escalation Rule

A proposed feature should not enter the project merely because it is interesting.

Before adding a new system, ask:

1. **Does it strengthen the central T⁴ thesis?**
2. **Does it provide a capability needed by an existing system?**
3. **Can the current scope demonstrate the idea without it?**
4. **Does adding it introduce a fundamentally different technical problem?**
5. **Has the existing core been validated sufficiently to justify the added complexity?**

If the answer is primarily "it would be cool," the feature should remain outside the current scope.

---

## 7. Minimum Interesting System

The smallest T⁴ system that should be considered successful is approximately:

```text
Settlement A
     │
     │ road
     │
   Bridge
     │
     │ road
     │
Settlement B
```

with an alternative route available elsewhere in the network.

The system should be able to:

1. represent the geographic network;
2. calculate a route;
3. calculate traversal consequences;
4. close the bridge;
5. recalculate;
6. demonstrate a different result;
7. explain why the result changed.

If this scenario is not interesting or useful, adding more world systems will not solve the underlying problem.

---

## 8. Success Criteria for the Initial Investigation

The feasibility investigation should establish that T⁴ can demonstrate:

### Spatial Understanding

The system understands geographic relationships rather than simply storing coordinates.

### Network Traversal

The system can calculate meaningful routes through a geographic network.

### Consequences

A route produces measurable consequences such as time and supplies.

### State Dependence

Changing a world condition changes those consequences.

### Explainability

The system can show how and why the result was produced.

### Architectural Separation

Geographic persistence, domain rules, and presentation can remain reasonably independent.

### Technical Viability

The chosen technologies can support the above without requiring disproportionate complexity.

---

## 9. Scope Philosophy

T⁴ should grow **outward from the traversal problem**, not inward from the fantasy world.

The project does not need to simulate an entire world to demonstrate that geography matters.

The preferred progression is:

**Geography → Traversal → Logistics → World State → Consequences**

Only after that foundation is validated should additional systems be considered.

---

## 10. Current Scope Status

**Phase:** Phase 5 Completed (Visualizer & Identity Projection Operational)

**Committed:**
Geospatial traversal and logistics as the central problem, backed by MapLibre v6 identity projection over bespoke fantasy raster assets.

---

## 11. Phase 3 Scope: Application Layer & API Integration

**Objective:** Expose the proven spatial pathfinding engine via a clean REST API and build an interactive geospatial visualization interface.

**Key Deliverables:**

1. **FastAPI Backend (`src/t4/api/`):**
    - `/api/v1/route`: Computes paths given start/end coordinates, profiles, and hazard modifiers.
    - `/api/v1/profiles`: Exposes available travel profiles and rules.
    - `/api/v1/snap`: Snaps arbitrary point coordinates to the road network graph.
2. **Interactive Frontend (`src/t4/ui/` or client app):**
    - React + MapLibre integration for visual route planning.
    - Profile selection and real-time path rendering over spatial data.
3. **Documentation & Testing:**
    - API contract docs (OpenAPI/Swagger via FastAPI).
    - Integration test suite for HTTP endpoints.

---

## 12. Phase 4 Scope: Interactive Spatial Workbench

**Objective:** Transform the T4 visualizer into an interactive planning workbench for clicking waypoints, visualizing path difficulty, inspecting map features, simulating real-time world state overrides, and exporting session notes.

**Key Deliverables:**

1. **Interactive Waypoint Builder (Map Click Routing):**
    - Click settlement nodes directly on the MapLibre canvas to queue up origin, intermediate waypoints, and destination stops.
    - UI controls for reordering, deleting, and resetting itinerary stops.
2. **Route Polyline & Terrain Difficulty Rendering:**
    - Draw calculated itinerary path segments over the road network graph.
    - Color-code path segments dynamically by terrain type and road status.
3. **Rich Feature Inspection Tooltips:**
    - Hover inspection for settlements (node ID, connected roads, properties).
    - Hover inspection for road segments (status, terrain difficulty multiplier, physical distance).
4. **Dynamic World State Overrides (Live Road Simulator):**
    - Click a road segment or toggle its status directly in its tooltip (_open_, _washed_out_, _closed_).
    - Instantly trigger an itinerary recalculation to demonstrate changing spatial consequences.
5. **Campaign Handout & Session Log Export:**
    - Export calculated route ledger and step-by-step itinerary notes to Markdown (for Notion/Obsidian) and raw JSON.

---

## 13. Phase 5 Scope: Custom Fantasy Geography & Image Source Integration

**Objective:** Replace placeholder real-world coordinates and web tiles with a bespoke, authored fantasy regional map while preserving all existing traversal, routing, world-state, and export capabilities.

**Key Deliverables:**

1. **Map Asset & Visual Integration (`client/src/App.jsx`):**
    - Integrate the generated regional fantasy map image using MapLibre's built-in `ImageSource` feature.
    - Configure precise four-corner geographic/planar bounding coordinates to align the raster map artwork with vector layers.
    - Replace the dark-matter web tile basemap with a clean, neutral tactical container/background optimized for the fantasy parchment aesthetic.

2. **Planar Coordinate & Distance Model (`src/t4/api/main.py`):**
    - Transition backend `NODES` from real-world longitude/latitude degrees to a clean planar coordinate system matching the fantasy map's layout (e.g., a local grid).
    - Replace lat/lon scaling factors with a standard Euclidean distance formula ($\sqrt{\Delta x^2 + \Delta y^2}$) for route distance metrics.

3. **Topology & Named Landmark Alignment:**
    - Author backend settlement nodes (`Oakhaven`, `Highbridge`, `Ironhold`, `Northgate`, `Riverbend`, `Eastwatch`, `Valeside`) and road edges (`The King's Road`, `The High Road`, `The Watcher's Path`) to match the visual features on the fantasy map.
    - Verify that river crossings (_Highbridge Crossing_) and mountain barriers (_The Gilded Pass / Ironspine Mountains_) correctly constrain routing alternatives.

4. **Preservation of Core Workbench Features:**
    - Ensure multi-leg itinerary building, live hazard overrides (`ACTIVE_OVERRIDES`), automatic detours, travel profiles, and Markdown handout exports function identically on the new fantasy coordinate space.
