"""Offline extension tests; no acquisition, historical scripts or shared-file writes."""
import sys
from pathlib import Path
import socket
import pytest

MODULE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(MODULE))


def pytest_configure(config):
    config.addinivalue_line('filterwarnings',r'error::EncodingWarning:^(acquire|model|prepare|analyze|plot|build_docs|verify_extension)$')


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args,**kwargs):
        raise AssertionError('Routine extension tests must remain offline')
    monkeypatch.setattr(socket.socket,'connect',blocked)


@pytest.fixture(scope='session')
def tables():
    import pandas as pd
    return {name:pd.read_csv(MODULE/'data'/f'{name}.csv',encoding='utf-8') for name in
        ['native_migration','harmonized_migration','population_denominators','population_structure_join','acs_source_cells']}
