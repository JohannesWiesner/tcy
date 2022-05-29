
# Description
This repository contains a spreadsheet `csp_packages.tsv` that gives information about `conda` and `pip` packages that are used by the CSP lab. It also contains a `environment.yml` file that is supposed to contain the same information as `csp_packages.tsv` in order to create a conda environment that contains all the packages found in the spreadsheet.
# Aims
New lab members can download this repository and use `environment.yml` to create a conda environment that contains all the packages that the CSP lab needs. `environment.yml`  contains all the packages that can be found in the  spreadsheets (with a few exceptions packages that are bug flagged but may be available in the future when the developers of these packages fixed the bugs). This will allow users to get a computational environment with `R`,  `python` and all the packages they need to perform their analyses. 
# How to use 
1.) After  installing Miniconda on their machines, users specify their name and surname in `environment.yml` and then should be able to execute the following command to create their environment:

    conda env create -f environment.yml  

Note: There is no need to specify `-n environment_name` in the command above when the name of the environment is specified in the file itself. More information can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).

2.) Some R-packages are not (yet) available as conda-packages. In order to semi-automate the installation process of these packages in your conda environment, run `install_cran_packages.sh`. This script will activate the conda environment, start R in this environment and then install the CRAN-packages via `install.packages()`

## Current workarounds
In case something goes wrong with the installation of pip-packages, this repository also contains a script `install_pip_packages.sh` wich can be used to install the pip packages found in `environment.yml`. Note that in general this is not the desired way to do this. 
# How to contribute
1.) Whenever you find a new package that you find interesting and/or have to install for your project, this should be added to `csp_packages.tsv`. The spreadsheet contains the following columns:

- package_name (the name of the package as found on conda or pip pages)
- installation_command (the full installation command)
- package_manager (pip, conda, cran)
- conda_channel (which conda channel to install from)
- area (e.g. data wrangling, plotting, etc.)
- link (the link to the package itself)
- necessity (required: you find that this package should be available for all lab members, optional: only you need it for your current project but maybe any future lab member might find it also useful in the future)
- description (a short description of what this package does)
- comment (optional comments if something is buggy)
- language (python, R)
- bug_flag (Set to `True` if this package causes trouble at the moment)

2.) After adding the information for the new package, you can run `get_yml_from_csv.py` to create an updated version of `environment.yml`. `get_yml_from_csv.py` simply parses the information in `csp_packages.tsv` in order to not have to do this tedious work yourself.  

3.) Push your changes 

# Notes
Theoretically there would be an even better option than this solution: First, one would create an environment using `environment.yml` (which can take a long time because conda has to resolve the dependency graph to create an environment where each of the packages is ‘happy’ with the versions of all other packages). Then this environment could be exported via [conda env export > environment.yml](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#exporting-the-environment-yml-file).  Finally, other users could take this `.yml` file to directly create the environment (without the need to resolve the dependency graph one more time, because this file already contains the ‘solution’). But here comes the problem: This file often does not work across platforms (e.g. your own personal laptop (which runs probably on Windows) vs. Linux servers). The longterm solution for this is to create a containerized solution with this environment as aimed in https://github.com/JohannesWiesner/csp_neurodocker.
<!--stackedit_data:
eyJoaXN0b3J5IjpbMTE5MTg2MzIzMiwtMTE1NjQzNTA4NywxMj
A4ODM4MDM0LDczMDk5ODExNl19
-->