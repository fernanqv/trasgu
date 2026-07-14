from pathlib import Path

import numpy as np
import pyvinecopulib as pv


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_CONFIG = BASE_DIR / "trasgu.yaml"
SIMULATIONS_DIR = BASE_DIR / "simulations"
N_ITERATIONS = 100

# CHIMERA MATRIX 7 VARS: 25200
matrix_inv= np.array(
    [ [ 7, 7, 3, 4, 4, 7, 6 ],
      [ 0, 3, 7, 3, 3, 3, 4 ],
      [ 0, 0, 4, 7, 2, 4, 3 ],
      [ 0, 0, 0, 2, 7, 2, 2 ],
      [ 0, 0, 0, 0, 6, 6, 7 ],
      [ 0, 0, 0, 0, 0, 5, 5 ],
      [ 0, 0, 0, 0, 0, 0, 1 ]
    ]
)

matrix = matrix_inv[:, ::-1]
print(matrix)

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
