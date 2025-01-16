import pybamm
import os


def get_release():
    readme = open("./README.md", "r")
    contents = readme.readlines()
    readme.close()

    contents.insert(0, f"# PyBaMM validation - {pybamm.__version__}\n")

    readme = open("./README.md", "w")
    for line in contents:
        readme.write(f"{line}")
    readme.close()


def get_version():
    env_file = os.getenv("GITHUB_ENV")

    with open(env_file, "a") as myfile:
        myfile.write(f"VERSION={pybamm.__version__}")
