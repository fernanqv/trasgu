import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


data = pd.read_csv("aic_comparison.csv")
data["vine_difference"] = np.abs(
    data["aic_vine"] - data["aic_fixed_matrix_clayton"]
)
data["dissmann_difference"] = np.abs(
    data["aic_dissmann"] - data["aic_fixed_matrix_clayton"]
)

differences = {
    "Vine - fixed Clayton matrix": data["vine_difference"],
    "Dissmann - fixed Clayton matrix": data["dissmann_difference"],
}

for model, column in [
    ("Vine", "vine_difference"),
    ("Dissmann", "dissmann_difference"),
]:
    largest = data.nlargest(2, column).copy()
    largest.insert(0, "simulation", largest.index + 1)
    print(
        f"\nTwo largest absolute differences for {model} "
        "versus the fixed Clayton matrix:"
    )
    print(largest[["simulation", "vine_id", column]].to_string(index=False))


fig, ax = plt.subplots(figsize=(10, 6))

markers = ["o", "x"]

for (label, difference), marker in zip(differences.items(), markers):
    x = np.sort(difference.dropna().to_numpy())
    y = np.arange(1, len(x) + 1) / len(x)

    ax.plot(
        x,
        y,
        linestyle="none",
        marker=marker,
        markersize=5,
        markerfacecolor="none",
        label=label,
    )

ax.axvline(0, color="gray", linestyle="--", linewidth=1)
ax.set_xlabel("AIC difference")
ax.set_ylabel("Cumulative rank of simulations")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("aic_differences.png", dpi=300)
plt.show()
