# T⁴ Design Notebook

This document records the exploration and design investigation for **T⁴ — Topographic Terrain Traversal Tool**.

It is intentionally a working notebook rather than a finalized architecture document.

The purpose is to record questions, hypotheses, experiments, findings, and decisions as the project takes shape.

---

## 1. Project Thesis

T⁴ explores what happens when geography becomes computationally meaningful in a fictional tabletop world.

The central question is:

> **What happens when a game world actually understands where things are?**

The project should treat geography as part of the computational model rather than merely as something displayed on a map.

A route should therefore be capable of producing meaningful consequences:

- distance;
- traversal time;
- logistical cost;
- route alternatives;
- changes caused by geographic or world-state conditions.

---

## 2. Current Working Concept

T⁴ is currently envisioned as a **geospatial traversal and logistics engine** for fictional tabletop worlds.

The initial system will use a hand-authored geographic world rather than attempting to procedurally generate one.

The smallest interesting scenario currently appears to be:

- two or more settlements;
- a connected road network;
- geographic features that give the network spatial meaning;
- a meaningful chokepoint such as a bridge or mountain pass;
- a party with basic movement and logistical constraints;
- a world-state change that can alter the available route.

The canonical experiment is currently:

**Bridge open → route A → bridge closed → route B → changed logistical consequences**

---

## 3. What T⁴ Is Trying to Prove

The initial investigation should establish whether the following ideas work together effectively:

1. Geographic data can be authored and stored cleanly.
2. Geographic data can be rendered interactively.
3. A road network can be represented as a traversable graph.
4. A route can be calculated between meaningful locations.
5. Geographic or route properties can affect traversal cost.
6. Party constraints can turn traversal into a logistics calculation.
7. A small change in world state can produce a different result.
8. The system can explain the resulting calculation.

The goal is not to prove that an entire world simulation is possible.

The goal is to prove that the **core interaction is interesting and technically sound**.

---

## 4. Current Architectural Hypothesis

The current conceptual separation is:

### PostGIS knows geography

Responsible for:

- spatial geometry;
- geographic relationships;
- spatial queries;
- geographic persistence.

### Python knows rules

Responsible for:

- traversal;
- routing;
- movement calculations;
- logistics;
- world-state effects;
- consequence calculations.

### React knows presentation

Responsible for:

- map interaction;
- displaying routes;
- displaying geographic features;
- presenting calculations and explanations;
- allowing the user to interact with the world.

This is a working architectural principle, not yet a finalized implementation.

---

## 5. Current Technology Hypotheses

### PostgreSQL + PostGIS

**Status:** Strong candidate

PostGIS should provide the spatial persistence and query capabilities required by the project.

Questions to investigate:

- Which geometry types are actually needed?
- How should fictional-world coordinates be represented?
- Which spatial operations are useful to the domain?
- How much spatial logic belongs in SQL versus Python?

### FastAPI

**Status:** Strong candidate

Python is already a productive environment for the project's domain calculations and provides a natural API boundary.

### React + TypeScript

**Status:** Strong candidate

The frontend needs interactive map behavior and a clear way to present geographic and logistical results.

### MapLibre GL JS

**Status:** Strong candidate

MapLibre provides the interactive geographic presentation layer without requiring a proprietary mapping platform.

### QGIS

**Status:** Strong candidate for authoring

QGIS may provide a practical way to create and edit the fictional world's geographic data without requiring a custom world editor.

### Routing Engine

**Status:** Open question\*\*

Candidates currently include:

- NetworkX;
- pgRouting;
- potentially another graph/routing approach if experimentation identifies a better fit.

This decision should be investigated rather than assumed.

---

## 6. Open Questions

### 6.1 What exactly constitutes the initial geographic model?

Questions:

- Are roads sufficient initially?
- Which geographic features are necessary to make the project meaningfully spatial?
- How much terrain is actually required?
- Does a river crossing or mountain pass provide enough geographic context?

### 6.2 How should terrain affect traversal?

Possible approaches range from:

- terrain as descriptive metadata;
- terrain as a movement-cost modifier;
- terrain as an impassable condition;
- continuous terrain-based pathfinding.

The initial investigation should avoid committing to a more complex model than the project actually needs.

### 6.3 Where should routing occur?

NetworkX and pgRouting represent different architectural choices.

This should be tested rather than decided purely from preference.

### 6.4 What constitutes world state?

The initial working hypothesis is that world state should consist only of **small, explicit facts that can affect a calculation**.

For example:

- bridge open/closed;
- road condition;
- passability.

Calculated results such as route, travel time, and supply requirements should not automatically become persistent world state.

### 6.5 How should fictional geography be represented?

A fictional world does not necessarily require conventional Earth latitude/longitude.

The representation needs to support:

- spatial relationships;
- distance calculations;
- map rendering;
- geographic editing;
- routing.

The appropriate coordinate representation remains an investigation topic.

---

## 7. Current Scope Boundary

### In scope for investigation

- fictional geography;
- hand-authored geographic data;
- spatial databases;
- interactive mapping;
- road networks;
- routing;
- traversal;
- basic logistics;
- simple mutable world state;
- explainable results.

### Explicitly deferred

- off-road pathfinding;
- weather;
- factions;
- trade;
- resource economies;
- technology systems;
- procedural generation;
- autonomous simulation;
- multiplayer;
- combat;
- magic;
- campaign management;
- full RPG rules.

Deferral does not imply that these ideas are bad. It means they should not determine the architecture before the core system has been validated.

---

## 8. Experiments

Experiments should be small, disposable, and designed to answer specific questions.

### Experiment 1 — Geographic Data Pipeline

**Question:** Can a small fictional geographic dataset move cleanly through the proposed toolchain?

