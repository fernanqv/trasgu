#!/usr/bin/env python3

from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, spearmanr


data_file = Path(__file__).parent / "simulations/iteration_1/vinecop_samples.txt"
data = np.loadtxt(data_file)

spearman = spearmanr(data).statistic

kendall = np.eye(data.shape[1])
for i in range(data.shape[1]):
    for j in range(i + 1, data.shape[1]):
        correlation = kendalltau(data[:, i], data[:, j]).statistic
        kendall[i, j] = correlation
        kendall[j, i] = correlation

print("Spearman:")
print(spearman)
print("\nKendall:")
print(kendall)
