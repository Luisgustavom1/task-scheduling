# Codebase Stack Analysis

**Scope:** `/research` directory only  
**Python Version:** 3.13  

## Core Runtime

- **Python:** 3.13
- **Virtual Environment:** `../ve/` (fully provisioned)

## Key Dependencies

| Dependency | Version | Purpose | Status |
|---|---|---|---|
| `wfcommons` | (installed in ve/) | WFCommons workflow parsing, DAG structure, machine specs | ✓ Active |
| `networkx` | 3.4.2 | Graph algorithms (implicit in wfcommons) | ✓ Active |
| `numpy` | 2.2.4 | Numerical operations, array handling | ✓ Active |
| `pandas` | 2.2.3 | Data analysis (currently unused; available) | - |
| `matplotlib` | 3.10.1 | Visualization (future: traces, metrics) | - |
| `pyyaml` | 6.0.2 | Config files (if needed) | - |

## Architecture Layers

**Parser Layer:** `parser/wfcommons.py`
- Input: WFCommons JSON file path
- Output: Workflow object (domain model)
- Dependencies: wfcommons, numpy

**Domain Layer:** `task.py`, `data_item.py`, `workflow.py`, `resources.py`, `common.py`
- Task state machine, DataItem tracking, Resource specs
- Dependencies: dataclasses (stdlib), enum (stdlib)

**Simulator Layer:** `simulator.py`
- Orchestrates workflow execution
- Calls scheduler for task allocation
- Manages workflow state, timing, event processing
- Dependencies: domain models, parser

**Scheduler Layer:** `schedulers/simple.py`
- Implements scheduling strategy (greedy for now)
- Must implement Scheduler interface (from scheduler.py — external or base)

## Entry Point

- `main.py` — CLI runner; parses args, loads workflow, runs simulator

## Configuration

- **Parser config:** Config dataclass (ignore_memory, reference_speed)
- **Simulator behavior:** Logging flag
- **Resource specs:** Loaded from WFCommons JSON (machines, cores, memory)

## No Third-Party Frameworks

- ❌ No web framework (FastAPI, Flask, Django)
- ❌ No ORM (SQLAlchemy)
- ❌ No async/await runtime (asyncio used minimally if at all)
- ❌ No CLI framework (argparse only, built-in)

This is a pure Python simulation engine with minimal external dependencies.
