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

@pytest.fixture()
def setup(request):
    '''Returns everything that the tests need in order to run'''

    # read in the .tsv file as dataframe
    # FIXME: Already here something can go wrong, if the .tsv file is corrupted! See issue #7
    tsv_path = request.config.getoption("tsv_path")
    df = pd.read_csv(tsv_path,sep='\t',index_col=None,header=0,dtype=str)

    # map each column name to the alphabet (needed for get_affected_cells function)
    excel_mapper = dict(zip(df.columns,string.ascii_uppercase))

    setup_dict = {'tsv_path':tsv_path,'df':df,'excel_mapper':excel_mapper}

    # add all test configs to the dictionary
    with open('./test_configs.json') as f:
        test_configs = json.load(f)
        setup_dict = {**test_configs,**setup_dict}

    return setup_dict

def get_affected_cells(mask_df,excel_mapper):
    '''Helper function that takes in a boolean data frame where true values
    indicate an error for that cell. Returns the column and index name of the
    concerned cells in spreadsheet-program style (e.g. A1, Z3, etc.) which
    makes it easier for users to find and correct the affected cells
    in their spreadsheet program'''

    mask_df.columns = mask_df.columns.map(excel_mapper)
    mask_df.index = mask_df.index + 2
    cells = mask_df.reset_index().melt(id_vars='index').query('value == True')
    cells = cells['variable'] + cells['index'].astype(str)
    cells = cells.tolist()

    return cells

def test_tsv_path(setup):
    '''Test if the provided path to the .tsv file points to an existing file.
    Note: This function is not that relevant if path to .tsv file is hardcoded into
    setup fixture'''

    tsv_path = setup['tsv_path']

    if not os.path.isfile(tsv_path):
        pytest.fail('Path to spreadsheet file does not point to an existing file')

def test_tsv(setup):
    '''Test that the provided spreadsheet file is a .tsv file (and not .csv, .xlsx, etc).
    Note: This function is not that relevant if path to .tsv file is hardcoded into
    setup fixture'''

    tsv_path = setup['tsv_path']

    if not tsv_path.endswith('.tsv'):
        pytest.fail('Provided spreadsheet file must be a .tsv file')

def test_whitespaces(setup):
    '''Ensure that cells in the .tsv file have neither leading or trailing
    whitespaces'''

    df = setup['df']
    excel_mapper = setup['excel_mapper']

    def create_mask(cell):
        if pd.isna(cell):
            return False
        if cell.startswith(' ') or cell.endswith(' '):
            return True
        else:
            return False

    whitespace_mask = df.astype(str).map(create_mask)

    if whitespace_mask.any(axis=None):
        affected_cells = get_affected_cells(whitespace_mask,excel_mapper)
        message = f"These cells have either leading or trailing whitespaces: {', '.join(affected_cells)}"
        pytest.fail(message)

def test_valid_columns(setup):
    '''Test that dataframe has all necessary columns'''

    valid_columns = setup['valid_columns']
    df = setup['df']

    if valid_columns:

        if not set(valid_columns).issubset(df.columns):
            message = "The .tsv file must have at least these columns: "
            message += f"{', '.join(valid_columns)}"
            pytest.fail(message)

def test_filled_out_columns(setup):
    '''Check that certain columns are completely filled out'''

    filled_out_columns = setup['filled_out_columns']
    df = setup['df']
    excel_mapper = setup['excel_mapper']

    if filled_out_columns:

        df = df[filled_out_columns]
        nan_mask = df.isna()

        if any(nan_mask.any()):
            affected_cells = get_affected_cells(nan_mask,excel_mapper)
            message = f"These cells must not contain NaNs, i.e. be filled out: {', '.join(affected_cells)}"
            pytest.fail(message)

def test_valid_options(setup):
    '''Some columns in the .tsv file must only contain certain values'''

    valid_options = setup['valid_options']
    df = setup['df']

    if valid_options:

        message = ""

        # check each column and throw error if necessary
        for column,options in valid_options.items():

            current_column_values = df[column].astype(str).unique().tolist()
            column_check = set(current_column_values).issubset(options)

            if column_check == False:
                message += f"The column '{column}' must only contain the following values: "
                message += f"{options} but it contains these values {current_column_values}\n"

        if message:
            pytest.fail(message)

def test_multi_option_columns(setup):
    '''For each specified column check that rows must only contain valid strings
    separated by comma and optional whitespaces'''

    multi_option_columns = setup['multi_option_columns']
    df = setup['df']
    excel_mapper = setup['excel_mapper']

    if multi_option_columns:

        message = ""

        # reduce dataframe to columns of interest
        for column,options in multi_option_columns.items():

            # drop rows with NaNs in that column
            df = df.dropna(subset=[column])

            # convert series to series of lists (remove whitespaces first)
            series = df[column].str.replace(' ','')
            series_of_lists = series.str.split(',')

            # for each row check that provided options are a superset of the current list
            mask = ~series_of_lists.apply(set(options).issuperset).to_frame()

            # return list of affects cells where you found error
            affected_cells = get_affected_cells(mask,excel_mapper)

            if len(affected_cells) != 0:
                message += f"Cells in the {column} column must only contain these values: "
                message += f"{', '.join(multi_option_columns[column])}. "
                message += f"Please check these cells: {', '.join(affected_cells)}\n"

        if message:
            pytest.fail(message)

def test_column_dependencies(setup):
    '''For each specified column check that all other columns are filled out'''

    column_dependencies = setup['column_dependencies']
    df = setup['df']
    excel_mapper = setup['excel_mapper']

    if column_dependencies:

        message = ""

        for source_column,other_columns in column_dependencies.items():

            # create a subset of the original dataframe that only contains
            # rows where source column is filled out
            source_column_df = df.dropna(subset=source_column)

            # now check that all other specified columns are not NaN
            other_columns_df = source_column_df[other_columns]
            nan_mask = other_columns_df.isna()
            affected_cells = get_affected_cells(nan_mask,excel_mapper)

            # if you found any cells, add to dictionary for later error printing
            if len(affected_cells) != 0:
                message += "The following cells must be filled out because you"
                message += "filled out a cell in {source_column}: {', '.join(affected_cells)}\n"

        if message:
            pytest.fail(message)

def test_conditional_column_dependecies(setup):
    '''For each specific column and its condition check that other columns are filled out'''

    conditional_column_dependencies = setup['conditional_column_dependencies']
    df = setup['df']
    excel_mapper = setup['excel_mapper']

    if conditional_column_dependencies:

        message = ""

        for column,condition_dict in conditional_column_dependencies.items():

            for condition,other in condition_dict.items():

                # reduce dataframe to condition
                condition_df = df.loc[df[column] == condition]

                # now check which cells in other columns are not filled out
                nan_mask = condition_df[other].isna()
                affected_cells = get_affected_cells(nan_mask,excel_mapper)

                # if you found any cells, add to message
                if len(affected_cells) != 0:

                    message += f"The following cells must be filled out because " \
                                f"corresponding cells in {column} are set to " \
                                f"{condition}: {', '.join(affected_cells)}\n"

        if message:
            pytest.fail(message)