**Proposed pipeline:**
GeoJSON features → FastAPI → MapLibre

**Status:** Completed

**Finding:** GeoJSON feature collections representing settlements (nodes) and polylines (roads) serialized cleanly from FastAPI endpoints and rendered reliably across MapLibre GL JS data layers.

**Decision:** Adopted FastAPI and GeoJSON as the standard data transport layer for spatial entities.

---

### Experiment 2 — Minimal Road Network

**Question:** Can a small hand-authored road network be represented and traversed as a graph?

**Proposed world:**

- Settlements (Oakhaven, Riverbend, Northgate, Ironhold)
- Connected road segments (primary, secondary, trails)
- Meaningful alternative routes around hubs

**Status:** Completed

**Finding:** Representing roads as graph edges connecting settlement node identifiers allowed straightforward traversal and pathfinding without requiring heavy external spatial database extensions for initial exploration.

**Decision:** Implemented dictionary-based graph structures in Python for rapid iteration on network topology.

---

### Experiment 3 — Routing

**Question:** Can the system calculate a meaningful route between settlements?

Candidates:

- NetworkX / Custom BFS-based graph traversal
- pgRouting

**Status:** Completed

**Finding:** Custom graph-based pathfinding successfully handled multi-leg trade loops, origin/destination sequencing, and automated detour routing when primary paths were obstructed.

**Decision:** Used lightweight Python graph search algorithms to power multi-leg routing and detour detection.

---

### Experiment 4 — Basic Logistics

**Question:** Does adding party constraints make traversal meaningfully different from simple shortest-path routing?

Potential variables:

- Movement speed multipliers
- Travel profiles (DCC Death Sport vs. Heavy Trade Wagon)
- Verbiage units (_Leagues_ vs. _Miles_, _Watch Shifts_ vs. _Hours_)

**Status:** Completed

**Finding:** Profile configurations successfully decoupled raw geometric distance from rule-system verbiage and travel duration calculations.

**Decision:** Adopted profile-driven multipliers to modify time and distance units based on campaign context.

---

### Experiment 5 — Mutable World State

**Question:** Can a small world-state change produce an understandable systemic consequence?

Canonical test:

> Close the bridge / road (`r2`).

Expected behavior:

- Original route becomes unavailable
- Alternative route is selected via detour logic
- Distance and travel time change
- System explains the change with a re-routing notice

**Status:** Completed

**Finding:** Managing `ACTIVE_OVERRIDES` in an in-memory world-state store allowed real-time road status toggling that immediately forced path recalculation and detour notices.

**Decision:** Maintained in-memory state overrides for campaign hazard simulation and live route re-calculation.

---

### Experiment 6 — Explainability

**Question:** Can T⁴ clearly explain why it selected a route and produced its logistical results?

Potential explanation:

- Route selected and step-by-step itinerary path
- Segment distances and terrain modifiers
- Calculated travel time and distance units
- Active hazard logs and re-routing notices

**Status:** Completed

**Finding:** Packaging itinerary metrics, active overrides, and notices into structured Markdown documents made game prep and player distribution seamless.

**Decision:** Added FastAPI export endpoints for one-click clipboard copying and `.md` file generation.

---

## 9. Decisions

This section records decisions that have been made after investigation.

### Decision Log

| Date           | Decision                                           | Reason / Evidence                                                                                                                                                                                                                       |
| :------------- | :------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| August 2026    | **Python + FastAPI Core Architecture**             | Provided an optimal balance of rapid API development, clean JSON serialization, and flexible custom graph-routing logic.                                                                                                                |
| September 2026 | **React + MapLibre GL JS Frontend**                | Delivered high-performance interactive mapping with full control over custom GeoJSON layers, styling, and hover event bindings.                                                                                                         |
| October 2026   | **Stable Basemap with Profile Verbiage & Styling** | Abandoned dynamic basemap style-switching (`setStyle`) due to canvas/source wiping races; locked in a stable dark tactical basemap while using profiles exclusively for rule verbiage, distance/time units, and route polyline styling. |
| October 2026   | **Markdown Campaign Handout Exports**              | Implemented structured `.md` export generation to bridge spatial data directly into tabletop GM preparation workflows (Obsidian, Notion, printouts).                                                                                    |

---

## 10. Rejected or Deferred Ideas

Ideas that are deliberately rejected or deferred should be recorded here when they have been discussed enough that revisiting them later would otherwise create confusion.

| Idea                               | Status   | Reason                                 |
| ---------------------------------- | -------- | -------------------------------------- |
| Autonomous civilization simulation | Deferred | Outside initial scope                  |
| Procedural world generation        | Deferred | Not required to prove core thesis      |
| Multiplayer                        | Deferred | Not required for initial validation    |
| Combat system                      | Deferred | Not part of traversal/logistics thesis |
| Full RPG rules engine              | Deferred | Would obscure the core system          |

---

## 11. Findings

This section will eventually contain concise conclusions from the investigation.

It should answer:

- What worked?
- What did not?
- What surprised us?
- Which hypotheses were wrong?
- Which technologies were appropriate?
- Which ideas became more interesting?
- Which ideas became unnecessary?
- What does the evidence justify building?

---

## 12. Transition to Implementation

A formal implementation roadmap should not be created until the feasibility investigation provides enough evidence to justify one.

The eventual transition point should occur when:

- the spatial data pipeline works;
- the geographic model is sufficiently understood;
- routing has been validated;
- logistics produce meaningful results;
- mutable world state produces meaningful consequences;
- the architecture has survived the initial experiments.

At that point, the investigation can become an implementation plan.

**Explore → Hypothesize → Experiment → Decide → Build**
