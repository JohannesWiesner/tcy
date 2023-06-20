
# TCY
**T**svto**C**onda**Y**ml. A package for easy creation of conda `.yml` files using a `.tsv` file as input.
## Aims
Using `.yml` files as recipes to create conda environments is already a good step towards reproducible scientific computing environments. However, sometimes we want to know **why** a particular package was included (or not), **what** it does (improving transparency), and whether it runs without errors on all common operating systems (Linux, Mac OS, Windows). Spreadsheet files offer much more possibilities to document this. The goal of this repository is to have the documentation capabilities of a `.tsv` file and then be able to export the packages that are described in it to a `.yml` file.
## The packages.tsv file
The input spreadsheet file has the following columns:
- `package_name` (the offical name of the package)
- `version` (specify the version of the package you need, this can include )
- `installation_command` (the full installation command)
- `package_manager` (pip, conda, cran)
- `conda_channel` (which conda channel to install from)
- `area` (e.g. "data wrangling", "plotting", etc.)
- `link` (the link to the package itself)
- `necessity` ("required": you find that this package should be available for all lab members, "optional": only you need it for your current project but maybe any future lab member might find it also useful in the future)
- `description` (a short description of what this package does)
- `comment` (optional comments if something is buggy or if you want to tell other users some useful information)
- `language` (Python, R, Julia)
- `bug_flag` (can be 'linux','windows' or 'cross_platform')
## How to generate a custom environment.yml file
With a python installation on their machines, users can run the  `tcy.py` script in the console:

 `python tcy.py linux`

The following positional arguments have to be specified:

- `{linux,windows}` (Operating system under which the `.yml` file will be used to create a conda environment. Can be 'linux' or 'windows'. Depending on the input only packages that run bug-free under the specified OS are  selected. Packages that are flagged with `cross-platform` in the `bug_flag` column of the input `.tsv` file are never included.

The following optional arguments can be set for further customization:
- `--yml_name` (Sets the \"name:\" attribute of the .yml file. If not given, the .yml file will not have a \"name:\" attribute. This is useful if the file should only be used for updating an existing environment that already has a name, i.e. not to create a new one)
- `--yml_file_name` (Sets the name of the .yml file. The default is 'environment.yml')
- `--pip_requirements_file` (Write pip packages to a separate `requirements.txt` file. This will file will always be placed in the same directory as the .yml file)
- `--write_conda_channels` (Specifies conda channels directly for each conda package (e.g. conda-forge::spyder). In this case the \'defaults\' channel is the only channel that appears in the \'channels:\' section. See: [this link](https://stackoverflow.com/a/65983247/8792159) for a preview)
- `--tsv_path` (Optional path to the `.tsv` file. If not given, the function will expect a  `"packages.tsv"` file to be in the current working directory)
- `--yml_dir`(Path to a valid directory where the .yml file should be placed in. If not given the file will  be placed in the current working directory. If a `requirements.txt` for pip is generated it will always be placed in the same directory  as the .yml file)
- `--cran_installation_script` (If set, generates a bash script `install_cran_packages.sh`that allows to install CRAN-packages within the conda-environment. Only valid when `--yml_name` is set)
- `--cran_mirror`(A valid URL to a CRAN-Mirror where packages should be downloaded from. The default is https://cloud.r-project.org)
- `--languages` (Filter for certain languages. Valid inputs are 'Python', 'R' & 'Julia')
- `--necessity` (Filter for necessity. Valid inputs are 'optional' and 'required').

### CRAN-packages
Some R-packages are not (yet) available as conda-packages. In order to semi-automate the installation process of these packages in your conda environment, run `install_cran_packages.sh`. This script will activate the conda environment, start R in this environment and then install the CRAN-packages via `install.packages()` Note that this is not the recommended way to do it, but some R-packages are simply not available as conda-packages (this should be checked though on a regular basis).

## Notes for CSP lab members
This repository contains a subfolder called `environments` . New lab members can download this repository and use the file  `csp_Linux_solved.yml` within that folder to create a conda environment. This file contains a solved solution of the package specifications found in `csp_Linux_input.yml` derived from a GitHub-Action Workflow. The file contains all the packages that can be found in `csp.tsv` and that run bug-free under Linux (with a few exceptions of packages that are bug flagged but may be available in the future when the developers of these packages have fixed the bugs). This will allow users to get a computational environment with `R`,  `python` and all the packages they need to perform their analyses.

 1. After downloading this repo users have to set their name
    `name:csp_surname_name` attribute in the `.yml` file.
 2. After that they execute the following command to create their
    environment: `conda env create -f environment.yml` (Note: There is no need to specify `-n environment_name` in this command because the name of the environment is alredy specified in the file itself. More information can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file))

Whenever you find a new package that you find interesting and/or have to install for your project, you can open an issue in this repository or even better, fork this repo, add your package to the `csp.tsv` file and send a pull request!

# Q & A
## What about dependencies?

It's not necesary to specifiy dependencies in the `.tsv` file! Conda will take care of that. So for example, there's no need to put `numpy` in the `.tsv` file because `numpy` is a common dependency of most scientific python packages (e.g. `scikit-learn`,`pytorch`, etc.) There might however be cases where there are optional dependencies that can but do not have to be installed (Example: The plotting package `plotly` works completely fine if we install it as it is. But if we want the nice feature of creating interactive plots we also have to install the dependency `orca`). Optional dependencies should be marked as `dependency` in the `area` column of the `.tsv` file.

## Why not create the  environment and share the exported .yml file?
Theoretically there would be an even better option than everyone creating the same environment over and over: First, one user would create an environment using `environment.yml` (which can take a long time because conda has to resolve the dependency graph to create an environment where each of the packages is ‘happy’ with the versions of all other packages). Then this environment could be exported via `conda env export > environment.yml` . Finally, other users could then take this `.yml` file to directly create the environment (without the need to resolve the dependency graph one more time, because this file already contains the ‘solution’. More information on that can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#exporting-the-environment-yml-file)). But here comes the catch: This file often does not work across platforms (e.g. your own personal laptop which might run on Windows vs. Linux servers). The longterm solution for
this is to create a containerized solution with this environment as aimed in [csp_docker](https://github.com/JohannesWiesner/csp_neurodocker)
