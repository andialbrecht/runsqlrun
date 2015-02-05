import importlib
from collections import namedtuple

DriverSpec = namedtuple('DriverSpec', 'key, name, module')

DRIVERS = [
    DriverSpec('psql', 'PostgreSQL', 'psycopg2'),
    DriverSpec('mysql', 'MariaDB / MySQL', 'mysql.connector'),
    DriverSpec('oracle', 'Oracle', 'cx_Oracle'),
]


def get_backend(config):
    if config.get('driver', None) == 'psql':
        from rsr.connections.backends import psql
        return psql.Driver(config)
    elif config.get('driver', None) == 'mysql':
        from rsr.connections.backends import mysql
        return mysql.Driver(config)
    elif config.get('driver', None) == 'oracle':
        from rsr.connections.backends import oracle
        return oracle.Driver(config)
    else:
        raise NotImplementedError()


def get_available_drivers():
    for spec in DRIVERS:
        try:
            importlib.import_module(spec.module)
            yield spec
        except ImportError:
            pass
