from __future__ import annotations

import matplotlib.pyplot as plt
from metrics import SimulationMetrics

def plot_metric_comparison(
  algorithms: list[str],
  metrics_by_algorithm: dict[str, SimulationMetrics],
  dag_name: str,
) -> None:
  metrics_to_plot = {
    "Makespan": lambda m: m.makespan(),
    "SLR": lambda m: m.slr(),
    "Load balance": lambda m: m.loadBalance(),
    "Communication cost": lambda m: m.communicationCost(),
    "Total wait time": lambda m: m.totalWaitTime(),
  }

  cmap = plt.get_cmap("tab10")
  colors = {alg: cmap(i % 10) for i, alg in enumerate(algorithms)}

  for metric_label, get_metric_val in metrics_to_plot.items():
    data = sorted(
      [(alg, get_metric_val(metrics_by_algorithm[alg])) for alg in algorithms],
      key=lambda item: item[1]
    )
    sorted_algs, sorted_vals = zip(*data) if data else ((), ())

    plt.figure(figsize=(10, 5), constrained_layout=True)
    
    plt.grid(axis='y', linestyle=':', alpha=0.4, zorder=1)

    bars = plt.bar(
      sorted_algs, 
      sorted_vals, 
      color=[colors[alg] for alg in sorted_algs], 
      edgecolor="#333333",
      linewidth=0.8,
      alpha=0.85,
      zorder=2
    )
    
    best_val = sorted_vals[0] if sorted_vals else 1.0
    custom_labels = []
    
    for val in sorted_vals:
      val_str = f"{val:.3f}" 
      
      if val == best_val:
        custom_labels.append(f"{val_str}\n(best)")
      else:
        pct_diff = ((val - best_val) / best_val * 100) if best_val != 0 else 0.0
        custom_labels.append(f"{val_str}\n+{pct_diff:.2f}%")

    plt.bar_label(
      bars, 
      labels=custom_labels, 
      padding=4, 
      color="#111827", 
      fontsize=9,
      bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.5)
    )

    if sorted_vals:
      min_val = min(sorted_vals)
      max_val = max(sorted_vals)
      diff = max_val - min_val
      
      if diff > 0:
        padding = diff * 0.15
        plt.ylim(min_val - padding, max_val + (padding * 2.5))
      else:
        plt.ylim(min_val * 0.9, max_val * 1.2)

    plt.title(metric_label)
    plt.ylabel(metric_label)
    plt.xticks(rotation=30)
    plt.suptitle(f"Scheduler comparison for {dag_name}")

    plt.show()