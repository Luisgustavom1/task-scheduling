# Technical Concerns & Risk Assessment

**Scope:** `/research` directory  
**Severity Levels:** 🔴 CRITICAL | 🔴 HIGH | ⚠️ MEDIUM | 🟡 LOW

---

## 🔴 CRITICAL Issues (Blocking v1.0)

### C1: Simulator Execution Loop Missing

**Severity:** 🔴 CRITICAL  
**Status:** Unresolved  
**Impact:** Workflows cannot run end-to-end; v1.0 blocked

**What:**
- `simulator.start(scheduler)` method exists but doesn't implement event loop
- After calling scheduler once, method returns without processing task execution

**Root Cause:**
- Incomplete implementation
- No event queue or discrete event simulation framework
- No main loop to drive task state transitions

**Evidence:**
```python
def start(self, scheduler):
    # Scheduler is called once, but then nothing happens
    actions = scheduler.start(self.workflow, self.resources)
    # Missing: Event loop to process actions and simulate execution
```

**Unblock:**
1. Implement event queue (priority queue of events: task_start, task_end, etc.)
2. Add main loop: while unfinished_tasks > 0:
   - Pop next event
   - Update task/resource state
   - Trigger dependent tasks if ready
   - Record metrics (start_time, end_time)
3. Test with bwa-chameleon-small-001.json

**Effort Estimate:** 2-3 hours

**Files to Modify:**
- `simulator.py` (main event loop)
- `task.py` (add start_time, end_time, assigned_resource fields)
- `resources.py` (track running_tasks per resource)

---

### C2: calcDownwardRank() Returns None

**Severity:** 🔴 CRITICAL  
**Status:** Unresolved  
**Impact:** Initialization incomplete; returns None to caller

**What:**
- Method exists in simulator.py
- Has no return statement
- Implicitly returns None

**Root Cause:**
- Incomplete implementation
- Likely intended to compute task priorities (for scheduler use)

**Evidence:**
- Search for `calcDownwardRank` in simulator.py; method body likely incomplete

**Unblock:**
1. Determine intended behavior: compute downward rank (expected completion time) for each task
2. Formula: downward_rank[task] = max(downward_rank[child] + task.runtime) for all children
3. Return dict of task_id → downward_rank

**Effort Estimate:** 1 hour

**Files to Modify:**
- `simulator.py` (implement method or remove if not needed)

---

### C3: No Error Handling or Validation

**Severity:** 🔴 CRITICAL  
**Status:** Unresolved  
**Impact:** Crashes on invalid input; no graceful degradation

**What:**
- Parser assumes JSON is valid WFCommons format
- Simulator assumes all tasks/resources valid
- Scheduler assumes inputs are well-formed
- No exception handling anywhere

**Root Cause:**
- Code assumes "happy path" only
- No defensive programming

**Evidence:**
```python
# parser/wfcommons.py
instance = wfinstances.Instance(input_instance=path.joinpath(file_path))
# No error handling if file doesn't exist or is malformed

# simulator.py
self.tasks[task_id] = Task(...)
# No validation that task_id is valid or task data is complete
```

**Unblock:**
1. Add file existence checks in parser
2. Add JSON schema validation in parser
3. Add task/resource validation in simulator
4. Add resource exhaustion handling in scheduler
5. Wrap everything in try-catch with meaningful error messages

**Effort Estimate:** 1-2 hours

**Files to Modify:**
- `parser/wfcommons.py`
- `simulator.py`
- `schedulers/simple.py`

---

## 🔴 HIGH Priority Issues

### H1: Task Execution State Not Tracked

**Severity:** 🔴 HIGH  
**Status:** Unresolved  
**Impact:** Cannot measure metrics (makespan, task timing); no visibility into execution

**What:**
- Task model has no fields for: start_time, end_time, assigned_resource
- No way to record when task actually executed or which resource ran it
- Metrics collection impossible

**Root Cause:**
- Domain model incomplete for execution phase

