from __future__ import annotations

import hashlib
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Circle, FancyBboxPatch


class SchedulerVisualizer:
  def __init__(self, title: str = "Task Scheduler", animate: bool = True, frame_delay: float = 0.03):
    self.title = title
    self.animate = animate
    self.frame_delay = frame_delay

    self.simulator = None
    self.workflow_graph: nx.DiGraph | None = None
    self.graph_positions: dict[str, tuple[float, float]] = {}
    self.processor_order: list[str] = []
    self.processor_rows: dict[str, float] = {}
    self.task_status: dict[str, str] = {}
    self.task_records: dict[str, dict[str, float | str]] = {}
    self.max_end_time = 1.0

    self.fig = None
    self.graph_ax = None
    self.timeline_ax = None

  def attach(self, simulator: Any):
    self.simulator = simulator
    self.processor_order = list(simulator.processors.keys())
    self.processor_rows = {processor_id: len(self.processor_order) - 1 - index for index, processor_id in enumerate(self.processor_order)}
    self.task_status = {task_id: "pending" for task_id in simulator.workflow.tasks}
    self.task_records = {}
    self.max_end_time = 1.0

    workflow_graph = nx.DiGraph()
    for task_id in simulator.workflow.tasks:
      workflow_graph.add_node(task_id)
    for parent_id, children in simulator.workflow.tasks_children.items():
      for child_id in children:
        workflow_graph.add_edge(parent_id, child_id)

    self.workflow_graph = workflow_graph
    if len(workflow_graph) > 0:
      self.graph_positions = nx.spring_layout(workflow_graph, seed=42)
    else:
      self.graph_positions = {}

    plt.ion()
    self.fig, (self.graph_ax, self.timeline_ax) = plt.subplots(
      2,
      1,
      figsize=(15, 8),
      gridspec_kw={"height_ratios": [1.1, 1.4]},
      constrained_layout=True,
    )
    self.fig.patch.set_facecolor("#0f172a")
    self.fig.suptitle(self.title, color="white", fontsize=16, fontweight="bold")

    self._draw_scene()
    self._flush()

  def on_task_scheduled(self, task, processor_id: str, start_time: float, end_time: float, ready_time: float):
    del ready_time

    if self.simulator is None:
      return

    task_id = task.task_id
    self.task_status[task_id] = "running"
    if end_time > self.max_end_time:
      self.max_end_time = end_time

    if self.animate and not task_id.startswith("artificial_"):
      self._animate_task(task_id, processor_id, start_time, end_time)

    self.task_records[task_id] = {
      "task_id": task_id,
      "processor_id": processor_id,
      "start": start_time,
      "end": end_time,
    }
    self.task_status[task_id] = "done"
    self._draw_scene()
    self._flush()

  def finalize(self):
    self._draw_scene()
    self._flush()
    plt.ioff()
    plt.show(block=True)

  def _animate_task(self, task_id: str, processor_id: str, start_time: float, end_time: float):
    lane_y = self.processor_rows[processor_id]
    destination_x = start_time + max(end_time - start_time, 0.05) / 2
    source_x = -1.0
    source_y = len(self.processor_order) + 0.35
    steps = 4

    for frame_index in range(steps + 1):
      progress = frame_index / steps
      token_x = source_x + (destination_x - source_x) * progress
      token_y = source_y + (lane_y - source_y) * progress
      self._draw_scene(active_token=(token_x, token_y, task_id), highlight_task=task_id)
      self._flush()

  def _draw_scene(self, active_token: tuple[float, float, str] | None = None, highlight_task: str | None = None):
    if self.graph_ax is None or self.timeline_ax is None:
      return

    self.graph_ax.clear()
    self.timeline_ax.clear()

    self._style_axes()
    self._draw_workflow_graph(highlight_task=highlight_task)
    self._draw_processor_timeline(active_token=active_token, highlight_task=highlight_task)

  def _style_axes(self):
    for ax in (self.graph_ax, self.timeline_ax):
      ax.set_facecolor("#111827")
      ax.tick_params(colors="#e5e7eb")
      for spine in ax.spines.values():
        spine.set_color("#334155")

  def _draw_workflow_graph(self, highlight_task: str | None = None):
    if self.workflow_graph is None:
      return

    ax = self.graph_ax
    ax.set_title("Workflow Graph", color="white", fontweight="bold", loc="left")
    ax.axis("off")

    if len(self.workflow_graph) == 0:
      return

    node_colors = []
    node_sizes = []
    labels = {}

    for task_id in self.workflow_graph.nodes:
      status = self.task_status.get(task_id, "pending")
      if task_id.startswith("artificial_"):
        base_color = "#38bdf8"
      elif status == "done":
        base_color = "#22c55e"
      elif status == "running":
        base_color = "#f59e0b"
      else:
        base_color = "#64748b"

      if highlight_task == task_id:
        node_sizes.append(1600)
      else:
        node_sizes.append(1200 if status == "running" else 1000)

      node_colors.append(base_color)
      labels[task_id] = task_id.replace("artificial_", "")

    nx.draw_networkx_edges(
      self.workflow_graph,
      self.graph_positions,
      ax=ax,
      edge_color="#94a3b8",
      alpha=0.35,
      arrows=False,
      width=1.6,
    )
    nx.draw_networkx_nodes(
      self.workflow_graph,
      self.graph_positions,
      ax=ax,
      node_color=node_colors,
      node_size=node_sizes,
      linewidths=1.5,
      edgecolors="#e2e8f0",
    )
    nx.draw_networkx_labels(
      self.workflow_graph,
      self.graph_positions,
      ax=ax,
      labels=labels,
      font_size=8,
      font_color="white",
    )

  def _draw_processor_timeline(self, active_token: tuple[float, float, str] | None = None, highlight_task: str | None = None):
    ax = self.timeline_ax
    ax.set_title("Processors and Running Tasks", color="white", fontweight="bold", loc="left")

    max_x = max(self.max_end_time, 1.0) * 1.15 + 0.8
    left_margin = -1.8
    ax.set_xlim(left_margin, max_x)
    ax.set_ylim(-0.75, len(self.processor_order) + 0.9)
    ax.set_xlabel("Time", color="#e5e7eb")
    ax.set_yticks([])

    ax.axvline(0, color="#475569", linestyle="--", linewidth=1.0, alpha=0.65)
    ax.text(
      left_margin + 0.05,
      len(self.processor_order) + 0.45,
      "ready queue",
      color="#94a3b8",
      fontsize=9,
      ha="left",
      va="center",
    )

    for processor_id in self.processor_order:
      lane_y = self.processor_rows[processor_id]
      lane = FancyBboxPatch(
        (0, lane_y - 0.35),
        max_x,
        0.7,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.0,
        edgecolor="#334155",
        facecolor="#1e293b",
        alpha=0.95,
      )
      ax.add_patch(lane)
      ax.text(
        left_margin + 0.12,
        lane_y,
        processor_id,
        color="white",
        fontsize=9,
        fontweight="bold",
        va="center",
        ha="left",
      )

    for task_record in sorted(self.task_records.values(), key=lambda item: float(item["start"])):
      task_id = str(task_record["task_id"])
      processor_id = str(task_record["processor_id"])
      lane_y = self.processor_rows[processor_id]
      start_time = float(task_record["start"])
      end_time = float(task_record["end"])
      duration = max(end_time - start_time, 0.04)
      color = self._task_color(task_id)
      bar = FancyBboxPatch(
        (start_time, lane_y - 0.23),
        duration,
        0.46,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.1,
        edgecolor="#e2e8f0",
        facecolor=color,
        alpha=0.95,
      )
      ax.add_patch(bar)
      if duration > 0.45:
        ax.text(
          start_time + duration / 2,
          lane_y,
          task_id.replace("artificial_", ""),
          color="#0f172a",
          fontsize=8,
          fontweight="bold",
          ha="center",
          va="center",
        )

    if active_token is not None:
      token_x, token_y, task_id = active_token
      token = Circle((token_x, token_y), radius=0.18, facecolor=self._task_color(task_id), edgecolor="white", linewidth=1.5, zorder=10)
      ax.add_patch(token)
      ax.text(
        token_x,
        token_y + 0.28,
        task_id.replace("artificial_", ""),
        color="white",
        fontsize=7,
        fontweight="bold",
        ha="center",
        va="bottom",
        zorder=11,
      )

    ax.grid(axis="x", color="#334155", alpha=0.35, linestyle=":")

  def _task_color(self, task_id: str) -> str:
    digest = hashlib.md5(task_id.encode("utf-8")).hexdigest()
    hue_seed = int(digest[:6], 16)
    palette = ["#38bdf8", "#22c55e", "#f97316", "#e879f9", "#14b8a6", "#f43f5e", "#a78bfa", "#facc15"]
    return palette[hue_seed % len(palette)]

  def _flush(self):
    if self.fig is None:
      return

    self.fig.canvas.draw_idle()
    plt.pause(self.frame_delay)