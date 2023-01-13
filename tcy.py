# -*- coding: utf-8 -*-
"""
Parse the information csp_packges.tsv and return environment.yml file

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
import argparse

###############################################################################
## Create functions ###########################################################
###############################################################################

def write_yml_header(df,yml_path,write_conda_channels,ignore_yml_name,surname,name):
    '''Write first section of .yml file'''
    
    with open(yml_path,'w') as f:
        
        # write name attribute
        if not ignore_yml_name:
            f.write(f"name: csp_{surname}_{name}\n")

        # write channel attribute
        # if conda channels are not specified directly, all conda channels will be
        # written into the channels section. The order of appearance defines the priority.
        # Therefore, we sort the data frame according to how often a particular channel is needed.
        # The most needed channel appears first and the least needed appears last.
        # The default channel always comes last
        f.write('channels:\n')
        if write_conda_channels == False:
            conda_channel_counts = df['conda_channel'].value_counts().index.to_list()
            for channel in conda_channel_counts:
                f.write(f"- {channel}\n")        # 

        f.write('- defaults\n')

        # write dependencies attribute
        f.write('dependencies:\n')

# FIXME: See issue #24
def write_conda_package(row,yml_path,write_conda_channels):
    '''Parse a single row from the .tsv file and write the
    information found in it to the .yml file'''

    with open(yml_path,'a') as f:
        
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

# FIXME: See issue #24
def write_to_pip_requirements(row,requirements_path):
    '''Write a pip-package to the requirements.txt file'''
    
    with open(requirements_path,'a') as f:
        row = row.to_dict()
        package_name = row['package_name']
        install_command = f"{package_name}\n"
        f.write(install_command)

# FIXME: See issue #24
# this can probably be merged with write_conda_package. This would also 
# be smart so users can also define versions for pip-packages.
def write_pip_package(row_pip,yml_path):
    '''Write a pip-package directoyl to the .yml file'''
    
    with open(yml_path,'a') as f:
    
        row_pip = row_pip.to_dict()
        package_name_pip = row_pip['package_name']
        install_command = f"  - {package_name_pip}\n"
        f.write(install_command)

# FIXME: See issue #24
def write_pip_packages(df,pip_requirements_file,yml_path,requirements_path):
    '''Write pip-packages either directly to the .yml file or to 
    a separate requirements.txt file'''
    
    df = df.loc[df['package_manager'] == 'pip']
    
    # these two lines are needed in any case
    with open(yml_path,'a') as f:
        f.write('- pip\n')
        f.write('- pip:\n')

    if pip_requirements_file == True:
        with open(yml_path,'a') as f:
            f.write('  - -r requirements.txt')
        with open(requirements_path,'w') as f:
            df.apply(write_to_pip_requirements,axis=1,requirements_path=requirements_path)
    elif pip_requirements_file == False:
        df.apply(write_pip_package,axis=1,yml_path=yml_path)

# FIXME: Issue 5
def write_cran_installation_script(df,surname,name):
    '''Create a file 'install_cran_packages.sh' that activates the environment
    and installs all CRAN-packages in that environemnt'''

    df = df.loc[(df['language'] == 'R') & (df['package_manager'] == 'cran'),:]
    cran_packages = ','.join(f"\"{package}\"" for package in df['package_name'])

    with open('install_cran_packages.sh','w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'conda activate csp_{surname}_{name}\n')
        f.write('R\n')
        install_command = f'install.packages(c({cran_packages}))'
        f.write(install_command)            

# FIXME: Issue 5
def write_pip_installation_script(df,surname,name):
    
    df = df.loc[df['package_manager'] == 'pip']

    with open('install_pip_packages.sh','w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')
        f.write(f'conda activate csp_{surname}_{name}\n')
        f.write('pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \\\n')
        
        for pip_package in df['package_name']:
            f.write(f"{pip_package} \\\n")

    # delete last '\' character
    with open('install_pip_packages.sh', 'rb+') as filehandle:
        filehandle.seek(-3, os.SEEK_END)
        filehandle.truncate()

def run(surname,name,operating_system,ignore_yml_name=False,
        pip_requirements_file=True,write_conda_channels=False,
        tsv_path=None,yml_dir=None):
    '''Parses the .tsv file and creates an environment.yml file
    
    Parameters
    ----------
    surname : str
        Surname of the user.
    name : str
        Name of the user.
    operating_system : str
        Can be 'linux' or 'windows'. Depending on the input only packages
        that run bug-free under the specified OS are selected. Packages
        that are flagged with 'cross-platform' in the bug_flag column of the 
        input .tsv file are never included.
    ignore_yml_name : boolean, optional
        If True, don't set the "name:" attribute in the environment.yml file.
        This is useful if the resulting .yml file should only be used for updating 
        an existing environment (not to create a new one). The default is False.
    pip_requirements_file : boolean, optional
        If True, pip packages are written to a separate requirements.txt file. 
        If False, pip packages appear in environment.yml file under the "pip:"
        section. The default is True.
    write_conda_channels : boolean, optional
        If True, conda channels are directly specified for each package 
        (e.g. conda-forge::spyder). In this case the 'defaults' channel 
        is the only channel that appears in the 'channels:' section. See:
        https://stackoverflow.com/a/65983247/8792159 for a preview.
        If False, all found channels are put in the 'channels:' section in the 
        order from most frequently to least frequently used channel. 
        The default is False.
    tsv_path: str, optional
        Path to the packages.tsv file. If None, the function will expect 
        packages.tsv to be in the current working directory. The default is None
    yml_dir: str, optional
        Path to a valid directory where environment.yml should be placed in.
        If None, environment.yml will be placed in the current working directory.
        If a requirements.txt or pip is generated it will always be placed in 
        the same directory s the environment.yml file
        The default is None.
    
    Returns
    -------
    None.

    '''

    ###########################################################################
    ## General preparation ####################################################
    ###########################################################################
    
    # read in .tsv file
    if tsv_path:
        df = pd.read_csv(tsv_path,sep='\t',index_col=None,header=0)
    else:
        df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
    
    # create path to environment.yml file
    if yml_dir:
        if not os.path.isdir(yml_dir):
            os.makedirs(yml_dir)
        yml_path = os.path.join(yml_dir,'environment.yml')
        requirements_path = os.path.join(yml_dir,'requirements.txt')
    else:
        yml_path = './environment.yml'
        requirements_path = './requirements.txt'

    # read in the .tsv file
    # FIXME: See issue #21: After reading in the .tsv file, there should be a sanity
    # check running that makes sure no cell in the .tsv file ends with a space
    # We had an issue that user typed in "conda " instead of "conda" which could
    # not be interpreted. 
    # remove packages that generally don't work (for now) on all platforms
    df = df.loc[df['bug_flag'] != 'cross-platform']
    
    # remove pacakges that won't work for the specified operating system
    if operating_system:
        df = df.loc[df['bug_flag'] != operating_system]
    
    # sort by language, then by package manager, then by conda channel
    df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)
    
    # write .yml header
    write_yml_header(df,yml_path,write_conda_channels,ignore_yml_name,surname,name)
    
    ###########################################################################
    ## Write installation commands for conda-packages #########################
    ###########################################################################
    
    df_conda = df.loc[df['package_manager'] == 'conda']
    df_conda.apply(write_conda_package,axis=1,yml_path=yml_path,write_conda_channels=write_conda_channels)
    
    ###########################################################################
    ## Write installation commands for pip-packages ###########################
    ###########################################################################
    
    write_pip_packages(df,pip_requirements_file,yml_path=yml_path,requirements_path=requirements_path)
    
    ###########################################################################
    ## Specify optional additional bash script that can be run in case 
    ## installation of pip packages fails due to SSL-verification errors
    ###########################################################################
    
    write_pip_installation_script(df,surname,name)
    
    ###########################################################################
    ## Create bash script to install CRAN-packages ############################
    ###########################################################################
    
    write_cran_installation_script(df,surname,name)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Parse the information from packages.tsv and return environment.yml file')

    # add required arguments 
    parser.add_argument('--surname',type=str,required=True,help='Surname of user')
    parser.add_argument('--name',type=str,required=True,help='Name of user')
    parser.add_argument('--os',type=str,required=True,choices=['linux','windows'],
                        help="Can be \'linux\' or \'windows\'. Depending on the \
                        input only packages that run bug-free under the specified \
                        OS are selected. Packages that are flagged with 'cross-platform' \
                        in the bug_flag column of the input .tsv file are never included.")
    # add keyword arguments
    parser.add_argument('--ignore_yml_name',action='store_true',
                        help='Don\'t set the \"name:\" attribute in the environment.yml file.\
                        This is useful if the resulting .yml file should only be used for updating \
                        an existing environment (not to create a new one).')
    parser.add_argument('--no_pip_requirements_file',action='store_false',dest='pip_requirements_file',
                        help='Do not write pip packages to a separate requirements.txt file. \
                        Instead, pip packages appear in environment.yml file under the \"pip:\" \
                        section.')
    parser.add_argument('--write_conda_channels',action='store_true',
                        help='Specify conda channels directly for each conda package \
                        (e.g. conda-forge::spyder). In this case the \'defaults\' channel \
                        is the only channel that appears in the \'channels:\' section. See: \
                        https://stackoverflow.com/a/65983247/8792159 for a preview.')
    parser.add_argument('--tsv_path',type=str,required=False,
                        help='Optional Path to the packages.tsv file. If not given, \
                        the function will expect  packages.tsv to be in the current \
                        working directory')
    parser.add_argument('--yml_dir',type=str,required=False,
                        help='Path to a valid directory where environment.yml \
                        should be placed in. If not given, environment.yml will \
                        be placed in the current working directory. If a requirements.txt \
                        for pip is generated it will always be placed in the same directory \
                        as the environment.yml file')

    # parse arguments
    args = parser.parse_args()
    
    # parse .tsv file and get .yml file
    run(surname=args.surname,
        name=args.name,
        operating_system=args.os,
        ignore_yml_name=args.ignore_yml_name,
        write_conda_channels=args.write_conda_channels,
        pip_requirements_file=args.pip_requirements_file,
        tsv_path=args.tsv_path,
        yml_dir=args.yml_dir)