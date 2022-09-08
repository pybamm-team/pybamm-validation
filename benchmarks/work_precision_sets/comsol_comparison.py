import pybamm
import os
import pickle
import scipy.interpolate as interp


"-----------------------------------------------------------------------------"
"Pick C_rate and load comsol data"

# C_rate
# NOTE: the results in pybamm stop when a voltage cutoff is reached, so
# for higher C-rate the pybamm solution may stop before the comsol solution
C_rates = {"01": 0.1, "05": 0.5, "1": 1, "2": 2, "3": 3}
C_rate = "1"  # choose the key from the above dictionary of available results

# load the comsol results
comsol_results_path = pybamm.get_parameters_filepath(
    "benchmarks/comsol_results/comsol_{}C.pickle".format(C_rate)
)
comsol_variables = pickle.load(open(comsol_results_path, "rb"))

"-----------------------------------------------------------------------------"
"Create and solve pybamm model"

# load model and geometry
pybamm.set_logging_level("INFO")
pybamm_model = pybamm.lithium_ion.DFN()
geometry = pybamm_model.default_geometry

# load parameters and process model and geometry
param = pybamm_model.default_parameter_values
param.update(
    {
        "Electrode width [m]": 1,
        "Electrode height [m]": 1,
        "Negative electrode conductivity [S.m-1]": 126,
        "Positive electrode conductivity [S.m-1]": 16.6,
        "Current function [A]": 24 * C_rates[C_rate],
    }
)

param.process_model(pybamm_model)
param.process_geometry(geometry)

# create mesh
var_pts = {"x_n": 31, "x_s": 11, "x_p": 31, "r_n": 11, "r_p": 11}
mesh = pybamm.Mesh(geometry, pybamm_model.default_submesh_types, var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, pybamm_model.default_spatial_methods)
disc.process_model(pybamm_model)

# solve model at comsol times
time = comsol_variables["time"]
pybamm_solution = pybamm.CasadiSolver(mode="fast").solve(pybamm_model, time)


# Make Comsol 'model' for comparison
whole_cell = ["negative electrode", "separator", "positive electrode"]
comsol_t = comsol_variables["time"]
L_x = param.evaluate(pybamm_model.param.L_x)


def get_interp_fun(variable_name, domain):
    """
    Create a :class:`pybamm.Function` object using the variable, to allow plotting with
    :class:`pybamm.QuickPlot` (interpolate in space to match edges, and then create
    function to interpolate in time)
    """
    variable = comsol_variables[variable_name]
    if domain == ["negative electrode"]:
        comsol_x = comsol_variables["x_n"]
    elif domain == ["positive electrode"]:
        comsol_x = comsol_variables["x_p"]
    elif domain == whole_cell:
        comsol_x = comsol_variables["x"]

    # Make sure to use dimensional space
    pybamm_x = mesh.combine_submeshes(*domain).nodes * L_x
    variable = interp.interp1d(comsol_x, variable, axis=0)(pybamm_x)

    fun = pybamm.Interpolant(
        comsol_t,
        variable.T,
        pybamm.t * pybamm_model.timescale.evaluate(),
    )

    fun.domains = {"primary": domain}
    fun.mesh = mesh.combine_submeshes(*domain)
    fun.secondary_mesh = None
    return fun


comsol_c_n_surf = get_interp_fun("c_n_surf", ["negative electrode"])
comsol_c_e = get_interp_fun("c_e", whole_cell)
comsol_c_p_surf = get_interp_fun("c_p_surf", ["positive electrode"])
comsol_phi_n = get_interp_fun("phi_n", ["negative electrode"])
comsol_phi_e = get_interp_fun("phi_e", whole_cell)
comsol_phi_p = get_interp_fun("phi_p", ["positive electrode"])
comsol_voltage = pybamm.Interpolant(
    comsol_t,
    comsol_variables["voltage"],
    pybamm.t * pybamm_model.timescale.evaluate(),
)

comsol_voltage.mesh = None
comsol_voltage.secondary_mesh = None

# Create comsol model with dictionary of Matrix variables
comsol_model = pybamm.lithium_ion.BaseModel()
comsol_model.variables = {
    "Negative particle surface concentration [mol.m-3]": comsol_c_n_surf,
    "Electrolyte concentration [mol.m-3]": comsol_c_e,
    "Positive particle surface concentration [mol.m-3]": comsol_c_p_surf,
    "Current [A]": pybamm_model.variables["Current [A]"],
    "Negative electrode potential [V]": comsol_phi_n,
    "Electrolyte potential [V]": comsol_phi_e,
    "Positive electrode potential [V]": comsol_phi_p,
    "Terminal voltage [V]": comsol_voltage,
}

# Make new solution with same t and y
# Update solution scales to match the pybamm model
comsol_model.timescale_eval = pybamm_model.timescale_eval
comsol_model.length_scales_eval = pybamm_model.length_scales_eval
comsol_solution = pybamm.Solution(
    pybamm_solution.t, pybamm_solution.y, comsol_model, {}
)

# plot
output_variables = [
    "Negative particle surface concentration [mol.m-3]",
    "Electrolyte concentration [mol.m-3]",
    "Positive particle surface concentration [mol.m-3]",
    "Current [A]",
    "Negative electrode potential [V]",
    "Electrolyte potential [V]",
    "Positive electrode potential [V]",
    "Terminal voltage [V]",
]
plot = pybamm.QuickPlot(
    [pybamm_solution, comsol_solution],
    output_variables=output_variables,
    labels=["PyBaMM", "Comsol"],
)
# plot.dynamic_plot()
plot.plot(500)


plot.fig.savefig(
    f"./benchmarks/benchmark_images/comsol_comparison_{pybamm.__version__}.png", dpi=300
)

# content = f"## Comsol comparison\n<img src='./benchmark_images/comsol_comparison_{pybamm.__version__}.png'>\n"  # noqa

# with open("./benchmarks/validation.md", "r") as original:
#     data = original.read()
# with open("./benchmarks/validation.md", "w") as modified:
#     modified.write(f"{content}\n{data}")
