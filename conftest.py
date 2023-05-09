import pytest

def pytest_addoption(parser):
    parser.addoption("--tsv_path",action="store",default='./packages.tsv')

