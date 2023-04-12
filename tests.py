# -*- coding: utf-8 -*-
"""
Tests for GitHub Actions
@author: Johannes.Wiesner
"""

import numpy as np
import pandas as pd

# FIXME: Would be more nice to get 'coordinates' as you see them in LibreOffice
# or Excel (e.g. A1,B5, etc.)
# FIXME: Not really necessary to do this for the whole .tsv file. Only for
# the columns that are needed to generate the .yml file. See function below,
# we could reduce dataframe to a subset of columns
def test_check_whitespaces():
    '''Ensure that no cell in the .tsv file has leading or trailing whitespaces'''

    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
    
    # create a boolean mask that where True tells that a cell has whitespaces
    def create_mask(cell):
        if pd.isna(cell):
            return False
        if cell.startswith(' ') or cell.endswith(' '):
            return True
        else:
            return False
    
    whitespace_mask = df.applymap(create_mask)
    
    # give user feedback which cells are concerned
    if whitespace_mask.any(axis=None):
        cells_with_whitespaces = df.where(whitespace_mask).stack()
        print('These cells have either leading or trailing whitespaces')
        for idx,value in cells_with_whitespaces.items():
            print(f"Index: {idx[0]}, Column: {idx[1]}, Value: {value}")
    
    # throw assertion error if the boolean mask has any true values
    assert whitespace_mask.any(axis=None) == False
    
def test_check_filled_out_columns():
    '''Check that certain columns are filled out'''

    columns_to_check = ['package_name','language']
    
    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
    df = df[columns_to_check]
    column_results = df.isna().any()
    
    if any(column_results):
        columns_with_nans = column_results[column_results == True]
        print('These columns must not contain NaNs, i.e. have values in every cell:')
        [print(col) for col in columns_with_nans.index.tolist()]
    
    assert any(column_results) == False
    
def test_valid_options():
    '''Some columns in the .tsv file must only contain certain values'''
    

    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
    
    # set up valid options 
    valid_options_dict = {'package_manager':['conda','pip','cran'],
                     'language':['python','R','julia'],
                     'bug_flag':['linux','windows','cross-platform',np.nan]}
    
    # check each column and throw error if necessary
    for column,valid_options in valid_options_dict.items():
        column_results = df[column].unique()
        column_check = set(column_results).issubset(valid_options)    
        assert_info = f"The column {column} must only contain the following values: {valid_options} but contains {column_results}"
        assert column_check == True, assert_info