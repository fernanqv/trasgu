import pickle
from pathlib import Path

import pyvinecopulib as pv

controls_path = Path(__file__).with_name("controls.pkl")

controls = pv.FitControlsVinecop(
    family_set=pv.one_par,
    selection_criterion="aic",
    show_trace=False,
    parametric_method="mle",
)

with open(controls_path, "wb") as f:
    pickle.dump(controls, f)

with open(controls_path, "rb") as f:
    loaded_controls = pickle.load(f)

print(loaded_controls)
