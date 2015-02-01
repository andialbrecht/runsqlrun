from rsr.connections.backends.base import BaseDriver
from rsr.schema import dbo
from rsr.schema.base import BaseSchemaProvider

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class PsqlSchema(BaseSchemaProvider):

    def refresh_tables(self, schema, cb):
        for table in self.driver.execute_raw(SQL_TABLES):
            schema.add_object(dbo.Table(table[0], table[1], table[2]))


class Driver(BaseDriver):
    dbapi = psycopg2
    schema_class = PsqlSchema

    def get_connect_params(self):
        args = ()
        kwargs = {}
        kwargs['host'] = self.config.get('host', 'localhost')
        kwargs['port'] = self.config.get('port', 5432)
        kwargs['user'] = self.config.get('user', None)
        kwargs['password'] = self.config.get('password', None)
        kwargs['dbname'] = self.config.get('db', None)
        return args, kwargs

    def connect(self):
        connected = super(Driver, self).connect()
        if connected:
            self._conn.autocommit = True
        return connected


SQL_TABLES = """
select c.oid,
       c.relname,
       d.description
from pg_catalog.pg_class c
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
left join pg_catalog.pg_description d on d.objoid = c.oid
and d.objsubid = 0
where c.relkind = 'r'
  and n.nspname = 'public';
"""


SQL_COLUMNS = """
select a.attrelid,
       a.attrelid || '-' || a.attnum as uid,
                            a.attname,
                            d.description
from pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c on c.oid = a.attrelid
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
left join pg_catalog.pg_description d on d.objoid = c.oid
and d.objsubid = a.attnum
where c.relkind = 'r'
  and n.nspname = 'public'
  and a.attnum >= 0;
"""


SQL_CONSTRAINTS = """
select f.oid,
       f.conname,
       f.contype,
       f.conrelid,
       f.conkey,
       f.confrelid,
       f.confkey
from pg_catalog.pg_constraint f
join pg_catalog.pg_class c on c.oid = f.conrelid
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
where c.relkind = 'r'
  and n.nspname = 'public';
"""
