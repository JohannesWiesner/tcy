# -*- coding: utf-8 -*-
"""
Tests for GitHub Actions
@author: Johannes.Wiesner
"""

import pandas as pd

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