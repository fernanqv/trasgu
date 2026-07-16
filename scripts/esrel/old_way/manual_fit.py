from get_matrices import get_matrices
import numpy as np
import pyvinecopulib as pv


matrices5 = get_matrices("./", nodes=5)

family_set = pv.one_par
controls = pv.FitControlsVinecop(family_set=family_set, selection_criterion="aic", show_trace=False)

i=0
for matrix in matrices5:
    data = np.loadtxt("/gpfs/users/fernandezv/repos/trasgu/scripts/esrel/simulations/iteration_1/vinecop_samples.txt")
    # setup sample VC with given matrix and given copulas
    cop = pv.Vinecop.from_data(data, matrix=matrix.matrix, controls=controls)
    print(f"{i}, {cop.aic()}")
    i=i+1


