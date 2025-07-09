from dataclasses import dataclass
from enum import Enum, auto
import time
import logging
from typing import Deque, Dict, Set, List, Optional
from collections import deque

from research.resource import Resource
from research.scheduler import Action, Id, ScheduleTask, ScheduleTaskOnCores, Scheduler, TimeSpan, TransferData
from research.task import TaskState
from research.workflow import Workflow, DataItemState
from research.run_stats import RunStats
    
@dataclass
class DataTransfer:
    data_id: int
    source: Id
    target: Id

@dataclass
class QueuedTask:
    task_id: int
    cores: int
    action_id: int

@dataclass
class RunnerContext:
    start: float = time.time()
    
    def time(self) -> float:
        return time.time() - self.start

class DataTransferMode(Enum):
    # Every data item is automatically transferred between producer and consumer
    # via the master node (producer -> master -> consumer).
    ViaMasterNode = auto()
    # Every data item is automatically transferred between producer and consumer
    # directly (producer -> consumer)
    Direct = auto()

@dataclass
class Config: 
    data_transfer_mode: DataTransferMode = DataTransferMode.ViaMasterNode

class Runner:
    def __init__(self, node_id: int, wf: Workflow, scheduler: Scheduler, resources: List[Resource], config: Config):
        self.id = node_id
        self.action_id = 0  # Unique ID for actions
        
        self.workflow = wf
        self.scheduler = scheduler
        self.resources = resources
        
        # TODO: talvez pode ser uma lista
        self.data_transfers: Dict[int, DataTransfer] = {} # data_id -> DataTransfer
        self.data_location: Dict[int, int] = {}  # data_id -> resource_id
        self.data_transfer_tasks: Dict[Id, Dict[int, List[Id]]] = {}  # source -> {data_id -> [target_ids]}
        self.resource_data_items: Dict[Id, Set[int]] = {}  # resource_id -> {data_ids}
        self.task_location: Dict[int, int] = {}  # task_id -> resource_id
        self.scheduled_actions: Set[int] = set()
        self.resource_queue: List[List[Deque[QueuedTask]]] = [
            [deque() for _ in range(resource.cores)]
            for resource in resources
        ]
        self.available_cores: List[List[int]] = [
            list(range(resource.cores))
            for resource in resources
        ]
        self.task_cores: Dict[int, List[int]] = {}
        self.outputs: Set[int] = set()
        self.actions: List[Action] = []
        
        self.run_stats = RunStats()
        self.ctx = RunnerContext()
        self.config = config
        self.logger = logging.getLogger(f"runner-{node_id}")
    
    def start(self) -> None:
        for data_id, data_item in enumerate(self.workflow.get_data_items()):
            if data_item.state == DataItemState.READY:
                assert data_item.producer is None, \
                  "Non-input data item has Ready state"
                
                self.data_location[data_id] = self.id
                self.resource_data_items[self.id].add(data_id)
            elif not data_item.consumers:
                self.outputs.add(data_id)
        
        self.logger.info(
            "DAG execution: total %d resources, %d tasks, %d data items",
            len(self.resources),
            len(self.workflow.get_tasks()),
            len(self.workflow.get_data_items())
        )
        
        scheduling_start = time.time()
        actions = self.scheduler.start(self.workflow, self.resources)
        scheduling_time = time.time() - scheduling_start
        self.logger.info("scheduled in %.2f seconds", scheduling_time)

        self.run_stats.add_scheduling_time(scheduling_time)
        
        makespan = self._calc_makespan(actions)
        if makespan is not None:
            self.logger.info("Expected makespan: %.2f", makespan)
            self.run_stats.set_expected_makespan(makespan)
        
        self.actions.extend(actions)
        self.process_actions()
    
    def _calc_makespan(self, actions: List[Action]) -> Optional[float]:
        finish_times = []
        
        for action in actions:
            expected_span = None
            
            if isinstance(action, (ScheduleTask, ScheduleTaskOnCores)):
                expected_span = action.expected_span
            
            if expected_span is not None:
                finish_times.append(expected_span.finish)
        
        return max(finish_times) if finish_times else None
    
    def process_actions(self) -> None:
        # TODO: Implementação de processamento de ações
        # for i in 0..self.resources.len() {
        #     self.process_resource_queue(i);
        # }

        for action in self.actions:
            if isinstance(action, ScheduleTask):
                allowed_cores = list(range(self.resources[action.resource].cores))
                self._process_action(action.task, action.resource, action.cores, allowed_cores, action.expected_span)
            elif isinstance(action, ScheduleTaskOnCores):
                action.cores.sort()
                has_duplicate_cores = len(set(action.cores)) != len(action.cores)
                if has_duplicate_cores:
                    self.logger.error(
                        f"Action {action} has duplicate cores {action.cores}."
                    )
                    return
                self._process_action(action.task, action.resource, len(action.cores), action.cores, action.expected_span)
            elif isinstance(action, TransferData):
                self._add_transfer_data_task(action.data_item, action.source, action.target)
            
            self.action_id += 1
    
    def _process_action(
        self,
        task_id: int,
        resource_id: int,
        need_cores: int,
        allowed_cores: List[int],
        expected_span: Optional[TimeSpan]
    ):
        task = self.workflow.get_task(task_id)

        resource = self.resources[resource_id]
        if need_cores > resource.cores:
            self.logger.error(
                f"Wrong action, resource {resource_id} doesn't have enough cores"
            )
            return

        if task.memory > resource.memory:
            self.logger.error(
                f"Wrong action, resource {resource_id} doesn't have enough memory"
            )
            return

        if need_cores < task.min_cores or need_cores > task.max_cores:
            self.logger.error(
                f"Wrong action, task {task_id} doesn't support {need_cores} cores"
            )
            return

        if task.state == TaskState.READY:
            self.workflow.update_task_state(task_id, TaskState.RUNNABLE)
        elif task.state == TaskState.PENDING:
            self.workflow.update_task_state(task_id, TaskState.SCHEDULED)
        else:
            self.logger.error(f"Can't schedule task with state {task.state}")
            return

        data_items = self.workflow.get_task(task_id).inputs
        self.task_location[task_id] = resource_id

        if self.config.data_transfer_mode == DataTransferMode.ViaMasterNode:
            for data_item_id in data_items:
                self._add_transfer_data_task(data_item_id, self.id, self.resources[resource_id].id)

        if self.config.data_transfer_mode == DataTransferMode.Direct:
            for data_item_id in data_items:
                location = self.data_location.get(data_item_id)
                if location and location != self.resources[resource_id].id:
                    self._add_transfer_data_task(data_item_id, location, self.resources[resource_id].id)

        for core in allowed_cores:
            self.resource_queue[resource_id][core].append(
                QueuedTask(
                    task_id=task_id,
                    cores=need_cores,
                    action_id=self.action_id
                )
            )

        if expected_span is not None:
            self.logger.debug(
                f"Expected span for task {task_id} is {expected_span.start} - {expected_span.finish}"
            )

        self.process_resource_queue(resource_id)
    
    def _add_transfer_data_task(self, data_item_id: int, source: Id, target: Id) -> None:
        if data_item_id in self.resource_data_items[source]:
            self._transfer_data(data_item_id, source, target)
        else:
            self.data_transfer_tasks[source][data_item_id].append(target)

    def _transfer_data(self, data_item_id: int, source: Id, target: Id): 
        data_item = self.workflow.get_data_item(data_item_id)
        data_id = len(self.data_transfers.values())
        self.data_transfers[data_id] = DataTransfer(
            data_id=data_item_id,
            source=source,
            target=target
        )

        self.run_stats.set_transfer_start(
            data_id,
            data_item.size,
            self.ctx.time()
        )

    def process_resource_queue(self, resource_idx: int):
        curr_resource_queue = self.resource_queue[resource_idx]
        while len(curr_resource_queue) != 0:
            something_scheduled = False
            needed_cores: Dict[int, int] = dict()  # action_id -> needed cores
            task_ids: Dict[int, int] = dict()      # action_id -> task_id
            ready_cores: Dict[int, List[int]] = dict()   # action_id -> list of ready cores

            for core in self.available_cores[resource_idx]:
                resource_queue = curr_resource_queue[core]
                while len(resource_queue) != 0 and resource_queue[0].action_id in self.scheduled_actions:
                    # Remove already scheduled tasks from the queue
                    resource_queue.popleft()

                if len(resource_queue) == 0:
                    continue

                queued_task = resource_queue[0]
                task = self.workflow.get_task(queued_task.task_id)
                resource = self.resources[resource_idx]
                if task.memory > resource.memory_available:
                    continue

                # Check if all inputs are available on this resource
                if not all(x in self.resource_data_items.get(resource.id, set()) for x in task.inputs):
                    continue

                needed_cores[queued_task.action_id] = queued_task.cores
                task_ids[queued_task.action_id] = queued_task.task_id
                ready_cores.setdefault(queued_task.action_id, []).append(core)

            for action_id, need_cores in needed_cores.items():
                # TODO: isso aqui ta meio estranho
                cores_list = ready_cores.pop(action_id)[:need_cores]
                if len(cores_list) < need_cores:
                    continue

                task_id = task_ids.pop(action_id)
                task = self.workflow.get_task(task_id)
                resource = self.resources[resource_idx]
                if task.memory > resource.memory_available:
                    continue

                for core in cores_list:
                    curr_resource_queue[core].popleft()
                    # check if core is in available cores to remove it (python will raise an error if core is not in the list)
                    if core in self.available_cores[resource_idx]:
                        self.available_cores[resource_idx].remove(core)

                resource.cores_available -= need_cores
                resource.memory_available -= task.memory
                self.task_cores[task_id] = cores_list


                self.workflow.update_task_state(task_id, TaskState.RUNNING)

                # self.start_task(task_id)

                something_scheduled = True
                self.scheduled_actions.add(action_id)
            if not something_scheduled:
                break

    def set_task_start(self, task_id: int):
        task = self.workflow.get_task(task_id)
        location = self.task_location.get(task_id)
        cores = len(self.task_cores.get(task_id, []))

        if location is None:
            self.logger.error(f"Task {task_id} has no location assigned")
            return

        self.run_stats.set_task_start(
            task_id,
            location,
            cores,
            task.memory,
            self.ctx.time()
        )