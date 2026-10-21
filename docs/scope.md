# T⁴ Scope

This document defines the scope boundaries for **T⁴ — Topographic Terrain Traversal Tool**, protecting its core traversal and logistics thesis from scope creep.

Its purpose is to protect the project's central idea from being gradually replaced by adjacent systems that are interesting but unnecessary.

Scope may change as experimentation produces new evidence.

---

## 1. Core Purpose

**Status:** Phase 2 Implementation & Validation (Active Prototype)

T⁴ explores how a fictional world's geography becomes computationally meaningful. The core pipeline—ingesting GeoPackage data, building spatial graphs with endpoint snapping, calculating effort-weighted multi-stop routes, handling world-state closures, and exporting results back to GIS—is successfully validated.

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

## 2. Scope Boundaries

### Validated & Implemented (Phase 2)

- Hand-authored fictional geography (settlements and roads).
- Tolerance-based spatial endpoint snapping.
- Effort-weighted Dijkstra routing with terrain multipliers.
- Two-tier blockage handling (hard structural closures forcing detours).
- Multi-stop itinerary chaining and ledger tracking (distance, travel time, rations).
- GIS persistence (exporting route geometries back to QGIS).

### Active Roadmap (Phase 3 Prep)

- **Soft Blockages / Hazard Penalties:** Adding conditional friction/time/resource penalties to edges without outright deletion.
- **Pluggable Resource Profiles:** Abstracting ledger metrics to support fantasy overland travel, sci-fi/horror countdowns, battery drain, and surreal survival environments.

### Explicitly Deferred

- VTT features, combat engines, RPG rulesets, procedural generation, autonomous civilization simulation, multiplayer, and full economic/weather simulations.

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

Before adding a new system, ask:

1. **Does it strengthen the central T⁴ thesis?**
2. **Does it provide a capability needed by an existing system?**
3. **Can the current scope demonstrate the idea without it?**
4. **Does adding it introduce a fundamentally different technical problem?**
5. **Has the existing core been validated sufficiently to justify the added complexity?**

If the answer is primarily "it would be cool," the feature remains outside the scope.

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

**Phase:** Feasibility Investigation

**Committed:**
Geospatial traversal and logistics as the central problem.

**Strong candidates:**
Hand-authored fictional geography, PostGIS, FastAPI, React, MapLibre, road-network routing.

**Under investigation:**
Routing engine, terrain model, coordinate representation, minimum geographic model, depth of logistics.

**Deferred:**
Off-road traversal, weather, factions, resources, trade, technology, procedural generation, autonomous simulation, multiplayer, combat, RPG systems, campaign management.
