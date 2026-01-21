import pyvinecopulib as pv
import pickle

controls = pv.FitControlsVinecop(
    family_set=pv.one_par,
    selection_criterion="aic",
    show_trace=False,
    parametric_method="mle",
)

controls

with open("controls.pkl", "wb") as f:
    pickle.dump(controls, f)
# Cargar
with open("controls.pkl", "rb") as f:
    controls = pickle.load(f)