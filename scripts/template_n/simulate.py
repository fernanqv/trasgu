import argparse
import shutil
from pathlib import Path

import numpy as np
import pyvinecopulib as pv
import yaml

from trasgu import Trasgu


BASE_DIR = Path(__file__).resolve().parent
SIMULATIONS_DIR = BASE_DIR / "simulations"

parser = argparse.ArgumentParser()
parser.add_argument("iterations", type=int, help="Number of simulations to generate")
args = parser.parse_args()
if args.iterations < 1:
    parser.error("iterations must be greater than zero")

tr = Trasgu(str(BASE_DIR / "trasgu.yaml"))
matrix = tr.get_matrix(148682)[0]
print(matrix)

bicop = pv.Bicop(pv.clayton, parameters=np.array([[3.1819]]))
pair_copulas = [
    [bicop, bicop, bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop, bicop],
    [bicop, bicop, bicop],
    [bicop, bicop],
    [bicop],
]

controls_dissmann = pv.FitControlsVinecop(
    family_set=pv.one_par,
    tree_criterion="tau",
    selection_criterion="aic",
    parametric_method="mle",
    show_trace=False,
)
controls_clayton = pv.FitControlsVinecop(
    family_set=[pv.clayton],
    tree_criterion="tau",
    selection_criterion="aic",
    parametric_method="mle",
    show_trace=False,
)

vinecop = pv.Vinecop.from_structure(matrix=matrix, pair_copulas=pair_copulas)

SIMULATIONS_DIR.mkdir(exist_ok=True)

for iteration in range(1, args.iterations + 1):
    run_dir = SIMULATIONS_DIR / f"iteration_{iteration}"
    run_dir.mkdir(exist_ok=True)

    samples = vinecop.simulate(300)
    np.savetxt(run_dir / "vinecop_samples.txt", samples, delimiter=" ")
    shutil.copyfile(BASE_DIR / "trasgu.yaml", run_dir / "trasgu.yaml")

    ground_truth_aic = vinecop.aic(samples)
    model = pv.Vinecop.from_data(samples, controls=controls_dissmann)
    vinecop_clayton = pv.Vinecop.from_data(
        samples, matrix=matrix, controls=controls_clayton
    )

    result = {
        "aic_dissmann": float(model.aic()),
        "aic_fixed_matrix_clayton": float(vinecop_clayton.aic()),
        "aic_ground_truth": float(ground_truth_aic),
        "matrix": model.matrix.tolist(),
    }
    with open(run_dir / "references.yaml", "w", encoding="utf-8") as output_file:
        yaml.safe_dump(result, output_file, sort_keys=False)
    print(result)
