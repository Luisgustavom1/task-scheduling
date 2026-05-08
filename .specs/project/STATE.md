# Project State — Decisions, Blockers, Lessons

**Last Updated:** May 7, 2026  
**Scope:** Task Scheduling Simulator (`/research` directory only)

---

## Decisions

**D1: Scope to `/research` directory only**
- Rationale: Isolate core simulator from genetic-algorithms experiments and wfcommons tooling
- Implication: Separate PROJECT.md, independent roadmap, focused testing
- Reversibility: Medium (can merge back if needed, but separation aids clarity)

**D2: Python dataclasses for domain models**
- Current: Task, DataItem, Resource use @dataclass
- Alternative considered: Pydantic (validation) vs plain classes (simpler)
- Chosen: Dataclasses (good balance of simplicity + structure; can add validation layer later)
- Status: ✓ Good choice, no changes needed

**D3: Event-driven simulation architecture**
- Current: Simulator maintains workflow state, processes tasks event-by-event
- Alternative: Time-stepped simulation (less realistic for workflows)
- Chosen: Event-driven (more accurate, matches real scheduling systems)
- Status: ✓ Concept sound; implementation incomplete

**D4: Pluggable scheduler interface**
- Current: Scheduler.start() method; SimpleScheduler implements basic greedy
- Rationale: Enable algorithm comparison without changing simulator core
- Status: ✓ Design is clean, working well

---

## Blockers

**B1: Simulator execution loop incomplete** 🔴 CRITICAL
- **What:** `simulator.start(scheduler)` → no main loop; tasks not executed
- **Root cause:** 
  - `calcDownwardRank()` in simulator.py has no return statement (returns None)
  - No main task processing loop after initialization
- **Impact:** Cannot run any workflows; v1.0 blocked
- **Unblock:** Implement event loop + fix calcDownwardRank return
- **Effort:** ~1-2 hours
- **Decision:** FIX IMMEDIATELY (highest priority)

**B2: Error handling completely missing** 🔴 HIGH
- **What:** Code assumes all inputs valid; no exception handling
- **Locations:** Parser, Simulator, Scheduler don't validate input
- **Impact:** Crashes on malformed DAGs, crashes on resource exhaustion, crashes on invalid configs
- **Unblock:** Add validation layer + try-catch blocks
- **Effort:** ~1-2 hours
- **Decision:** FIX IN v1.0 (needed for stability)

**B3: SimpleScheduler lacks resource awareness** ⚠️ MEDIUM
- **What:** Current implementation greedily picks first available resource
- **Missing:** No prioritization, no topology awareness (upstream/downstream)
- **Impact:** Not a *wrong* scheduler, but suboptimal results
- **Unblock:** Add task priority ranking (upward/downward rank from HEFT algorithm)
- **Effort:** ~2-3 hours
- **Decision:** DEFER to v1.1 (works, but could be better)

---

## Lessons

**L1: WFCommons library is mature but underdocumented**
- The wfcommons.wfinstances.Instance API works well once you understand the structure
- Recommend: Read source code examples, not just docs
- Applied to: Parser implementation

**L2: Task state transitions are complex but crucial**
- Task must move: READY → (dependencies satisfied) → RUNNABLE → (scheduler assigns) → SCHEDULED → RUNNING → DONE
- Current code partially models this; execution loop needs to enforce it strictly
- Applied to: Revisit task.py state enum during execution loop implementation

**L3: Resource tracking requires careful state management**
- Need to track: cores_available, memory_available, currently_running_tasks per resource
- Mistakes here lead to over-allocation or false "out of capacity" errors
- Applied to: Resource.py; consider adding assertion checks

**L4: Data transfer modeling is deferred but important**
- Current code calculates average_transfer_rate but doesn't use it
- Recommendation: Leave deferred until v1.2; focus on task execution first

---

## TODOs

**Priority 1 (Unblock v1.0):**
- [ ] Fix `calcDownwardRank()` return statement (simulator.py, line ~TBD)
- [ ] Implement simulator event loop in simulator.start()
- [ ] Test with bwa-chameleon-small-001.json
- [ ] Add try-catch + validation (parser, simulator, scheduler)

**Priority 2 (Complete v1.0):**
- [ ] Test with blast and 1000genome workflows
- [ ] Record and display makespan metrics
- [ ] Code review: indentation consistency (2 vs 4 spaces)
- [ ] Add docstrings to all public methods

**Priority 3 (Future):**
- [ ] Implement pytest test suite
- [ ] Add upward/downward rank calculation (for v1.1 scheduler)
- [ ] Document scheduler interface contract

---

## Deferred Ideas

**Deferred to v1.1:**
- HEFT scheduler and other scheduling algorithms
- Scheduler comparison metrics (fairness, utilization score)

**Deferred to v1.2:**
- Data transfer timing simulation
- Resource contention (shared L3 cache, network saturation)
- Task failure/retry

**Deferred beyond v2.0:**
- Integration with genetic-algorithms/ for algorithm optimization
- Visualization dashboard
- Distributed simulation

---

## Session Notes

**May 7, 2026 - TLC Project Init (Research Directory)**
- Scoped project to `/research` only (independent from broader workspace)
- Created PROJECT.md, ROADMAP.md, STATE.md
- Identified B1 (execution loop) as critical blocker
- Next session: Run "tlc implement" or "tlc tasks" to break down v1.0 completion
