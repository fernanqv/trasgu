import numpy as np  # general module for numerical computations
import pyvinecopulib as pv  # module for vine copula modeling
import os
from chimera_tools import load_matrices_from_h5


if __name__ == "__main__":
    # sampling matrix
    # load matrices_nodes8.pkl in matrix

    # with open("matrices_nodes8.pkl", "rb") as f:
    #     matrices = pickle.load(f)
    # matrix = matrices[0].matrix
    # Create inputs folder if it does not exist

    if not os.path.exists("inputs"):
        os.makedirs("inputs")

    for n_vars in range(4, 9):
        raw_matrix = load_matrices_from_h5(
            f"chimera/chimera{n_vars}.h5", start=10, end=11
        )
        # pyvinecopulib expects Fortran-ordered uint64 matrices
        matrix = np.array(raw_matrix[0], dtype=np.uint64, order="F", copy=True)

        # copula parameters for different scenarios
        cop_pars = {}
        cop_pars["gauss"] = [0.8, 0.6, 0.4, 0.2, 0.1]
        cop_pars["gumbel"] = [2.5798, 1.7545, 1.3820, 1.1560, 1.0716]
        cop_pars["clayton"] = [3.1819, 1.5046, 0.7585, 0.3102, 0.1429]
        cop_pars["frank"] = [7.9019, 4.4659, 2.6100, 1.2238, 0.6029]
        # cop_pars["gauss"] = [0.8, 0.8, 0.8, 0.8]
        # cop_pars["gumbel"] = [2.5798, 2.5798,2.5798,2.5798]
        # cop_pars["clayton"] = [3.1819, 3.1819, 3.1819, 3.1819]
        # cop_pars["frank"] = [7.9019, 7.9019, 7.9019, 7.9019]
        ind_scene = {"high": 0, "med": 1, "low": 3}
        # set some pretty printin
        print(
            f"{'cops':<8} {'sc ene':7} {'n':>5} {'aic_tr':>9} {'dm_aic':>9} {'bf_tr_aic':>9} {'time':>6}"
        )
        # looping over different sample sizes, copula families, and dependency scenarios
        for n_samples in [100, 500]:
            for pcs_name in ["gumbel", "clayton", "gauss"]:
                for scene in ["low", "med", "high"]:
                    # setup copulas to be used for sampling
                    if pcs_name == "gauss":
                        cop = pv.Bicop(
                            pv.BicopFamily.gaussian,
                            0,
                            np.array([[cop_pars[pcs_name][ind_scene[scene]]]]),
                        )
                    elif pcs_name == "gumbel":
                        cop = pv.Bicop(
                            pv.BicopFamily.gumbel,
                            0,
                            np.array([[cop_pars[pcs_name][ind_scene[scene]]]]),
                        )
                    elif pcs_name == "clayton":
                        cop = pv.Bicop(
                            pv.BicopFamily.clayton,
                            0,
                            np.array([[cop_pars[pcs_name][ind_scene[scene]]]]),
                        )
                    elif pcs_name == "frank":
                        cop = pv.Bicop(
                            pv.BicopFamily.frank,
                            0,
                            np.array([[cop_pars[pcs_name][ind_scene[scene]]]]),
                        )
                    else:
                        print("error")
                    # setup copula structure for sampling
                    pc = {}
                    pc[8] = [
                        [cop, cop, cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop],
                        [cop, cop, cop],
                        [cop, cop],
                        [cop],
                    ]
                    pc[7] = [
                        [cop, cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop],
                        [cop, cop, cop],
                        [cop, cop],
                        [cop],
                    ]
                    pc[6] = [
                        [cop, cop, cop, cop, cop],
                        [cop, cop, cop, cop],
                        [cop, cop, cop],
                        [cop, cop],
                        [cop],
                    ]
                    pc[5] = [
                        [cop, cop, cop, cop],
                        [cop, cop, cop],
                        [cop, cop],
                        [cop],
                    ]
                    pc[4] = [
                        [cop, cop, cop],
                        [cop, cop],
                        [cop],
                    ]
                    # specify family set of copulas to be used in fitting
                    family_set = pv.one_par
                    # get a vinecopula to sample from with the specified structure and copulas
                    sample_vc = pv.Vinecop.from_structure(
                        matrix=matrix, pair_copulas=pc[n_vars]
                    )
                    # detect the number of nodes of the matrix (to get all the matrices of the same size later)
                    # get a sample to work with
                    data = sample_vc.simulate(n_samples)
                    np.savetxt(
                        f"inputs/input{n_vars}_{n_samples}_{pcs_name}_{scene}.txt", data
                    )
