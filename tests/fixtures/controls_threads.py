import pickle
import pyvinecopulib as pv

controls = pv.FitControlsVinecop(
    family_set=pv.one_par,
    selection_criterion="aic",
    show_trace=False,
    parametric_method="mle",
    num_threads=16,
)

with open("controls_threads16.pkl", "wb") as f:
    pickle.dump(controls, f)