# Task Scheduling Simulator (`/research`)

**Vision:** Build a modular, extensible workflow task scheduling simulator that accurately models task execution, resource allocation, and scheduling policies for scientific workflows.

**For:** Researchers and practitioners evaluating task scheduling algorithms for distributed scientific workflow systems

**Solves:** Lack of a unified simulation platform to test, compare, and validate scheduling strategies against real-world workflow characteristics (task dependencies, data transfers, heterogeneous resources)

## Goals

- **Primary:** Create a working event-driven simulator that can execute scientific workflows (DAGs) with pluggable schedulers, measuring key metrics (makespan, resource utilization, energy efficiency)
- **Secondary:** Provide accurate workflow parsing from WFCommons format with full dependency and data transfer modeling
- **Tertiary:** Enable comparison of scheduling algorithms through modular scheduler interface
- **User Success Metric:** Simulator successfully runs bwa, blast, and 1000genome workflows to completion, producing makespan and resource utilization metrics

## Tech Stack

**Core:**
- Language: Python 3.13
- Workflow Format: WFCommons JSON instances
- Graph Processing: NetworkX (implicit in WFCommons)
- Numerical: NumPy

**Key Dependencies:**
- `wfcommons` — WFCommons library (workflow parsing, DAG structure)
- `networkx` — Graph utilities
- `numpy` — Numerical operations (estimation, calculations)

## Scope

**v1.0 includes:**
- WFCommons JSON parser → Workflow objects with tasks, data items, resource specifications
- Core domain models: Task (with state machine), DataItem, Resource, Workflow
- Event-driven simulator initialization and workflow normalization
- SimpleScheduler: basic greedy allocation strategy (first-available resource)
- Execution loop: task scheduling, state transitions, event processing
- Metrics collection: basic makespan and task completion tracking

**Explicitly out of scope (v1):**
- Multiple scheduler implementations (advanced algorithms)
- Distributed simulation or parallelization
- GUI or visualization
- Energy modeling or cost optimization
- Persistence (checkpointing/replication)
- Advanced networking simulation (data transfer timing)

## Constraints

- **Technical:** Must work with heterogeneous resource specs and variable task core/memory requirements
- **Data:** Real test DAGs available (bwa, blast, 1000genome) in `dag-instances/wfcommons/`
- **Performance:** Simulator must complete workflows in reasonable wall-clock time (not real-time)

## Current Status

**Phase:** v1.0 ~60-70% complete

**Blockers:**
- Simulator execution loop incomplete (calcDownwardRank returns None, no main task processing loop)
- No error handling/validation throughout

**To reach v1.0:**
1. Complete simulator execution loop
2. Add error handling and validation
3. Test against real DAGs
