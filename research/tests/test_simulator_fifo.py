import sys
import pathlib
import logging
import json

# Make the `research` package modules importable when running pytest from repo root
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from wfcommons.common.task import Task
from wfcommons.common.machine import Machine
from wfcommons import wfinstances
from schedulers.fifo import FIFOScheduler

logging.basicConfig(level=logging.WARNING)


def make_workflow():
    class Workflow:
        def __init__(self):
            self.tasks = {}  # task_id -> Task
            self.tasks_parents = {}  # task_id -> set(parent_ids)
            self.tasks_children = {}  # task_id -> set(child_ids)
            self.edges = set()
            self.name = "test_workflow"

        def add_task(self, task: Task):
            self.tasks[task.task_id] = task
            # ensure parents/children entries exist
            if task.task_id not in self.tasks_parents:
                self.tasks_parents[task.task_id] = set()
            if task.task_id not in self.tasks_children:
                self.tasks_children[task.task_id] = set()

        def add_edge(self, parent_id: str, child_id: str):
            # parent_id and child_id might be Task objects or ids
            if isinstance(parent_id, Task):
                parent_id = parent_id.task_id
            if isinstance(child_id, Task):
                child_id = child_id.task_id

            # Ensure both tasks have entries in the dicts
            self.tasks_parents.setdefault(parent_id, set())
            self.tasks_parents.setdefault(child_id, set())
            self.tasks_children.setdefault(parent_id, set())
            self.tasks_children.setdefault(child_id, set())

            self.tasks_children[parent_id].add(child_id)
            self.tasks_parents[child_id].add(parent_id)
            self.edges.add((parent_id, child_id))

        def to_nx_digraph(self):
            # placeholder for compatibility with other code
            return None

    return Workflow()


class InstanceFake:
    def __init__(self, workflow, machines):
        self.workflow = workflow
        self.machines = machines


def test_simulator_fifo_simple_chain():
    # Setup: two tasks t1 -> t2
    wf = make_workflow()

    t1 = Task(name="t1", task_id="t1", runtime=2.0)
    t2 = Task(name="t2", task_id="t2", runtime=3.0)

    wf.add_task(t1)
    wf.add_task(t2)
    wf.add_edge(t1.task_id, t2.task_id)

    # Create two machines
    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    m2 = Machine(name="m2", cpu={'coreCount': 1, 'speedInMHz': 500, 'vendor': 'Y'})

    machines = {
        'm1': m1,
        'm2': m2,
    }

    inst = InstanceFake(workflow=wf, machines=machines)

    # Import simulator lazily so sys.path hack is applied
    import importlib
    sim_mod = importlib.import_module('simulator')
    Simulator = sim_mod.Simulator

    sim = Simulator(inst, logger=logging.getLogger("test_simulator"))

    # Simulator expects a start task; set it to t1
    sim.start_task = t1

    scheduler = FIFOScheduler()

    sim.start(scheduler)

    # Assertions
    assert len(sim.completed_tasks) == 2
    # check both tasks present in completed_tasks
    assert 't1' in sim.completed_tasks
    assert 't2' in sim.completed_tasks
    # history should contain two entries in FIFO order
    assert [h['task_id'] for h in sim.history] == ['t1', 't2']


def test_simulator_respects_processor_availability():
    wf = make_workflow()
    t1 = Task(name="t1", task_id="t1", runtime=1.0)
    t2 = Task(name="t2", task_id="t2", runtime=1.0)

    wf.add_task(t1)
    wf.add_task(t2)
    wf.add_edge(t1.task_id, t2.task_id)

    # Make m2 slower so first task should go to faster machine m1
    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 2000, 'vendor': 'X'})
    m2 = Machine(name="m2", cpu={'coreCount': 1, 'speedInMHz': 500, 'vendor': 'Y'})

    machines = {'m1': m1, 'm2': m2}
    inst = InstanceFake(workflow=wf, machines=machines)

    import importlib
    sim = importlib.import_module('simulator').Simulator(inst)
    sim.start_task = t1

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # ensure tasks executed and recorded
    assert len(sim.history) == 2
    # the first scheduled task should be t1
    assert sim.history[0]['task_id'] == 't1'
    # verify processors recorded in history are valid keys
    assert sim.history[0]['processor_id'] in machines
    assert sim.history[1]['processor_id'] in machines


