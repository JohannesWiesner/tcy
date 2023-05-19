# -*- coding: utf-8 -*-
"""
Parse the information from packages.tsv and return an environment.yml file
and an optional requirements.txt file

Notes:
    
- environment.yml: This file can be used to create a conda environment
- requirements.txt: This file can be used to install pip packages
- install_cran_packages.sh: This bash script can be used to install CRAN-packages
  inside a conda environment (it has to be run after creating  a conda environment 
  using the environment.yml file)

@author: Johannes.Wiesner
"""

import pandas as pd
import os
import argparse
import pytest

def run(operating_system,yml_name=None,yml_file_name='environment.yml',pip_requirements_file=False,
        write_conda_channels=False,tsv_path='./packages.tsv',yml_dir=None,
        cran_installation_script=False,cran_mirror='https://cloud.r-project.org',
        languages='all',necessity='all'):
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
    yml_file_name: str, optional
        Sets a custom name for the .yml file.
        The default is 'environment.yml'
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
    cran_installation_script: boolean, optional
        If True, generates a bash script that allows to install CRAN-packages
        within the conda-environment. Only valid when yml_name is set.
        The default is False.
    cran_mirror: str, optional
        A valid URL to a CRAN-Mirror where packages should be downloaded from.
        The default is 'https://cloud.r-project.org'
    languages: str or list of str, optional
        Filter for languages. Valid arguments are Python, Julia, R.
        The default is 'all'
    necessity: str or list of str, optional
        Filter for necessity. Valid arguments are optional, required.
        The default is 'all'
        
    
    Returns
    -------
    None.

    '''

    # get path to .yml file
    if yml_dir:
        yml_path = os.path.join(yml_dir,yml_file_name)
        requirements_path = os.path.join(yml_dir,'requirements.txt')
        cran_installation_script_path = os.path.join(yml_dir,'install_cran_packages.sh')
    else:
        yml_path = yml_file_name
        requirements_path = 'requirements.txt'
        cran_installation_script_path = 'install_cran_packages.sh'
        
    # check provided .tsv file for errors using pytest
    pytest.main(["test_tsv_file.py","--tsv_path",tsv_path,'-qqqq','--tb','no'])
    
    # read in .tsv file
    df = pd.read_csv(tsv_path,sep='\t',index_col=None,header=0)

    # remove packages that generally don't work (for now) on all platforms
    df = df.loc[df['bug_flag'] != 'cross-platform']
    
    # remove packages that won't work for the specified operating system
    df = df.loc[df['bug_flag'] != operating_system]
    
    # filter for languages if specified by user
    if not languages == 'all':
        df = df.loc[df['language'].isin(languages),:]
    
    # filter for necessitiy if specified by user
    if not necessity == 'all':
        df = df.loc[df['necessity'].isin(necessity),:]
    
    # sort by language, then by package manager, then by conda channel
    df.sort_values(by=['language','package_manager','conda_channel'],inplace=True)
    
    # get all conda channels, sort by frequency and if there are ties sort alphabetically
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
    if 'pip' in df['package_manager'].values:
    
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
    
    if 'cran' in df['package_manager'].values:
    
        if cran_installation_script:
            
            if not yml_name:
                raise TypeError('When creating installation scripts for CRAN-packages you must specify a yml_name')
                        
            # subset dataframe to CRAN-packages 
            df_cran = df.loc[(df['language'] == 'R') & (df['package_manager'] == 'cran'),:]
            
            # parse list of CRAN-packages to a single string with packages separated by comma
            cran_packages = ','.join(f"'{package}'" for package in df_cran['package_name'])
            
            # write bash script that allows you to:
            # 1. activate the conda environment from within a bash-script as suggested here:
            # https://github.com/conda/conda/issues/7980#issuecomment-472648567
            # 2. use RScript to install packages within the conda environment. 
            # We have to specify a mirror because otherwise script will halt because 
            # we would have to choose one:
            # https://stackoverflow.com/questions/50870927/using-install-packages-inside-a-shell-script-through-terminal-to-automatically
            with open(cran_installation_script_path,'w') as f:
                f.write('#!/bin/bash\n')
                f.write("CONDA_BASE=$(conda info --base) && source $CONDA_BASE/etc/profile.d/conda.sh\n")
                f.write(f"conda activate {yml_name} && Rscript -e \"install.packages(c({cran_packages}),repos=\'{cran_mirror}\')\"")
    
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
    parser.add_argument('--yml_file_name',type=str,required=False,default='environment.yml',
                        help='Sets the name of the .yml file. The default is is environment.yml')
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
    parser.add_argument('--cran_installation_script',action='store_true',
                        help=' If True, generates a bash script that allows to install \
                        CRAN-packages within the conda-environment. Only valid when --yml_name is set.')
    parser.add_argument('--cran_mirror',type=str,required=False,default='https://cloud.r-project.org',
                        help="A valid URL to a CRAN-Mirror where packages should be downloaded from. \
                        The default is \'https://cloud.r-project.org\'")
    parser.add_argument('--languages',type=str,required=False,default='all',nargs='+',
                        help="Filter for certain programming languages. Valid inputs \
                        are Python, R, Julia.")
    parser.add_argument('--necessity',type=str,required=False,default='all',nargs='+',
                        help="Filter for necessity. Valid inputs are \'required\', \'optional\'")

    # parse arguments
    args = parser.parse_args()
    
    # parse .tsv file and get .yml file
    run(operating_system=args.os,
        yml_name=args.yml_name,
        yml_file_name=args.yml_file_name,
        write_conda_channels=args.write_conda_channels,
        pip_requirements_file=args.pip_requirements_file,
        tsv_path=args.tsv_path,
        yml_dir=args.yml_dir,
        cran_installation_script=args.cran_installation_script,
        cran_mirror=args.cran_mirror,
        languages=args.languages,
        necessity=args.necessity)
