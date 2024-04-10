# TCY
**T**svto**C**onda**Y**ml. A package for easy creation of conda `.yml` files using a `.tsv` file as input.

## Aims
Using `.yml` files as recipes to create conda environments is already a good step towards reproducible scientific computing environments. However, sometimes we want to know **why** a particular package was included (or not), **what** it does (improving transparency), and whether it runs without errors on all common operating systems (Linux, Mac OS, Windows). Spreadsheet files offer much more possibilities to document this. The goal of this repository is to have the documentation capabilities of a `.tsv` file and then be able to export the packages that are described in it to a `.yml` file.

## Use this repository for your own work

The most easy way to use tcy is to create your own repository by using this repository as a template. This has two advantages over using tcy locally on your machine:

1. Your "recipes" will be stored in a Github repository and are therefore available from any machine as long as you have an internet connection.
2. Creating environments can take a lot of time, depending on the number of packages that need to be included. Using the following approach, the computionally heavy solving process is outsourced to a Github-Runner so your personal machine can be used for other things.

If you want to use this approach, then follow these steps:

1. Create your own repository by clicking on the `Use this template` button in the upper right.

2. Make sure to allow Github Runners to push changes to your repository by going to Settings → Actions → General → Workflow permissions → Checkmark "Read and write permissions"

3. Clone your repository to your local machine

4. Make local changes to `environments/packages.tsv`

5. Push your changes. This will start a Github-Action-Worfklow (that uses tcy and micromamba) to create `.yml` files with solved package specification solutions. The workflow will automatically push the files to your repo, so wait until it's finished.

6. After the workflow has finished, pull the latest changes to your local repository.

7. Create your conda environment using either the `ubuntu-latest_solved.yml` or `windows-latest_solved.yml` file (depending on your OS) by doing this:

   * Set the name of the environment by overwriting the `name: ` attribute in the `.yml` file.
   * After that execute the following command to create your environment: `conda env create -f ubuntu_latest_solved.yml` (or `conda env create -f windows_latest_solved.yml`)
   (Note: There is no need to specify `-n environment_name` in this command because the name of the environment was already specified in the first step. More information can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file))

## For developers
### How to generate a custom .yml file using tcy

tcy can be pip-installed using `pip install tcy`. There are two ways to use tcy:

1. You can import the `run` function in your own code-base using `from tcy import run`.
2. tcy can also be used as a command-line application by simply running `tcy` in the terminal.

The following **positional arguments** have to be specified in both cases:

