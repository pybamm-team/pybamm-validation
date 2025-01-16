import pybamm
import os


def get_release():
    readme = open("./README.md", "r")
    contents = readme.readlines()
    readme.close()
    contents = contents[2:]

    contents.insert(0, f"# PyBaMM validation - {pybamm.__version__}\n")

    readme = open("./README.md", "w")
    for line in contents:
        readme.write(f"{line}")
    readme.close()


def get_prev_version():

    if pybamm.__version__.count(".") == 1:
        if pybamm.__version__[-1] == "1":
            prev_version = f"{int(pybamm.__version__[:2]) - 1}.12"
        else:
            prev_version = f"{pybamm.__version__[:2]}.{int(pybamm.__version__[pybamm.__version__.index('.') + 1:]) - 1}"
    elif pybamm.__version__.count(".") == 2:
        if pybamm.__version__[-1] == "1":
            prev_version = pybamm.__version__[:-2]
        else:
            prev_version = f"{pybamm.__version__[:-2]}.{int(pybamm.__version__[-1]) - 1}"

    return prev_version


def get_version():
    env_file = os.getenv("GITHUB_ENV")

    with open(env_file, "a") as myfile:
        myfile.write(f"VERSION={pybamm.__version__}")


def update_readme():

    prev_version = get_prev_version()

    readme = open("./README.md", "r")
    contents = readme.readlines()
    readme.close()
    for i in range(0, len(contents)):

        if prev_version in contents[i]:

            contents[i] = contents[i].replace(prev_version, f"{pybamm.__version__}")

    readme = open("./README.md", "w")
    for line in contents:
        readme.write(f"{line}")
    readme.close()