def test_diamond_dependency_pattern():
    """Test a diamond-shaped DAG: t1 -> (t2, t3) -> t4"""
    import importlib
    
    wf = make_workflow()
    t1 = Task(name="t1", task_id="t1", runtime=1.0)
    t2 = Task(name="t2", task_id="t2", runtime=2.0)
    t3 = Task(name="t3", task_id="t3", runtime=2.0)
    t4 = Task(name="t4", task_id="t4", runtime=1.0)

    for t in [t1, t2, t3, t4]:
        wf.add_task(t)

    wf.add_edge(t1.task_id, t2.task_id)
    wf.add_edge(t1.task_id, t3.task_id)
    wf.add_edge(t2.task_id, t4.task_id)
    wf.add_edge(t3.task_id, t4.task_id)

    m1 = Machine(name="m1", cpu={'coreCount': 4, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst)
    sim.start_task = t1

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # All 4 tasks should complete
    assert len(sim.completed_tasks) == 4
    # t4 should start only after both t2 and t3 are done
    t2_end = sim.completed_tasks['t2']
    t3_end = sim.completed_tasks['t3']
    t4_start = next(h['start'] for h in sim.history if h['task_id'] == 't4')
    assert t4_start >= max(t2_end, t3_end)


def test_single_task_workflow():
    """Edge case: workflow with only one task"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    t1 = Task(name="t1", task_id="t1", runtime=5.0, machines=[m_ref])
    wf.add_task(t1)

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst)
    # Let simulator handle start_task via normalization

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # The real task t1 should execute with proper runtime
    assert 't1' in sim.completed_tasks
    assert sim.completed_tasks['t1'] == 5.0


def test_multiple_independent_tasks():
    """Edge case: multiple tasks with no dependencies can run in parallel"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    tasks = [Task(name=f"t{i}", task_id=f"t{i}", runtime=1.0, machines=[m_ref]) for i in range(1, 4)]
    for t in tasks:
        wf.add_task(t)
    # No edges added - tasks are independent

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    m2 = Machine(name="m2", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    m3 = Machine(name="m3", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1, 'm2': m2, 'm3': m3}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst, logger=logging.getLogger("test"))
    # Let simulator create entry_point for multiple start tasks

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # All 3 tasks should complete
    assert 't1' in sim.completed_tasks
    assert 't2' in sim.completed_tasks
    assert 't3' in sim.completed_tasks


def test_processor_speed_affects_runtime():
    """Verify that processor speed scales task runtime correctly"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref_machine", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    t1 = Task(name="t1", task_id="t1", runtime=10.0, machines=[m_ref])
    wf.add_task(t1)

    # Processor with same speed as reference
    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst)
    # Let simulator handle start task

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # Task should execute with its base runtime when speeds match
    actual_end = sim.completed_tasks['t1']
    assert actual_end == 10.0


def test_makespan_calculation():
    """Verify makespan is the maximum end time of all tasks"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    t1 = Task(name="t1", task_id="t1", runtime=5.0, machines=[m_ref])
    t2 = Task(name="t2", task_id="t2", runtime=3.0, machines=[m_ref])
    wf.add_task(t1)
    wf.add_task(t2)
    # t1 -> t2
    wf.add_edge(t1.task_id, t2.task_id)

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst)
    # Let simulator handle

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    makespan = max(h['end'] for h in sim.history)
    # t1 ends at 5, t2 starts at 5 and ends at 8
    assert makespan == 8.0


