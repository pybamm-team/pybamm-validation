import pybamm
import matplotlib.pyplot as plt
import itertools


parameters = [
    "Marquis2019",
    "NCA_Kim2011",
    "Ramadass2004",
    "Chen2020",
    "Ecker2015",
]

models = {"SPM": pybamm.lithium_ion.SPM(), "DFN": pybamm.lithium_ion.DFN()}

npts = [4, 8, 16, 32, 64]

solvers = {
    "IDAKLUSolver": pybamm.IDAKLUSolver(),
    "Casadi - safe": pybamm.CasadiSolver(),
    "Casadi - fast": pybamm.CasadiSolver(mode="fast"),
}


fig, axs = plt.subplots(len(solvers), len(models), figsize=(8, 5))

for ax, i, j in zip(
    axs.ravel(),
    itertools.product(solvers.values(), models.values()),
    itertools.product(solvers, models),
):
    for params in parameters:
        time_points = []
        ns = []
        solver = i[0]

        model = i[1].new_copy()

        # load parameter values and process model and geometry
        param = pybamm.ParameterValues(params)

        i = list(i)

        for N in npts:
            var_pts = {
                "x_n": N,  # negative electrode
                "x_s": N,  # separator
                "x_p": N,  # positive electrode
                "r_n": N,  # negative particle
                "r_p": N,  # positive particle
            }
            sim = pybamm.Simulation(
                model, solver=solver, parameter_values=param, var_pts=var_pts
            )

            time = 0
            runs = 20
            for _ in range(0, runs):
                solution = sim.solve([0, 3500])
                time += solution.solve_time.value
            time = time / runs
            state = sim.built_model.concatenated_initial_conditions.shape[0]
            ns.append(state)
            time_points.append(time)

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("number of states")
        ax.set_ylabel("time(s)")
        ax.set_xticks(ns)
        ax.set_xticklabels(ns, fontsize=10)
        ax.set_title(f"{j[1]} with {j[0]}")
        ax.plot(ns, time_points)

plt.tight_layout()
plt.gca().legend(
    parameters,
    loc="upper right",
)

plt.savefig(
    f"benchmarks/benchmark_images/time_vs_no_of_states_{pybamm.__version__}.png"
)


content = f"## Solve Time vs Number of states\n<img src='./benchmarks/benchmark_images/time_vs_no_of_states_{pybamm.__version__}.png'>\n"

with open("./README.md") as original:
    data = original.read()
with open("./README.md", "w") as modified:
    modified.write(f"{content}\n{data}")
