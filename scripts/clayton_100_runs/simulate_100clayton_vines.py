from pathlib import Path

import numpy as np
import pyvinecopulib as pv


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_CONFIG = BASE_DIR / "trasgu.yaml"
SIMULATIONS_DIR = BASE_DIR / "simulations"
N_ITERATIONS = 100

# Matrix ID: ****
matrix = np.array(
    [
        [7, 1, 6, 3, 4, 6, 6],
        [3, 6, 4, 4, 6, 4, 0],
        [4, 4, 3, 6, 3, 0, 0],
        [6, 3, 7, 7, 0, 0, 0],
        [1, 7, 1, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0],
        [5, 0, 0, 0, 0, 0, 0],
    ]
)

bicop = pv.Bicop(pv.clayton, parameters=np.array([[6.8]]))
pair_copulas = [
    [bicop, bicop, bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop],
    [bicop, bicop],
    [bicop],
]

vinecop = pv.Vinecop.from_structure(matrix=matrix, pair_copulas=pair_copulas)
template_config = TEMPLATE_CONFIG.read_text()
SIMULATIONS_DIR.mkdir(exist_ok=True)

for iteration in range(1, N_ITERATIONS + 1):
    run_dir = SIMULATIONS_DIR / f"iteration_{iteration}"
    run_dir.mkdir(exist_ok=True)

    samples = vinecop.simulate(300)
    np.savetxt(run_dir / "vinecop_samples.txt", samples, delimiter=" ")
    (run_dir / "trasgu.yaml").write_text(template_config)
