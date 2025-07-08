from dataclasses import dataclass
import time
import logging
from typing import Dict, Set, List, Optional, Any
from collections import defaultdict

from research.resource import Resource
from research.scheduler import Action, Id, ScheduleTask, ScheduleTaskOnCores, Scheduler, TransferData
from workflow import Workflow, DataItemState

@dataclass
class RunStats:
    scheduling_times: List[float] = []
    expected_makespan: Optional[float] = None
    total_network_traffic: float = 0.0
    transfer_starts: Dict[int, float] = {}  # data_item -> start_time
    
    def add_scheduling_time(self, time_seconds: float) -> None:
        self.scheduling_times.append(time_seconds)
    
    def set_expected_makespan(self, makespan: float) -> None:
        self.expected_makespan = makespan

    def set_transfer_start(self, data_item: int, size: float, time: float):
        self.total_network_traffic += size;
        self.transfer_starts[data_item] = time;

@dataclass
class DataTransfer:
    data_id: int
    source: Id
    target: Id

@dataclass
class RunnerContext:
    start: float = time.time()
    
    def time(self) -> float:
        return time.time() - self.start

class Runner:
    def __init__(self, node_id: int, wf: Workflow, scheduler: Scheduler, resources: List[Resource], network: Any):
        self.id = node_id
        
        self.workflow = wf
        self.scheduler = scheduler
        self.resources = resources
        self.network = network
        
        # TODO: talvez pode ser uma lista
        self.data_transfers: Dict[int, DataTransfer] = {} # data_id -> DataTransfer
        self.data_location: Dict[int, int] = {}  # data_id -> resource_id
        self.data_transfer_tasks: Dict[Id, Dict[int, List[Id]]] = {}  # source -> {data_id -> [target_ids]}
        self.resource_data_items: Dict[Id, Set[int]] = {}  # resource_id -> {data_ids}
        self.outputs: Set[int] = set()
        self.actions: List[Action] = []
        
        self.run_stats = RunStats()
        self.ctx = RunnerContext()
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
        for action in self.actions:
            if isinstance(action, ScheduleTask):
                self._schedule_task(action)
            elif isinstance(action, ScheduleTaskOnCores):
                self._schedule_task_on_cores(action)
            elif isinstance(action, TransferData):
                self._add_transfer_data_task(action)
    
    def _schedule_task(self, action: ScheduleTask) -> None:
        """Agenda uma tarefa em um recurso específico"""
        self.logger.debug("Scheduling task %d on resource %d", 
                         action.task_id, action.resource_id)
        # Implementação específica do scheduling
        pass
    
    def _schedule_task_on_cores(self, action: ScheduleTaskOnCores) -> None:
        """Agenda uma tarefa em cores específicos de um recurso"""
        self.logger.debug("Scheduling task %d on resource %d, cores %s", 
                         action.task_id, action.resource_id, action.cores)
        # Implementação específica do scheduling em cores
        pass
    
    def _add_transfer_data_task(self, action: TransferData) -> None:
        if action.data_item in self.resource_data_items[action.source]:
            self._transfer_data(action)
        else:
            self.data_transfer_tasks[action.source][action.data_item].append(action.target)
        pass

    def _transfer_data(self, action: TransferData): 
        data_item = self.workflow.get_data_item(action.data_item)
        data_id = len(self.data_transfers.values())
        self.data_transfers[data_id] = DataTransfer(
            data_id=action.data_item,
            source=action.source,
            target=action.target
        )

        self.run_stats.set_transfer_start(
            data_id,
            data_item.size,
            self.ctx.time()
        )