# External Integrations & Dependencies

## WFCommons Library Integration

**Library:** wfcommons (PyPI: wfcommons)  
**Purpose:** Parse scientific workflow DAGs in WFCommons JSON format  
**Status:** ✓ Active integration

### How It's Used

**Entry Point:** `parser/wfcommons.py` — `from_wfcommons(file_path, config)`

**Process:**
1. **Load DAG:** `wfcommons.wfinstances.Instance(input_instance=path)`
   - Parses JSON file
   - Extracts workflow graph (tasks, edges, dependencies)
   - Extracts resource specifications (machines, cores, memory, speed)

2. **Access Data:**
   - `instance.workflow` — Workflow graph (tasks, edges, task metadata)
   - `instance.machines` — Resource specifications
   - `instance.workflow.tasks[task_id]` — Individual task (name, runtime, cores, I/O files)
   - `instance.workflow.edges` — Task dependencies (source → target)

3. **Conversion:**
   - Convert byte sizes → MB (1e6 bytes = 1 MB)
   - Estimate execution times for heterogeneous machines (MHz speed data → Gflop/s)
   - Map tasks to resources

### Data Structures

| WFCommons Class | Maps To | How |
|---|---|---|
| `Task` | `research.Task` | name, runtime (flops), cores, input_files, output_files |
| `Machine` | `research.Resource` | id, name, cpu_speed, cpu_cores, memory |
| `Workflow` graph | `research.Workflow` | tasks, data_items, task dependencies, ready tasks |

### Known Issues & Workarounds

| Issue | Workaround |
|---|---|
| WFCommons library documentation sparse | Read source code; check example usage in repo |
| Machine speed may be None | Use config.reference_speed as fallback |
| File size precision varies | Use math.ceil() when converting bytes → MB |
| Large DAGs slow to parse | Cache parsed results if doing repeated runs |

### Version Compatibility

**Currently Using:** Unknown version (installed in ve/)  
**Check:** `pip show wfcommons`  
**Recommendation:** Pin version in requirements.txt (once finalized)

---

## NetworkX (Implicit Dependency)

**Library:** networkx  
**Purpose:** Graph algorithms (implicit in wfcommons)  
**Status:** ✓ Available but not directly used

### Potential Future Use

- Topological sort (task ordering)
- Transitive reduction (simplify DAG)
- Longest path (critical path for task prioritization)

### If We Wanted to Use It Directly

```python
import networkx as nx

# Create DAG from workflow
G = nx.DiGraph()
for task_id in workflow.tasks:
    G.add_node(task_id)
for edge in workflow.edges:
    G.add_edge(edge[0], edge[1])

# Compute critical path
topo_order = list(nx.topological_sort(G))
longest_path = nx.dag_longest_path(G)
```

---

## NumPy Integration

**Library:** numpy  
**Purpose:** Numerical operations, array handling  
**Status:** ✓ Installed; minimally used

### Where It's Used

- `simulator.py`: `np.random` (if needed for random sampling)
- Potential: Matrix operations for resource utilization

### Rarely Used But Available

```python
import numpy as np

# Estimate execution time based on resource speed ratios
reference_exec_time = task.runtime
speed_ratio = target_resource.speed / reference_resource.speed
estimated_time = reference_exec_time / speed_ratio
```

**Current implementation:** Manual calculation (not using numpy specifically)

---

## Pandas (Available but Unused)

**Library:** pandas  
**Purpose:** Data analysis, CSV export (planned)  
**Status:** ⚠️ Installed; not currently used

### Potential Future Use (v1.2+)

```python
import pandas as pd

# Collect metrics into DataFrame
metrics = pd.DataFrame({
    'task_id': [t.id for t in completed_tasks],
    'start_time': [...],
    'end_time': [...],
    'makespan': [...],
    'resource_id': [...],
})

# Export to CSV
metrics.to_csv('execution_trace.csv', index=False)
```

---

## Matplotlib (Available but Unused)

**Library:** matplotlib  
**Purpose:** Visualization (future)  
**Status:** ⚠️ Installed; not currently used

### Potential Future Use (v1.2+)

```python
import matplotlib.pyplot as plt

# Plot execution timeline
plt.figure(figsize=(12, 6))
for task_id, task in enumerate(completed_tasks):
    plt.barh(task.resource_id, task.end_time - task.start_time, left=task.start_time)
plt.xlabel('Time (seconds)')
plt.ylabel('Resource')
plt.title('Workflow Execution Timeline')
plt.savefig('execution_timeline.png')
```

---

## PyYAML (Available but Unused)

**Library:** PyYAML  
**Purpose:** Configuration file parsing (future)  
**Status:** ⚠️ Installed; not currently used

### Potential Future Use

```yaml
# config.yaml
parser:
  ignore_memory: false
  reference_speed: 10.0
scheduler:
  strategy: "simple"  # or "heft", "priority", etc.
simulator:
  logging: true
```

### Usage:
```python
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)
```

---

## External Services & APIs

**Status:** 🟢 None (simulator is standalone)

- No network calls
- No database connections
- No cloud service integrations
- No external scheduling services

This is a pure CPU-bound simulation engine.

---

## Integration Testing Strategy

**Test external integrations:**

1. **WFCommons Parser Tests**
   ```python
   def test_real_dag_parsing():
       workflow = from_wfcommons("bwa-chameleon-small-001.json", Config())
       assert len(workflow.tasks) > 0
       assert len(workflow.resources) > 0
   ```

2. **Resource Compatibility Tests**
   ```python
   def test_task_fits_on_resource():
       task = workflow.tasks[0]
       resource = simulator.resources[0]
       assert resource.cores_available >= task.min_cores
   ```

3. **Dependency Chain Tests**
   ```python
   def test_edges_preserved_from_wfcommons():
       # Verify task dependencies parsed correctly
       assert task_b.id in task_a.children  # If A → B
   ```

---

## Dependency Pinning (Recommendations)

**Create `requirements.txt`:**

```
wfcommons==0.x.x  # (pin once you verify working version)
networkx==3.4.2
numpy==2.2.4
pandas==2.2.3
matplotlib==3.10.1
PyYAML==6.0.2
```

**Avoid:** Unpinned versions (floating dependencies risk breaking existing code)

---

## Isolation & Versioning

**Current Setup:**
- Virtual environment: `../ve/` (isolated from system Python)
- Activation: `. ../ve/bin/activate`
- All dependencies installed here; changes won't affect system

**Best Practice:** Always work within virtual environment:
```bash
cd /Users/luisao/ufu/task-scheduling
source ve/bin/activate
cd research
python main.py
```

---

## Future Integration Points

**v1.1 (Scheduler Variants):**
- Consider if any library provides HEFT algorithm
- Likely: Implement ourselves (simpler than adding dependency)

**v1.2 (Advanced Simulation):**
- Network simulation: Consider simpy (discrete event simulator)
- Data transfer: May need graph traversal (networkx)

**v2.0+ (Optimization):**
- Genetic algorithm integration (see `genetic-algorithms/` folder)
- ML-based scheduler learning (scikit-learn?)

---

## Integration Health Checklist

- ✓ WFCommons parsable with real DAG files
- ✓ Resource specs loaded correctly
- ✓ Task metadata accessible
- ⚠️ Error handling for missing/invalid data (add in v1.0)
- ⚠️ Version pinning for all dependencies (add in v1.0)
- ⚠️ Integration tests for parser layer (add in v1.0)
