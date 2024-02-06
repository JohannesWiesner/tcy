# -*- coding: utf-8 -*-
"""
Test integrity of the provided spreadsheet file
@author: Johannes.Wiesner
"""

import pandas as pd
import string
import pytest
import os
import json

class TestTsvFile:
    
    @pytest.fixture(autouse=True)
    def setup(self,request):
        self.tsv_path = request.config.getoption("tsv_path")

        # FIXME: Should throw some sort of error if there are any weird characters in this file
        # See issue #7
        self.df = pd.read_csv(self.tsv_path,sep='\t',index_col=None,header=0)
        self.excel_mapper = dict(zip(self.df.columns,string.ascii_uppercase))
        
        with open('./test_configs.json') as f:
            self.test_configs = json.load(f)
            self.valid_columns = self.test_configs['valid_columns']
            self.filled_out_columns = self.test_configs['filled_out_columns']
            self.valid_options = self.test_configs['valid_options']
            self.column_dependencies = self.test_configs['column_dependencies']
            self.multi_option_columns = self.test_configs['multi_option_columns']
        
    def get_affected_cells(self,mask_df):
        '''Take in a boolean data frame where true values indicate an error
        for that cell. Return the column and index name of the concerned cells.
        Use Excel-Style output (e.g. A1, Z3, etc.) which makes it easier for users
        to find the concerned cells in their spreadsheet program'''

        mask_df.columns = mask_df.columns.map(self.excel_mapper)
        mask_df.index = mask_df.index + 2
        cells = mask_df.reset_index().melt(id_vars='index').query('value == True')
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
        
        whitespace_mask = self.df.astype(str).applymap(create_mask)
        
        if whitespace_mask.any(axis=None):
            cells = self.get_affected_cells(whitespace_mask)
            message = f"These cells have either leading or trailing whitespaces: {', '.join(cells)}"
            pytest.fail(message)
    
    # FIXME: Should test for equality not for subset!
    def test_valid_columns(self):
        '''Test that dataframe has all necessary columns'''
        
        if self.valid_columns:
    
            if list(self.df.columns) != self.valid_columns:
                pytest.fail(f"datasets.tsv must have only these columns in that exact order: {', '.join(self.valid_columns)}")
            
    def test_filled_out_columns(self):
        '''Check that certain columns are completely filled out'''
        
        if self.filled_out_columns:
            
            df = self.df[self.filled_out_columns]
            nan_mask = df.isna()
            
            if any(nan_mask.any()):
                cells = self.get_affected_cells(nan_mask)
                message = f"These cells must not contain NaNs, i.e. be filled out: {', '.join(cells)}"
                pytest.fail(message)

    def test_valid_options(self):
        '''Some columns in the .tsv file must only contain certain values (NaN values
        are ignored for this test)'''
    
        if self.valid_options:
    
            # check each column and throw error if necessary
            for column,options in self.valid_options.items():
                current_column_values = self.df[column].dropna().unique()
                column_check = set(current_column_values).issubset(options)    
                if column_check == False:
                    message = f"The column '{column}' must only contain the following values: {options} but contains {current_column_values}"
                    pytest.fail(message)
    
    def test_column_dependencies(self):
        '''For each specified column check that all other columns are filled out'''
        
        if self.column_dependencies:
        
            affected_cells_dict = {}
    
            for source_column,other_columns in self.column_dependencies.items():
                
                # create a subset of the original dataframe that only contains
                # rows where source column is filled out
                source_column_df = self.df.dropna(subset=source_column)
                
                # now check that all other specified columns are not NaN
                other_columns_df = source_column_df[other_columns]
                nan_mask = other_columns_df.isna()
                affected_cells = self.get_affected_cells(nan_mask)
                
                # if you found any cells, add to dictionary for later error printing
                if len(affected_cells) != 0:
                    affected_cells_dict[source_column] = affected_cells
    
            # raise an error if the dictionary is not empty
            if affected_cells_dict:
                message = ""
                for column,cells in affected_cells_dict.items():
                    message += f"The following cells must be filled out because you filled out a cell in {column}: {', '.join(cells)}\n"
                pytest.fail(message)
                
    def test_multi_option_columns(self):
        '''For each specified column check that rows must only contain valid strings
        separated by comma and optional whitespaces'''
        
        if self.multi_option_columns:
            
            affected_cells_dict = {}

            # reduce dataframe to columns of interest
            for column,options in self.multi_option_columns.items():
                    
                # drop rows with NaNs in that column
                df = self.df.dropna(subset=[column])
                
                # convert series to series of lists (remove whitespaces first)
                series = df[column].str.replace(' ','')
                series_of_lists = series.str.split(',')
                
                # for each row check that provided options are a superset of the current list
                mask = ~series_of_lists.apply(set(options).issuperset).to_frame()
                
                # return list of affects cells where you found error
                affected_cells = self.get_affected_cells(mask)

                if len(affected_cells) != 0:
                    affected_cells_dict[column] = affected_cells

            # raise an error if the dictionary is not empty
            if affected_cells_dict:
                message = ""
                for column,cells in affected_cells_dict.items():
                    message += f"Cells in the {column} column must only contain these values: "
                    message += f"{', '.join(self.multi_option_columns[column])}. "
                    message += f"Please check these cells: {', '.join(cells)}\n"
                pytest.fail(message)