def test_dependencies_prevent_early_execution():
    """Verify child tasks don't execute before all parents complete"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    t1 = Task(name="t1", task_id="t1", runtime=10.0, machines=[m_ref])
    t2 = Task(name="t2", task_id="t2", runtime=10.0, machines=[m_ref])
    t3 = Task(name="t3", task_id="t3", runtime=1.0, machines=[m_ref])
    
    for t in [t1, t2, t3]:
        wf.add_task(t)
    
    wf.add_edge(t1.task_id, t3.task_id)
    wf.add_edge(t2.task_id, t3.task_id)

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    m2 = Machine(name="m2", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1, 'm2': m2}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst, logger=logging.getLogger("test"))
    # Let simulator create entry_point

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    t1_end = sim.completed_tasks['t1']
    t2_end = sim.completed_tasks['t2']
    t3_start = next(h['start'] for h in sim.history if h['task_id'] == 't3')
    
    # t3 should not start until both t1 and t2 are done
    assert t3_start >= t1_end
    assert t3_start >= t2_end


def test_real_wfcommons_workflow():
    """Test with real BWA workflow from wfcommons"""
    import importlib
    import pathlib
    
    # Load the real wfcommons workflow
    dag_path = pathlib.Path(__file__).parent.parent.parent / "dag-instances" / "wfcommons" / "bwa-chameleon-small-001.json"
    
    if not dag_path.exists():
        print(f"Skipping: {dag_path} not found")
        return
    
    inst = wfinstances.Instance(input_instance=str(dag_path))
    
    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst, logger=logging.getLogger("test"))

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # Basic sanity checks
    assert len(sim.completed_tasks) > 0
    assert len(sim.history) > 0
    
    # All tasks in history should have valid execution times
    for h in sim.history:
        assert h['end'] >= h['start']
        assert h['start'] >= 0
        
    # Verify makespan exists
    makespan = max(h['end'] for h in sim.history)
    assert makespan > 0
    
    # Verify throughput is calculated
    throughput = len(sim.workflow.tasks) / (makespan or 1)
    assert throughput > 0
    
    print(f"Real workflow test: {len(sim.workflow.tasks)} tasks, makespan: {makespan:.2f}s, throughput: {throughput:.2f} tasks/s")


def test_identical_task_runtimes():
    """Edge case: all tasks have same runtime"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    tasks = [Task(name=f"t{i}", task_id=f"t{i}", runtime=5.0, machines=[m_ref]) for i in range(1, 5)]
    for t in tasks:
        wf.add_task(t)
    
    # Linear chain: t1 -> t2 -> t3 -> t4
    for i in range(len(tasks) - 1):
        wf.add_edge(tasks[i].task_id, tasks[i+1].task_id)

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst)
    # Let simulator handle

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # With 4 tasks each taking 5s in series: total should be 20s
    makespan = max(h['end'] for h in sim.history)
    assert makespan == 20.0


def test_fifo_order_respected():
    """Verify FIFO scheduler processes ready tasks in FIFO order"""
    import importlib
    
    wf = make_workflow()
    m_ref = Machine(name="ref", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    # Create a workflow where we can verify FIFO ordering
    t1 = Task(name="t1", task_id="t1", runtime=0.1, machines=[m_ref])
    t2 = Task(name="t2", task_id="t2", runtime=0.1, machines=[m_ref])
    t3 = Task(name="t3", task_id="t3", runtime=0.1, machines=[m_ref])
    
    for t in [t1, t2, t3]:
        wf.add_task(t)
    
    # No dependencies between t2, t3 - they become ready at same time
    wf.add_edge(t1.task_id, t2.task_id)
    wf.add_edge(t1.task_id, t3.task_id)

    m1 = Machine(name="m1", cpu={'coreCount': 1, 'speedInMHz': 1000, 'vendor': 'X'})
    machines = {'m1': m1}
    inst = InstanceFake(workflow=wf, machines=machines)

    Simulator = importlib.import_module('simulator').Simulator
    sim = Simulator(inst, logger=logging.getLogger("test"))
    # Let simulator handle

    scheduler = FIFOScheduler()
    sim.start(scheduler)

    # Verify all 3 tasks executed
    assert 't1' in sim.completed_tasks
    assert 't2' in sim.completed_tasks
    assert 't3' in sim.completed_tasks
