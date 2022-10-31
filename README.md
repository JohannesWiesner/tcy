# Description
This repository contains a spreadsheet `csp_packages.tsv` that gives information about `conda` and `pip` packages that are used by the CSP lab. It also contains a `environment.yml` file that is supposed to contain the same information as `csp_packages.tsv` in order to create a conda environment that contains all the packages found in the spreadsheet.
# Aims
New lab members can download this repository and use `environment.yml` to create a conda environment that contains all the packages that the CSP lab needs. `environment.yml`  contains all the packages that can be found in the  spreadsheets (with a few exceptions packages that are bug flagged but may be available in the future when the developers of these packages fixed the bugs). This will allow users to get a computational environment with `R`,  `python` and all the packages they need to perform their analyses.
# How to use
1.) After  installing Miniconda on their machines, users specify these variables in `get_yml_from_csv`:

- `name` (your first name)
- `surname` (your surname)
- `pip_requirements_file` (should pip packages be written to a `requirements.txt`file or should they directly
be written in the .yml file itself? Default is True)
- `write_conda_channels` (should the conda channels be directly specified for each package (e.g. `conda-forge::spyder`)? If true, only the `default` channel appears in the `channels` section and all other channels
are specified directly. If false, all found channels are put in the `channel` section in the order from most frequent
to least frequent channel. Default is False)
- `operating_system` (Specify your operating system to handle os-specific bugs. Some bugs only appear in windows, other only in linux, some exist across all platforms)

2.) After that, useres are able to execute the following command to create their environment:

    conda env create -f environment.yml

Note: There is no need to specify `-n environment_name` in this command because the name of the environment is specified in the file itself. More information can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).

3.) Some R-packages are not (yet) available as conda-packages. In order to semi-automate the installation process of these packages in your conda environment, run `install_cran_packages.sh`. This script will activate the conda environment, start R in this environment and then install the CRAN-packages via `install.packages()` Note that this is not the recommended way to do it, but some R-packages are simply not available as conda-packages (this should be checked though on a regular basis).

## Current workarounds
In case something goes wrong with the installation of pip-packages, this repository also contains a script `install_pip_packages.sh` wich can be used to install the pip packages found in `environment.yml`. Note that in general this is not the desired way to do this.
# How to contribute
1.) Whenever you find a new package that you find interesting and/or have to install for your project, this should be added to `csp_packages.tsv`. The spreadsheet contains the following columns:

- `package_name` (the name of the package as found on conda or pip pages)
- `version` (specify the version of the package you need)
- `installation_command` (the full installation command)
- `package_manager` (pip, conda, cran)
- `conda_channel` (which conda channel to install from)
- `area` (e.g. "data wrangling", "plotting", etc.)
- `link` (the link to the package itself)
- `necessity` (required: you find that this package should be available for all lab members, optional: only you need it for your current project but maybe any future lab member might find it also useful in the future)
- `description` (a short description of what this package does)
- `comment` (optional comments if something is buggy or if you want to tell other users some useful information)
- `language` (python, R)
- `bug_flag` (can be 'linux' or 'windows')

2.) After adding the information for the new package, you can run `get_yml_from_csv.py` to create an updated version of `environment.yml`. `get_yml_from_csv.py` simply parses the information in `csp_packages.tsv` in order to not have to do this tedious work yourself.

3.) Push your changes

# Notes
## Dependencies

It's not necesary to specifiy dependencies in the `.tsv` file! Conda will take care of that. So for example, there's no need to put `numpy` in the `.tsv` file because `numpy` is a common dependency of most scientific python packages (e.g. `scikit-learn`,`pytorch`, etc.) There might however be cases where there are optional dependencies that can but must not be installed (Example: The plotting package `plotly` works completely fine if we install it as it is. But if we want the nice feature of creating interactive plots we also have to install the dependency `orca`). Optional dependencies should be marked as `dependency` in the `area` column of the `.tsv` file.

## Why not create the  environment and share the exported .yml file?
Theoretically there would be an even better option than everyone creating the same environment over and over: First, one user would create an environment using `environment.yml` (which can take a long time because conda has to resolve the dependency graph to create an environment where each of the packages is ‘happy’ with the versions of all other packages). Then this environment could be exported via `conda env export > environment.yml` . Finally, other users could then take this `.yml` file to directly create the environment (without the need to resolve the dependency graph one more time, because this file already contains the ‘solution’. More information on that can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#exporting-the-environment-yml-file)). But here comes the catch: This file often does not work across platforms (e.g. your own personal laptop which might run on Windows vs. Linux servers). The longterm solution for this is to create a containerized solution with this environment as aimed in [csp_neurodocker](https://github.com/JohannesWiesner/csp_neurodocker)