- `{linux,windows}` (Operating system under which the `.yml` file will be used to create a conda environment. Can be 'linux' or 'windows'. Depending on the input only packages that run bug-free under the specified OS are selected. Packages that are flagged with `cross-platform` in the `bug_flag` column of the input `.tsv` file are never included.

The following **optional arguments** can be set for further customization:

- `--yml_name` (Sets the \"name:\" attribute of the .yml file. If not given, the .yml file will not have a \"name:\" attribute. This is useful if the file should only be used for updating an existing environment that already has a name, i.e. not to create a new one)
- `--yml_file_name` (Sets the name of the .yml file. The default is 'environment.yml')
- `--pip_requirements_file` (Write pip packages to a separate `requirements.txt` file. This will file will always be placed in the same directory as the .yml file)
- `--write_conda_channels` (Specifies conda channels directly for each conda package (e.g. conda-forge::spyder). In this case the \'defaults\' channel is the only channel that appears in the \'channels:\' section. See: [this link](https://stackoverflow.com/a/65983247/8792159) for a preview)
- `--tsv_path` (Optional path to the `.tsv` file. If not given, the function will expect a  `"packages.tsv"` file to be in the current working directory)
- `--yml_dir`(Path to a valid directory where the .yml file should be placed in. If not given the file will  be placed in the current working directory. If a `requirements.txt` for pip is generated it will always be placed in the same directory  as the .yml file)
- `--cran_installation_script` (If set, generates a bash script `install_cran_packages.sh`that allows to install CRAN-packages within the conda-environment. Only valid when `--yml_name` is set)
- `--cran_mirror`(A valid URL to a CRAN-Mirror where packages should be downloaded from. The default is https://cloud.r-project.org)
- `--languages` (Filter for certain languages. Valid inputs are 'python', 'r', 'julia' or 'all'. The default is 'all')
- `--necessity` (Filter for necessity. Valid inputs are 'optional' and 'required').

### The packages.tsv file
The input spreadsheet file needs to have the following columns:
- `package_name` (the offical name of the package)
- `version` (specify the version of the package you need by following the [package match specification syntax](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications))
- `package_manager` (can be 'pip', 'conda', or 'cran')
- `conda_channel` (which conda channel to install from)
- `necessity` (can be 'required', 'optional')
- `language` (python, r, julia)
- `bug_flag` (can be 'linux','windows' or 'cross_platform')

### Automatic testing of the datasets.tsv file

This repository includes a testing pipeline that checks for the integrity of / valid entries in the `packages.tsv`. Which tests are running is decided using the `test_configs.json` file. Each tests corresponds to a key within the `json` file. If the corresponding value is `null` the test is not being executed. Here's an explanation of each test and rules for how the values should be provided in case the test should be executed.

| key                 | value                                                              | description                                                                                            |
|---------------------|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| valid_columns       | list of column names                                               | tsv file must only have these columns in that specific order                                           |
| filled_out_columns  | list of column names                                               | cells in these columns must not contain NaNs, i.e. every row within these columns must contain a value |
| valid_options       | dict with column names as keys and list of valid options as values | cells in these columns must only contain these values                                                  |
| column_dependencies | dict with column names as keys and list of other columns as values | if a cell in this column is filled out, cells in this/these other column(s) also have to be filled out |
| multi_option_columns| dict with column names as keys and list of valid options as values | cells in these columns must only contain valid options separated by commas                             |

### CRAN-packages
**EDIT: Still in development!**
Some R-packages are not (yet) available as conda-packages. In order to semi-automate the installation process of these packages in your conda environment, run `install_cran_packages.sh`. This script will activate the conda environment, start R in this environment and then install the CRAN-packages via `install.packages()` Note that this is not the recommended way to do it, but some R-packages are simply not available as conda-packages (this should be checked though on a regular basis).

## Q & A

### What about dependencies?

It's not necesary to specifiy dependencies in the `.tsv` file! Conda will take care of that. So for example, there's no need to put `numpy` in the `.tsv` file because `numpy` is a common dependency of most scientific python packages (e.g. `scikit-learn`,`pytorch`, etc.) There might however be cases where there are optional dependencies that can but do not have to be installed (Example: The plotting package `plotly` works completely fine if we install it as it is. But if we want the nice feature of creating interactive plots we also have to install the dependency `orca`). Optional dependencies should be marked as `dependency` in the `area` column of the `.tsv` file.

### Why not create the  environment and share the exported .yml file?
Theoretically there would be an even better option than everyone creating the same environment over and over: The environment should be only created once (which can take a long time because conda has to resolve a dependency graph where each of the packages is *‘happy’* with the versions of all other packages). Then this environment could be exported via `conda env export > environment.yml` . Finally, other users could then take this `.yml` file to create the environment without the need to resolve the dependency graph one more time, because this file already contains the ‘solution’. More information on that can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#exporting-the-environment-yml-file).

**But here comes the catch**: This file will probably not work across operating systems and their versions (e.g. your own personal laptop which might run on Windows vs. your server which runs on Linux). The reason for that is, that complex dependency graphs contain packages that are only available for a specific OS/OS-version.

The longterm solution for this problem is to create a containerized solution that includes a conda environment as aimed in [csp_docker](https://github.com/JohannesWiesner/csp_neurodocker)
