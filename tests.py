# -*- coding: utf-8 -*-
"""
Tests for GitHub Actions
@author: Johannes.Wiesner
"""

import numpy as np
import pandas as pd
import string
import pytest

df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
EXCEL_MAPPER = dict(zip(df.columns,string.ascii_uppercase))

def get_concerned_cells(boolean_df):
    '''Take in a boolean data frame where a True value indicates an error
    for that cell. Return the column and index name of the concerned cells.
    Use Excel-Style output (e.g. A1, Z3, etc.) which makes it easier for users
    to find the concerned cells in their spreadsheet program'''
    
    boolean_df.columns = boolean_df.columns.map(EXCEL_MAPPER)
    boolean_df.index = boolean_df.index + 2
    cells = boolean_df.reset_index().melt(id_vars='index').query('value == True')
    cells = cells['variable'] + cells['index'].astype(str)
    cells = cells.tolist()
    
    return cells

def test_check_whitespaces():
    '''Ensure that cells in the .tsv file have neither leading or trailing
    whitespaces'''

    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)

    # create a boolean mask 
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
        cells = get_concerned_cells(whitespace_mask)
        message = f"These cells have either leading or trailing whitespaces: {cells}"
        pytest.fail(message)
    
def test_check_filled_out_columns():
    '''Check that certain columns are filled out'''

    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)
    columns_to_check = ['package_name','language']
    df = df[columns_to_check]
    nan_mask = df.isna()
    
    if any(nan_mask.any()):
        cells = get_concerned_cells(nan_mask)
        message = f"These cells must not contain NaNs, i.e. be filled out: {cells}"
        pytest.fail(message)
        
def test_valid_options():
    '''Some columns in the .tsv file must only contain certain values'''

    df = pd.read_csv('./packages.tsv',sep='\t',index_col=None,header=0)

    # set up valid options 
    valid_options = {'package_manager':['conda','pip','cran'],
                     'language':['python','R','julia'],
                     'bug_flag':['linux','windows','cross-platform',np.nan]
                     }

    # check each column and throw error if necessary
    for column,options in valid_options.items():
        unique_column_values = df[column].unique()
        column_check = set(unique_column_values).issubset(options)    
        if column_check == False:
            message = f"The column '{column}' must only contain the following values: {options} but contains {unique_column_values}"
            pytest.fail(message)