# -*- coding: utf-8 -*-
"""
Parse the information csp_packges.tsv and return environment.yml file

What you need to do:

- Specify your surname and name
- Specify python and R versions (python 3.9 and R 4.1 are default)
- Specify if pip-packages should be written directly in the .yml file or
  separately in a requirements.txt (which is the default)
- Specify if conda-packages should be defined with their channel (e.g.
  conda-forge::package_name instead of only the package name).

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

name = 'johannes_2'
surname = 'wiesner'
python_version=3.9
r_version=4.1
pip_requirements_file=True # Should pip packages be written to a requirements.txt?
write_conda_channels=False # Should the conda channels be directly specified for each package?

###############################################################################
## Create functions ###########################################################
###############################################################################

def write_python(python_version=None):
    '''Write the Python language to the .yml file. Optionally, define version'''
    
    with open('environment.yml', 'a') as f:
        if python_version:
            f.write(f'- python={python_version}\n')
        else:
            f.write('- python\n')

# NOTE: One could possibly save code by using this code as template. 
# A package can be specified with an optional channel and and optional
# version. One could probably write a function like write_command or 
# something that takes in a dictionary and then writes the install command.
def write_R(df,r_version=None,write_conda_channels=False):
    '''Write R-language to the .yml file. For that, get the information  on
    the r-package itself and optionally specify version'''
        
    with open('environment.yml','a') as f:
        
        # get conda-channel and R package name
        row = df.loc[(df['language'] == 'R') & (df['area'] == 'language')].squeeze().to_dict()
        conda_channel = row['conda_channel']
        conda_package = row['package_name']
        
        install_command = "- "
        
        if write_conda_channels == True:
            install_command += f"{conda_channel}::"
            
        install_command += f"{conda_package}"
        
        if r_version:
            install_command += f"={r_version}"
        
        install_command += "\n"
        
        f.write(install_command)
        
def write_conda_package(row,write_conda_channels):
    '''Write a conda package to the .csv file'''
    
    with open('environment.yml','a') as f:
        row = row.to_dict()
        conda_channel = row['conda_channel']
        package_name = row['package_name']
        
        if write_conda_channels == True:
            install_command = f"- {conda_channel}::{package_name}\n"
        elif write_conda_channels == False:
            install_command = f"- {package_name}\n"
                        
        f.write(install_command)

def write_pip_package(row):
    '''Write a pip-package directly to the .yml file'''
    
    with open('environment.yml','a') as f:
        row = row.to_dict()
        package_name = row['package_name']
        install_command = f"  - {package_name}\n"
        f.write(install_command)

def write_to_pip_requirements(row):
    '''Write a pip-package to the requirements.txt file'''
    
    with open('requirements.txt','a') as f:
        row = row.to_dict()
        package_name = row['package_name']
        install_command = f"{package_name}\n"
        f.write(install_command)
            
###############################################################################
## General preparation ########################################################
###############################################################################

# read in the .tsv file
df = pd.read_csv('./csp_packages.tsv',sep='\t',index_col=None,header=0)

# remove packates that were flagged as buggy by repository owner
df = df.loc[df['bug_flag'] != True]

# sort by language, then by package manager, then by conda channel
df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)

# start to write .yml file
with open('environment.yml','w') as f:
    f.write(f"name: csp_{surname}_{name}\n")
    
    # if conda-channels should not be directly specified, write channels 
    # in the upper part where the order of appearance is related to how
    # often this package is needed
    f.write('channels:\n')
    if write_conda_channels == False:
        conda_channel_counts = df['conda_channel'].value_counts().index.to_list()
        for channel in conda_channel_counts:
            f.write(f"- {channel}\n")
            
    f.write('- defaults\n')
    
    f.write('dependencies:\n')

###############################################################################
## Specifiy installation commands for python conda packages ###################
###############################################################################

# only consider python packages
df_python = df.loc[df['language'] == 'python']

# write python
write_python(python_version)

# write python conda packages to .yml file
df_python_conda = df_python.loc[df['package_manager'] == 'conda']
df_python_conda.apply(write_conda_package,axis=1,write_conda_channels=write_conda_channels)

###############################################################################
## Specify installation commands for R conda packages #########################
###############################################################################

# only consider R pacakges
df_r = df.loc[df['language'] == 'R']

# write R 
write_R(df_r,r_version=r_version,write_conda_channels=write_conda_channels)

# write R conda packages to .yml file
df_r_conda = df_r.loc[(df['package_manager'] == 'conda') & (df_r['area'] != 'language')]
df_r_conda.apply(write_conda_package,axis=1,write_conda_channels=write_conda_channels)

###############################################################################
## Create bash script to install CRAN-packages ################################
###############################################################################

# FIXME: Issue 5
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

with open('environment.yml','a') as f:
    f.write('- pip\n')
    f.write('- pip:\n')

if pip_requirements_file:
    with open('environment.yml','a') as f:
        install_command = '  ' + '-' + ' ' + '-r' + ' ' + 'requirements.txt'
        f.write(install_command)
        
        with open('requirements.txt','w') as f:
            df_pip.apply(write_to_pip_requirements,axis=1)
else:
    df_pip.apply(write_pip_package,axis=1)

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