**Unblock:**
1. Add fields to Task dataclass:
   - `start_time: Optional[float] = None`
   - `end_time: Optional[float] = None`
   - `assigned_resource_id: Optional[str] = None`
2. Populate during event loop execution
3. Use to compute metrics

**Effort Estimate:** 1 hour

**Files to Modify:**
- `task.py` (add fields)
- `simulator.py` (populate during execution)

---

### H2: SimpleScheduler Too Naive

**Severity:** 🔴 HIGH  
**Status:** Partial (works but suboptimal)  
**Impact:** Scheduling quality poor; results not representative of real systems

**What:**
- Current strategy: Greedy first-fit (pick first available resource)
- No task prioritization (FIFO)
- No topology awareness (ignores DAG structure)
- No load balancing

**Root Cause:**
- Intentional simplification for MVP; needs upgrade

**Evidence:**
```python
def start(self, workflow, resources):
    for task_id in ready_tasks:  # FIFO, no prioritization
        for i in range(len(resources)):  # First-fit
            if resource_fits:
                allocate_task(...)
                break
```

**Impact on Results:**
- Makespan may be significantly longer than optimal
- Doesn't represent real schedulers (HEFT, min-min, etc.)

**Unblock (v1.1):**
1. Implement upward/downward rank calculation
2. Sort ready tasks by rank (higher priority first)
3. For each task, pick resource with earliest completion time

**Effort Estimate:** 2-3 hours

**Files to Modify:**
- `schedulers/simple.py` (enhance)
- Possibly `simulator.py` (expose rank calculation)

---

## ⚠️ MEDIUM Priority Issues

### M1: Inconsistent Code Style & Indentation

**Severity:** ⚠️ MEDIUM  
**Status:** Unresolved  
**Impact:** Code readability; inconsistent with conventions

**What:**
- Indentation varies: 2 spaces, 4 spaces, mixed
- No docstrings or type hints in many methods
- Inconsistent naming (wf_workflow vs workflow)

**Evidence:**
```python
# simulator.py - 2 spaces
  def __init__(self, instance):
    self.instance = instance

# parser/wfcommons.py - 4 spaces
    def from_wfcommons(file_path: str, config: Config) -> Workflow:
        ...
```

**Unblock:**
1. Run Black formatter: `black research/`
2. Add docstrings (Google style)
3. Add type hints to all public methods

**Effort Estimate:** 1-2 hours

**Files to Modify:**
- All `.py` files

---

### M2: Missing Type Hints on Public Methods

**Severity:** ⚠️ MEDIUM  
**Status:** Partial  
**Impact:** Reduced IDE support, harder to understand intent

**What:**
- Many functions lack return type hints
- Some functions lack argument type hints

**Evidence:**
```python
def calcAverageTransferRate(self):  # No return type
    ...

def estimateExecTime(self, ref_resource, target, runtime):  # No types
    ...
```

**Unblock:**
1. Add return types to all public methods
2. Add argument types where missing
3. Consider mypy validation in tests

**Effort Estimate:** 1 hour

---

### M3: Resource Model Too Simplistic

**Severity:** ⚠️ MEDIUM  
**Status:** Acknowledged  
**Impact:** Cannot model advanced resource types (GPU, TPU); no hierarchical resources

**What:**
- Resource only tracks: cores, memory, speed
- No support for: accelerators, memory hierarchy, network bandwidth
- Homogeneous resource assumption

**Rationale for Deferring:**
- v1.0 focus: CPU-only workflows
- Real workflows often use CPU+GPU; deferred to v1.2

**Unblock (v1.2):**
1. Extend Resource class with accelerators (gpu_count, tpu_count, etc.)
2. Add resource type field (cpu, gpu, tpu)
3. Update scheduler to consider accelerator requirements

**Files to Modify:**
- `resources.py`
- `schedulers/` (all implementations)

---

## 🟡 LOW Priority Issues

