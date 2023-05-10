# -*- coding: utf-8 -*-
"""
Test integrity of the provided spreadsheet file
@author: Johannes.Wiesner
"""

import numpy as np
import pandas as pd
import string
import pytest
import os

class TestTsvFile:
    
    @pytest.fixture(autouse=True)
    def setup(self,request):
        self.tsv_path = request.config.getoption("tsv_path")
        self.df = pd.read_csv(self.tsv_path,sep='\t',index_col=None,header=0)
        self.excel_mapper = dict(zip(self.df.columns,string.ascii_uppercase))
        self.valid_columns = ['package_name',
                              'version',
                              'installation_command',
                              'package_manager',
                              'conda_channel',
                              'area',
                              'link',
                              'necessity',
                              'description',
                              'comment',
                              'language',
                              'bug_flag']
        
        self.valid_options = {'package_manager':['conda','pip','cran'],
                              'language':['Python','R','Julia'],
                              'bug_flag':['linux','windows','cross-platform',np.nan]
                              }
        self.filled_out_columns = ['package_name','language']

    def get_concerned_cells(self,boolean_df):
        '''Take in a boolean data frame where true values indicate an error
        for that cell. Return the column and index name of the concerned cells.
        Use Excel-Style output (e.g. A1, Z3, etc.) which makes it easier for users
        to find the concerned cells in their spreadsheet program'''

        boolean_df.columns = boolean_df.columns.map(self.excel_mapper)
        boolean_df.index = boolean_df.index + 2
        cells = boolean_df.reset_index().melt(id_vars='index').query('value == True')
        cells = cells['variable'] + cells['index'].astype(str)
        cells = cells.tolist()
        
        return cells

    def test_tsv_path(self):
        '''Test if the provided path to the .tsv file points to an existing file'''
        if not os.path.isfile(self.tsv_path):
            pytest.fail('Path to spreadsheet file does not point to an existing file')
        
    def test_tsv(self):
        '''Test that the provided spreadsheet file is a .tsv file (and not .csv, .xlsx, etc)'''
        if not self.tsv_path.endswith('.tsv'):
            pytest.fail('Provided spreadsheet file must be a .tsv file')
    
    def test_columns(self):
        '''Test that dataframe has all necessary columns'''
        if not set(self.df.columns).issubset(self.valid_columns):
            pytest.fail(f"Valid column names are: {self.valid_columns}")

    def test_whitespaces(self):
        '''Ensure that cells in the .tsv file have neither leading or trailing
        whitespaces'''
        
        # create a boolean mask (True indicates cell with leading
        # or trailing whitespace)
        def create_mask(cell):
            if pd.isna(cell):
                return False
            if cell.startswith(' ') or cell.endswith(' '):
                return True
            else:
                return False
        
        whitespace_mask = self.df.applymap(create_mask)
        
        if whitespace_mask.any(axis=None):
            cells = self.get_concerned_cells(whitespace_mask)
            message = f"These cells have either leading or trailing whitespaces: {cells}"
            pytest.fail(message)
    
    def test_filled_out_columns(self):
        '''Check that certain columns are completely filled out'''
    
        df = self.df[self.filled_out_columns]
        nan_mask = df.isna()
        
        if any(nan_mask.any()):
            cells = self.get_concerned_cells(nan_mask)
            message = f"These cells must not contain NaNs, i.e. be filled out: {cells}"
            pytest.fail(message)
            
    def test_valid_options(self):
        '''Some columns in the .tsv file must only contain certain values'''
    
        # check each column and throw error if necessary
        for column,options in self.valid_options.items():
            current_column_values = self.df[column].unique()
            column_check = set(current_column_values).issubset(options)    
            if column_check == False:
                message = f"The column '{column}' must only contain the following values: {options} but contains {current_column_values}"
                pytest.fail(message)
