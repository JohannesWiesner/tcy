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
  installation errors (as described here: 
  https://stackoverflow.com/questions/25981703/pip-install-fails-with-connection-error-ssl-certificate-verify-failed-certiPip-packages are already defined in environment.yml in the 
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
# Should pip packages be written to a requirements.txt or should they directly 
# appear in the .yml file itself? Default is True.
pip_requirements_file = True
# Should the conda channels be directly specified for each package (e.g. conda-forge::spyder)
# If true, only the 'default' channel appears in the 'channels:' section and all other channels
# are specified directly (https://anaconda.org/conda-forge/pythonsee: https://stackoverflow.com/a/65983247/8792159). If false,
# all found channels are put in the 'channel:' section in the order from most frequent
# to least frequent. Default is False
write_conda_channels = False
# Specify your operating system (some bugs only appear in windows, other only
# in linux, some exist across all platform)
operating_system = 'linux' # Specify your operating system (can be 'linux' or 'windows' or None)

###############################################################################
## Create functions ###########################################################
###############################################################################

def write_yml_header(df,write_conda_channels):
    '''Write first section of .yml file'''
    
    with open('environment.yml','w') as f:
        
        f.write(f"name: csp_{surname}_{name}\n")
        f.write('channels:\n')
        
        # if conda channels are not specified directly, all conda channels will be
        # written into the channels section. The order of appearance defines the priority.
        # Therefore, we sort the data frame according to how often a particular channel is needed. 
        # The most needed channel appears first and the least needed appears last.
        if write_conda_channels == False:
            conda_channel_counts = df['conda_channel'].value_counts().index.to_list()
            for channel in conda_channel_counts:
                f.write(f"- {channel}\n")
                
        f.write('- defaults\n')
        f.write('dependencies:\n')

def write_conda_package(row,write_conda_channels):

    with open('environment.yml','a') as f:
        
        # extract all necessary information from row
        row = row.to_dict()
        package_name = row['package_name']
        version = row['version']
        conda_channel = row['conda_channel']
        
        # write command to .yml file
        install_command = "- "

        if write_conda_channels == True:
            install_command += f"{conda_channel}::{package_name}"
        elif write_conda_channels == False:
            install_command += f"{package_name}"
        
        if not pd.isna(version):
            install_command += f"={version}"
        
        install_command += "\n"
        
        f.write(install_command)

# this can probably be merged with write_conda_package. This would also 
# be smart so users can also define versions for pip-packages.
def write_pip_package(row_pip):
    '''Write a pip-package directoyl to the .yml file'''
    
    with open('environment.yml','a') as f:
    
        row_pip = row_pip.to_dict()
        package_name_pip = row_pip['package_name']
        install_command = f"  - {package_name_pip}\n"
        f.write(install_command)

def write_to_pip_requirements(row):
    '''Write a pip-package to the requirements.txt file'''
    
    with open('requirements.txt','a') as f:
        row = row.to_dict()
        package_name = row['package_name']
        install_command = f"{package_name}\n"
        f.write(install_command)

def write_pip_packages(df,pip_requirements_file):
    '''Write pip-packages either directly to the .yml file or to 
    a separate requirements.txt file'''
    
    df = df.loc[df['package_manager'] == 'pip']
    
    # these two lines are needed in any case
    with open('environment.yml','a') as f:
        f.write('- pip\n')
        f.write('- pip:\n')

    if pip_requirements_file == True:
        with open('environment.yml','a') as f:
            f.write('  - -r requirements.txt')
        with open('requirements.txt','w') as f:
            df.apply(write_to_pip_requirements,axis=1)
    elif pip_requirements_file == False:
        df.apply(write_pip_package,axis=1)

# FIXME: Issue 5
def write_cran_installation_script(df):
    '''Create a file 'install_cran_packages.sh' that activates the environment
    and installs all CRAN-packages in that environemnt'''

    df = df.loc[(df['language'] == 'R') & (df['package_manager'] == 'cran'),:]
    cran_packages = ','.join(f"\"{package}\"" for package in df['package_name'])

    with open('install_cran_packages.sh','w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'conda activate {name}_{surname}\n')
        f.write('R\n')
        install_command = f'install.packages(c({cran_packages}))'
        f.write(install_command)            

# FIXME: Issue 5
def write_pip_installation_script(df):
    
    df = df.loc[df['package_manager'] == 'pip']

    with open('install_pip_packages.sh','w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')
        f.write(f'conda activate csp_{name}_{surname}\n')
        f.write('pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \\\n')
        
        for pip_package in df['package_name']:
            f.write(f"{pip_package} \\\n")

    # delete last '\' character
    with open('install_pip_packages.sh', 'rb+') as filehandle:
        filehandle.seek(-3, os.SEEK_END)
        filehandle.truncate()

###############################################################################
## General preparation ########################################################
###############################################################################

# read in the .tsv file
df = pd.read_csv('./csp_packages.tsv',sep='\t',index_col=None,header=0)

# remove packages that generally don't work (for now) on all platforms
df = df.loc[df['bug_flag'] != 'cross-platform']

# remove pacakges that won't work for the specified operating system
if operating_system:
    df = df.loc[df['bug_flag'] != operating_system]

# sort by language, then by package manager, then by conda channel
df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)

# write .yml header
write_yml_header(df,write_conda_channels)

###############################################################################
## Write installation commands for conda-packages #############################
###############################################################################

df_conda = df.loc[df['package_manager'] == 'conda']
df_conda.apply(write_conda_package,axis=1,write_conda_channels=write_conda_channels)

###############################################################################
## Write installation commands for pip-packages ###############################
###############################################################################

write_pip_packages(df,pip_requirements_file)

###############################################################################
## Specify optional additional bash script that can be run in case 
## installation of pip packages fails due to SSL-verification errors
###############################################################################

write_pip_installation_script(df)

###############################################################################
## Create bash script to install CRAN-packages ################################
###############################################################################

write_cran_installation_script(df)