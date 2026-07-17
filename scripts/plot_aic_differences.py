import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


data = pd.read_csv("aic_comparison.csv")
data["diferencia_vine"] = np.abs(
    data["aic_vine"] - data["aic_fixed_matrix_clayton"]
)
data["diferencia_dissmann"] = np.abs(
    data["aic_dissmann"] - data["aic_fixed_matrix_clayton"]
)

differences = {
    "Vine - matriz fija Clayton": data["diferencia_vine"],
    "Dissmann - matriz fija Clayton": data["diferencia_dissmann"],
}

for modelo, columna in [
    ("Vine", "diferencia_vine"),
    ("Dissmann", "diferencia_dissmann"),
]:
    mayores = data.nlargest(2, columna).copy()
    mayores.insert(0, "simulacion", mayores.index + 1)
    print(f"\nDos diferencias absolutas más altas de {modelo} frente al fixed:")
    print(mayores[["simulacion", "vine_id", columna]].to_string(index=False))


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
ax.set_xlabel("Diferencia de AIC")
ax.set_ylabel("Rango acumulado de simulaciones")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("aic_differences.png", dpi=300)
plt.show()
