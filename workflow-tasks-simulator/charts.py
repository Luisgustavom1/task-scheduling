import pathlib
from metrics import SimulationMetrics
import matplotlib.pyplot as plt

def plot_machine_scaling(
  algorithms: list[str],
  metrics_by_machine_count: dict[int, dict[str, SimulationMetrics]],
  output_dir: pathlib.Path,
) -> None:
  metrics_to_plot = {
    "Makespan": lambda m: m.makespan(),
    "SLR": lambda m: m.slr(),
    "Balanceamento de carga": lambda m: m.loadBalance(),
    "Custo de comunicação": lambda m: m.communicationCost(),
    "Tempo total de espera": lambda m: m.totalWaitTime(),
  }
  machine_counts = sorted(metrics_by_machine_count.keys())

  cmap = plt.get_cmap("tab10")
  color_map = {alg: cmap(i % 10) for i, alg in enumerate(algorithms)}

  for metric_label, get_metric_val in metrics_to_plot.items():
    plt.figure(figsize=(12, 6), constrained_layout=True)

    x_positions = list(range(len(machine_counts)))
    group_width = 0.85
    bar_width = group_width / max(len(algorithms), 1)

    best_vals = {}
    for c in machine_counts:
      vals = [get_metric_val(metrics_by_machine_count[c][alg]) for alg in algorithms]
      if metric_label == "Balanceamento de carga":
        best_vals[c] = min(vals, key=lambda x: abs(x - 1.0))
      else:
        best_vals[c] = min(vals)

    global_max_y = 0.0

    for index, algorithm in enumerate(algorithms):
      offset = (index - len(algorithms) / 2) * bar_width + bar_width / 2
      bar_positions = [x + offset for x in x_positions]
      
      y_vals = [get_metric_val(metrics_by_machine_count[c][algorithm]) for c in machine_counts]
      
      if y_vals:
        global_max_y = max(global_max_y, max(y_vals))
      
      bars = plt.bar(
        bar_positions,
        y_vals,
        width=bar_width,
        color=color_map[algorithm],
        edgecolor="black",
        linewidth=1.2,
        label=algorithm,
        zorder=3
      )

      custom_labels = []
      for c, val in zip(machine_counts, y_vals):
        best = best_vals[c]
        val_str = f"{val:.3f}"
        
        if val == best:
          custom_labels.append(f"{val_str}\n(melhor)")
        else:
          if metric_label == "Balanceamento de carga":
            dist_to_best = abs(val - best)
            custom_labels.append(f"{val_str}\n(Δ={dist_to_best:.3f})")
          else:
            pct_diff = ((val - best) / best * 100) if best != 0 else 0.0
            custom_labels.append(f"{val_str}\n+{pct_diff:.2f}%")

      plt.bar_label(
        bars, 
        labels=custom_labels, 
        padding=4, 
        color="#111827", 
        fontsize=8,
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5),
        zorder=4
      )

    plt.xlabel("Número de Máquinas", fontsize=14)
    plt.ylabel("SLR Médio" if metric_label == "SLR" else metric_label, fontsize=14)
    
    plt.xticks(x_positions, machine_counts, fontsize=12)
    plt.yticks(fontsize=12)
    
    plt.ylim(0, global_max_y * 1.35)

    plt.tick_params(axis='both', direction='in', top=True, right=True, length=6)
    plt.legend(loc="upper left", frameon=True, edgecolor="black", fontsize=10, borderpad=0.6)

    if metric_label == "Balanceamento de carga":
      plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, zorder=0)

    safe_metric_name = metric_label.replace(" ", "_").lower()
    
    file_path = output_dir / f"{safe_metric_name}.png"
    
    plt.savefig(file_path, bbox_inches='tight', dpi=300)
    plt.close()