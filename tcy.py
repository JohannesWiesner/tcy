# -*- coding: utf-8 -*-
"""
Parse the information from packages.tsv and return an environment.yml file
and an optional requirements.txt file

Notes:
    
- environment.yml: This file can be used to create a conda environment
- requirements.txt: This file can be used to install pip packages
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


def run(operating_system,yml_name=None,pip_requirements_file=False,
        write_conda_channels=False,tsv_path='./packages.tsv',yml_dir=None):
    '''Parses the .tsv file and creates an environment.yml file
    
    Parameters
    ----------
    operating_system : str
        Can be 'linux' or 'windows'. Depending on the input only packages
        that run bug-free under the specified OS are selected. Packages
        that are flagged with 'cross-platform' in the bug_flag column of the 
        input .tsv file are never included.
    yml_name : str, optional
        If not given, don't set the "name:" attribute in the environment.yml file.
        This is useful if the resulting .yml file should only be used for updating 
        an existing environment (not to create a new one). The default is False.
    pip_requirements_file : boolean, optional
        If True, pip packages are written to a separate requirements.txt file. 
        If False, pip packages appear in environment.yml file under the "pip:"
        section. The default is False.
    write_conda_channels : boolean, optional
        If True, conda channels are directly specified for each package 
        (e.g. conda-forge::spyder). In this case the 'defaults' channel 
        is the only channel that appears in the 'channels:' section. See:
        https://stackoverflow.com/a/65983247/8792159 for a preview.
        If False, all found channels are put in the 'channels:' section in the 
        order from most frequently to least frequently used channel. 
    tsv_path: str, optional
        Path to a valid packages.tsv file. If not otherwise specified, 
        the function will expect packages.tsv to be in the current working directory. 
        The default is \'./packages.tsv\'.
    yml_dir: str, optional
        Path to a valid directory where environment.yml should be placed in.
        If None, environment.yml will be placed in the current working directory.
        If a requirements.txt or pip is generated it will always be placed in 
        the same directory as the environment.yml file
        The default is None.
    
    Returns
    -------
    None.

    '''

    # get path to .yml file
    if yml_dir:
        yml_path = os.path.join(yml_dir,'environment.yml')
        requirements_path = os.path.join(yml_dir,'requirements.txt')
    else:
        yml_path = './environment.yml'
        requirements_path = './requirements.txt'
        
    # read in .tsv file
    # FIXME: See issue #21: After reading in the .tsv file, there should be a sanity
    # check running that makes sure no cell in the .tsv file ends with a space
    # We had an issue that user typed in "conda " instead of "conda" which could
    # not be interpreted. 
    # remove packages that generally don't work (for now) on all platforms
    df = pd.read_csv(tsv_path,sep='\t',index_col=None,header=0)
    
    # remove packages that won't work for the specified operating system
    df = df.loc[df['bug_flag'] != operating_system]
    
    # sort by language, then by package manager, then by conda channel
    df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)
    
    # get all conda channels, sort by frequency and if there are ties, alphabetically
    conda_channels = df['conda_channel'].value_counts().sort_index(ascending=False).sort_values(ascending=False).index
        
    # write yml-header
    with open(yml_path,'w') as f:
    
        if yml_name:
            f.write(f"name: {yml_name}\n")
        
        f.write('channels:\n')
        
        if write_conda_channels == False:
            for channel in conda_channels:
                f.write(f"- {channel}\n")   
        
        f.write('- defaults\n')
        f.write('dependencies:\n')
    
    # write conda packages
    with open(yml_path,'a') as f:
        
        df_conda = df.loc[df['package_manager'] == 'conda']
        
        for idx,row in df_conda.iterrows():
            
            row = row.to_dict()
            package_name = row['package_name']
            version = row['version']
            conda_channel = row['conda_channel']
            
            command = f"{package_name}"
            
            if write_conda_channels:
                command = f"{conda_channel}::{command}"
            if not pd.isna(version):
                command = f"{command}{version}"
            command = f"- {command}\n"
           
            f.write(command)
    
    # write pip packages
    with open(yml_path,'a') as f:
        
        df_pip = df.loc[df['package_manager'] == 'pip']
        
        # these two lines are needed in any case
        f.write('- pip\n')
        f.write('- pip:\n')
    
        if pip_requirements_file == False:
                    
            for idx,row in df_pip.iterrows():
                row = row.to_dict()
                package_name = row['package_name']
                command = f"{package_name}"
                command = f"  - {command}\n"
                f.write(command)
                
        if pip_requirements_file == True:
            
            f.write('  - -r requirements.txt')
        
            with open(requirements_path,'w') as rf:
                for idx,row in df_pip.iterrows():
                    row = row.to_dict()
                    package_name = row['package_name']
                    command = f"{package_name}\n"
                    rf.write(command)
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Parse the information from packages.tsv and return environment.yml file')

    # add positional arguments
    parser.add_argument('os',type=str,choices=['linux','windows'],
                        help="Operating system under which the environment.yml file \
                        will be used to create a conda environment. Can be \'linux\' \
                        or \'windows\'. Depending on the input only packages that run \
                        bug-free under the specified OS are selected. Packages that are \
                        flagged with 'cross-platform' in the bug_flag column of the \
                        input .tsv file are never included.")
    # add keyword arguments
    parser.add_argument('--yml_name',type=str,required=False,
                        help='Sets the \"name:\" attribute of the .yml file. If not given \
                        The .yml file will not have a \"name:\" attribute.\
                        This is useful if the resulting .yml file should only be used for updating \
                        an existing environment that already has a name (i.e. not to create a new one).')
    parser.add_argument('--pip_requirements_file',action='store_true',dest='pip_requirements_file',
                        help='Write pip packages to a separate requirements.txt file.')
    parser.add_argument('--write_conda_channels',action='store_true',
                        help='Specify conda channels directly for each conda package \
                        (e.g. conda-forge::spyder). In this case the \'defaults\' channel \
                        is the only channel that appears in the \'channels:\' section. See: \
                        https://stackoverflow.com/a/65983247/8792159 for a preview.')
    parser.add_argument('--tsv_path',type=str,required=False,default='./packages.tsv',
                        help='Optional Path to the input packages.tsv file. \
                        If not otherwise specified, the function will expect packages.tsv \
                        to be in the current working directory.')
    parser.add_argument('--yml_dir',type=str,required=False,
                        help='Path to a valid directory where environment.yml \
                        should be placed in. If not given, environment.yml will \
                        be placed in the current working directory. If a requirements.txt \
                        for pip is generated it will always be placed in the same directory \
                        as the environment.yml file')

    # parse arguments
    args = parser.parse_args()
    
    # parse .tsv file and get .yml file
    run(operating_system=args.os,
        yml_name=args.yml_name,
        write_conda_channels=args.write_conda_channels,
        pip_requirements_file=args.pip_requirements_file,
        tsv_path=args.tsv_path,
        yml_dir=args.yml_dir)