### L1: No Test Suite

**Severity:** 🟡 LOW  
**Status:** Acknowledged  
**Impact:** No regression detection; manual testing only

**What:**
- Zero unit tests, integration tests, or end-to-end tests
- Hard to validate changes or catch bugs

**Unblock (v1.0):**
1. Add pytest test suite
2. Target 80%+ code coverage
3. Focus on domain models and parser first

**Effort Estimate:** 3-4 hours

**Files to Create:**
- `tests/conftest.py`
- `tests/test_*.py` (multiple files)

---

### L2: Sparse Documentation & Docstrings

**Severity:** 🟡 LOW  
**Status:** Partial  
**Impact:** Harder to onboard new contributors; unclear method intent

**What:**
- Most methods have no docstrings
- Architecture documentation missing
- No example usage or tutorials

**Unblock:**
1. Add module-level docstrings (explain purpose)
2. Add Google-style docstrings to all public methods
3. Create README with architecture overview

**Effort Estimate:** 2-3 hours

---

### L3: No Logging or Observability

**Severity:** 🟡 LOW  
**Status:** Partial  
**Impact:** Hard to debug; no visibility into execution

**What:**
- Basic logging in main.py only
- Simulator has no logging
- Scheduler has no logging

**Unblock (v1.1):**
1. Add logging to simulator (task state changes, scheduler calls)
2. Add logging to scheduler (allocation decisions)
3. Support multiple log levels (DEBUG, INFO, WARNING)

**Effort Estimate:** 1-2 hours

---

### L4: Genetic Algorithms Not Integrated

**Severity:** 🟡 LOW  
**Status:** Out of scope (separate module)  
**Impact:** None (yet); for future optimization research

**What:**
- `genetic-algorithms/` folder exists but unused
- Intended for evolving scheduler strategies
- Deferred to v2.0+

**Rationale:** Focus on baseline simulator first; GA optimization later

---

## 🟡 Data & Testing Concerns

### D1: Limited Test DAG Coverage

**Severity:** 🟡 LOW  
**Status:** Acknowledged  
**Impact:** May miss edge cases

**What:**
- Three test DAGs available: bwa, blast, 1000genome
- All from same source (WFCommons); similar structure

**Unblock (v1.2):**
1. Add synthetic test DAGs (tiny, simple structures for unit tests)
2. Add pathological cases (all serial, all parallel, diamonds, etc.)

**Effort Estimate:** 2-3 hours

---

## Risk Summary

| Risk | Severity | Status | Blocker | Mitigation |
|---|---|---|---|---|
| Execution loop missing | 🔴 | Unresolved | YES | Implement discrete event simulation |
| calcDownwardRank returns None | 🔴 | Unresolved | YES | Complete method or remove |
| No error handling | 🔴 | Unresolved | YES | Add validation + try-catch |
| Task execution state not tracked | 🔴 | Unresolved | YES | Add time/resource fields to Task |
| SimpleScheduler naive | 🔴 | Partial | NO | Defer to v1.1; current version works |
| Code style inconsistent | ⚠️ | Unresolved | NO | Run Black, add docstrings |
| Missing type hints | ⚠️ | Partial | NO | Add types to public methods |
| Resource model simplistic | ⚠️ | Acknowledged | NO | Defer to v1.2 |
| No test suite | 🟡 | None | NO | Implement pytest framework |
| Sparse docs | 🟡 | Partial | NO | Add docstrings, README |
| No logging | 🟡 | Partial | NO | Defer to v1.1 |

---

## Recommended Priority Order (v1.0)

1. **FIX IMMEDIATELY:** C1 (Execution loop), C2 (calcDownwardRank), C3 (Error handling)
2. **FIX SOON:** H1 (Task execution state), H2 (Consider if needed now)
3. **NICE TO HAVE:** M1 (Style), M2 (Type hints), L1 (Tests)

**Estimated Effort to v1.0:** 5-7 hours of focused work
