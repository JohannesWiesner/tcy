# -*- coding: utf-8 -*-
"""
Parse the information csp_packges.tsv and return environment.yml file
- When using csp_packages.gsheet, make sure to download csp_packages.gsheet 
  as .tsv file first
- Specify your surname and name
- Specify python and R versions (python 3.9 and R 4.1 are default)

Outputs:
- environemt.yml: This file can be used to create a conda environment
- install_cran_packages.sh: This bash script can be used to install CRAN-packages
inside your environment (it has to be run after creating your environment using
the environment.yml file) for which not conda-version exists (yet)
- install_pip_packages.sh: This bash script can be used to install pip packages
inside your environment (it has to be run after creating your environment using
the environment.yml file). Note: This file is only a workaround when getting
installation errors. Pip-packages are already defined in environment.yml in the 
pip-section. In case the installation works fine with environment.yml in the
future, this script is not necessary anymore.

@author: Johannes.Wiesner
"""

import pandas as pd
import os

###############################################################################
## User settings ##############################################################
###############################################################################

name = 'name'
surname = 'surname'
python_version=3.9
r_version=4.1
pip_requirements_file=True

###############################################################################
## General preparation ########################################################
###############################################################################

# download the csp_packages.gsheet as .tsv file from google drive
df = pd.read_csv('./csp_packages.tsv',sep='\t',index_col=None,header=0)

# remove packates that were flagged as buggy
df = df.loc[df['bug_flag'] != True]

# sort by language, then by package manager, then by conda channel
df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)

# write .yaml template
with open('environment.yml', 'w') as f:
    f.write(f'name: csp_{surname}_{name}\n')
    f.write('channels:\n')
    f.write('- defaults\n')
    f.write('dependencies:\n')
    
    if python_version:
        f.write(f'- python={python_version}\n')
    else:
        f.write('- python\n')

###############################################################################
## Specifiy installation commands for conda packages ##########################
###############################################################################

# only consider python packages
df_python = df.loc[df['language'] == 'python']

# specify channels directly for conda packages
df_python_conda = df_python.loc[df['package_manager'] == 'conda']

def write_conda_command(row):
    with open('environment.yml','a') as f:
        install_command = '-' + ' ' + row['conda_channel'] + '::' + row['package_name'] + '\n'
        f.write(install_command)
        
df_python_conda.apply(write_conda_command,axis=1)

###############################################################################
## Specify installation commands for conda R packages #########################
###############################################################################

df_r = df.loc[df['language'] == 'R']

# isolate the r-package itself to be able to specify version
r_language = df_r.loc[ (df['language'] == 'R') & (df['area'] == 'language')].squeeze().to_dict()
r_conda_channel = r_language['conda_channel']
r_conda_package = r_language['package_name']

with open('environment.yml','a') as f:
    if r_version:
        f.write(f'- {r_conda_channel}::{r_conda_package}={r_version}\n')
    else:
        f.write(f'- {r_conda_channel}::{r_conda_package}\n')

# parse all other conda r-packages
df_r_conda = df_r.loc[(df['package_manager'] == 'conda') & (df_r['area'] != 'language')]
df_r_conda.apply(write_conda_command,axis=1)

###############################################################################
## Create bash script to install CRAN-packages ################################
###############################################################################

with open('install_cran_packages.sh','w') as f:
    f.write('#!/bin/bash\n')
    f.write(f'conda activate {name}_{surname}\n')
    f.write('R\n')
    
df_r_cran = df_r.loc[df['package_manager'] == 'cran']
cran_package_list = ','.join(f'"{package}"' for package in df_r_cran['package_name'])

with open('install_cran_packages.sh','a') as f:
    install_command = f'install.packages(c({cran_package_list}))'
    f.write(install_command)

###############################################################################
## Specify installation commands for pip-packages #############################
###############################################################################

df_pip = df_python.loc[df['package_manager'] == 'pip']

with open('environment.yml', 'a') as f:
    f.write('- pip\n')
    f.write('- pip:\n')

def write_pip_command(row):
    with open('environment.yml','a') as f:
        install_command = '  ' + '-' + ' ' + row['package_name'] + '\n'
        f.write(install_command)

def write_to_pip_requirements(row):
    with open('requirements.txt','a') as f:
        install_command = row['package_name'] + '\n'
        f.write(install_command)

if pip_requirements_file:
    with open('environment.yml','a') as f:
        install_command = '  ' + '-' + ' ' + '-r' + ' ' + 'requirements.txt'
        f.write(install_command)
    df_pip.apply(write_to_pip_requirements,axis=1)
else:
    df_pip.apply(write_pip_command,axis=1)

###############################################################################
## Specify optional additional bash script that can be run in case 
## installation of pip packages fails due to SSL-verification errors
## https://stackoverflow.com/questions/25981703/pip-install-fails-with-connection-error-ssl-certificate-verify-failed-certi
###############################################################################

with open('install_pip_packages.sh','w') as f:
    f.write('#!/bin/bash\n')
    f.write('set -e\n')
    f.write(f'conda activate csp_{name}_{surname}\n')
    f.write('pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \\\n')

def write_pip_package(row):
    with open('install_pip_packages.sh','a') as f:
        f.write(row['package_name'] + ' \\\n')
        
df_pip.apply(write_pip_package,axis=1)

# delete last '\' character
with open('install_pip_packages.sh', 'rb+') as filehandle:
    filehandle.seek(-4, os.SEEK_END)
    filehandle.truncate()

