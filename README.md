# T⁴ — Topographic Terrain Traversal Tool

> A geospatial traversal and logistics tool for fictional tabletop worlds.

**T⁴** (Topographic Terrain Traversal Tool) explores what happens when geography becomes computationally meaningful rather than merely visual.

The project is intended to model a fictional world as spatial data and use that geography to calculate traversal, routing, and logistical consequences.

The central idea is:

> **What happens when a game world actually understands where things are?**

A journey should not simply be a line drawn between two points. Geography, routes, terrain, and changing world conditions should be capable of affecting what that journey costs and how it unfolds.

## Current Status

**Concept / Feasibility Investigation**

T⁴ is not yet an implementation project. The immediate goal is to determine whether its central technical and design ideas are interesting, practical, and worth developing into a larger portfolio project.

## Initial Concept

The smallest useful version of T⁴ is a fictional geographic world containing:

- settlements
- a connected road network
- terrain or geographic features
- at least one meaningful crossing or chokepoint
- a party with basic logistical constraints

Given a starting location and destination, T⁴ should be able to:

1. determine a viable route;
2. calculate traversal distance and time;
3. account for basic logistical consequences;
4. explain why the resulting route and costs were produced;
5. respond to a change in world state.

A canonical example is a bridge closure:

> A party normally travels from Settlement A to Settlement B across a bridge.
> The bridge becomes unavailable.
> T⁴ must find another route and show how the change affects distance, travel time, and logistics.

This small scenario is intended to demonstrate the project's central thesis without requiring a complete simulated world.

## Guiding Principles

### Geography is data

Geographic features should be represented as meaningful spatial data rather than decorative map elements.

### Geography affects computation

Location, terrain, routes, and geographic constraints should influence calculations performed by the system.

### World state can change consequences

A change to the world should be capable of changing traversal and logistical results.

### Results should be explainable

The system should be able to show how it arrived at a route or logistical result rather than presenting unexplained numbers.

### Prefer explicit systems over autonomous simulation

T⁴ should initially calculate consequences from an explicitly defined world state. It does not need to simulate an autonomous civilization.

### Start small

The project should prove its central idea before accumulating additional systems.

## Initial Technical Direction

The current conceptual stack is:

- **Frontend:** React + TypeScript
- **Map rendering:** MapLibre GL JS
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL + PostGIS
- **Geographic authoring:** QGIS
- **Routing:** To be evaluated experimentally

These are provisional choices, not commitments.

## Explicit Non-Goals

T⁴ is not initially intended to be:

- a virtual tabletop (VTT);
- a combat engine;
- a general RPG rules engine;
- a character-management system;
- a multiplayer game;
- a procedural world generator;
- an autonomous civilization simulator;
- a full economic simulation;
- a weather simulator;
- a complete campaign-management application.

These may be interesting future directions, but they are outside the initial feasibility investigation.

## Current Investigation

The first investigation will focus on whether the following pipeline is practical:

**QGIS → spatial data → PostGIS → FastAPI → routing/logistics calculations → MapLibre**

The investigation will specifically explore:

- spatial data modeling;
- PostGIS capabilities;
- geographic visualization;
- road-network representation;
- graph-based routing;
- traversal calculations;
- basic logistics;
- mutable world state;
- explainable results.

Findings and decisions will be recorded in the [design notebook](docs/design-notebook.md).

## Project Status Philosophy

T⁴ will be developed through:

**Explore → Hypothesize → Experiment → Decide → Build**

Early decisions should be supported by experiments where practical rather than treated as permanent architectural commitments.
