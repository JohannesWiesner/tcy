# this allows users to point test_tsv_file.py to the location of the
# packages.tsv file

import pytest

def pytest_addoption(parser):
    parser.addoption("--tsv_path",action="store",default='./packages.tsv')

