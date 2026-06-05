from __future__ import annotations

import math
from typing import Callable

import matplotlib.pyplot as plt

from metrics import SimulationMetrics

MetricDefinition = tuple[str, Callable[[SimulationMetrics], float]]


def format_value(value: float, max_decimals: int = 8) -> str:
  if not math.isfinite(value):
    return str(value)

  if max_decimals <= 0:
    return str(math.trunc(value))

  scale = 10 ** max_decimals
  truncated = math.trunc(value * scale) / scale
  text = f"{truncated:.{max_decimals}f}".rstrip("0").rstrip(".")
  return "0" if text == "-0" else text


def plot_metric_comparison(
  algorithms: list[str],
  metrics_by_algorithm: dict[str, SimulationMetrics],
  dag_name: str,
) -> None:
  metric_definitions: list[MetricDefinition] = [
    ("Makespan", lambda metrics: metrics.makespan()),
    ("SLR", lambda metrics: metrics.slr()),
    ("Load balance", lambda metrics: metrics.loadBalance()),
    ("Communication cost", lambda metrics: metrics.communicationCost()),
    ("Total wait time", lambda metrics: metrics.totalWaitTime()),
  ]

  for metric_label, metric_func in metric_definitions:
    fig, (ax, list_ax) = plt.subplots(
      2,
      1,
      figsize=(11, 4.9),
      gridspec_kw={"height_ratios": [3.2, 1]},
      constrained_layout=True,
    )
    values = [metric_func(metrics_by_algorithm[algorithm]) for algorithm in algorithms]
    ax.plot(algorithms, values, color="#2563eb", linewidth=2.2, marker="o", markersize=6)
    ax.fill_between(algorithms, values, color="#2563eb", alpha=0.12)
    for algorithm, value in zip(algorithms, values):
      ax.annotate(
        format_value(float(value), max_decimals=8),
        (algorithm, value),
        textcoords="offset points",
        xytext=(0, 6),
        ha="center",
        color="#111827",
        fontsize=9,
      )
    ax.set_title(metric_label)
    ax.set_ylabel(metric_label)
    ax.tick_params(axis="x", rotation=30)

    sorted_pairs = sorted(zip(algorithms, values), key=lambda item: item[1])
    list_lines = [
      "Sorted by metric (ascending):",
      *[
        f"{index}. {algorithm} = {format_value(float(value), max_decimals=8)}"
        for index, (algorithm, value) in enumerate(sorted_pairs, start=1)
      ],
    ]
    list_ax.axis("off")
    list_ax.text(
      0.01,
      0.95,
      "\n".join(list_lines),
      transform=list_ax.transAxes,
      va="top",
      ha="left",
      color="#111827",
      fontsize=9,
    )
    fig.suptitle(f"Scheduler comparison for {dag_name}")

  plt.show()
