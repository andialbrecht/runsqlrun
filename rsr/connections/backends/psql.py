from rsr.connections.backends.base import BaseDriver
from rsr.schema import dbo
from rsr.schema.base import BaseSchemaProvider

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class PsqlSchema(BaseSchemaProvider):

    def refresh(self, schema):
        tables = {}
        for item in self.driver.execute_raw(SQL_TABLES):
            if item[3] == 'r':
                klass = dbo.Table
            else:
                klass = dbo.View
            t = klass(item[0], item[1], item[2])
            schema.add_object(t)
            tables[item[0]] = t
        for col in self.driver.execute_raw(SQL_COLUMNS):
            table = tables[col[0]]
            col = dbo.Column(col[1], col[2], description=col[3], order=col[4])
            table.add_column(col)


class Driver(BaseDriver):
    dbapi = psycopg2
    schema_class = PsqlSchema

    def get_connect_params(self):
        args = ()
        kwargs = {}
        kwargs['host'] = self.config.get('host', 'localhost')
        kwargs['port'] = self.config.get('port', 5432)
        kwargs['user'] = self.config.get('username', None)
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
       d.description,
       c.relkind
from pg_catalog.pg_class c
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
left join pg_catalog.pg_description d on d.objoid = c.oid
and d.objsubid = 0
where c.relkind in ('r', 'v', 'm')
  and n.nspname = 'public';
"""


SQL_COLUMNS = """
select a.attrelid,
       a.attrelid || '-' || a.attnum as uid,
                            a.attname,
                            d.description,
                            a.attnum
from pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c on c.oid = a.attrelid
join pg_catalog.pg_namespace n on n.oid = c.relnamespace
left join pg_catalog.pg_description d on d.objoid = c.oid
and d.objsubid = a.attnum
where c.relkind in ('r', 'v')
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
