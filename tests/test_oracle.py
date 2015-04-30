# Tests for Oracle related functions.

import pytest

from rsr.connections.backends.oracle import Driver


@pytest.mark.parametrize('config,expected', [
    ({'username': 'foo', 'password': 'secret', 'host': 'localhost'},
     {'user': 'foo', 'password': 'secret', 'dsn': 'localhost'}),  # issue2
])
def test_get_connect_params(config, expected):
    driver = Driver(config)
    assert driver.get_connect_params()[0] == tuple()
    assert driver.get_connect_params()[1] == expected


@pytest.mark.parametrize('sql,expected', [
    (' select 1\nfrom dual;  ', 'select 1\nfrom dual'),
    ('select 1\nfrom dual; -- should work', 'select 1\nfrom dual'),
])
def test_prepare_statement(sql, expected):
    driver = Driver({})
    assert driver.prepare_sql(sql) == expected
