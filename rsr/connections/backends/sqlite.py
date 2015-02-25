from rsr.connections.backends.base import BaseDriver
from rsr.schema import dbo
from rsr.schema.base import BaseSchemaProvider

try:
    import sqlite3
except ImportError:
    sqlite3 = None


class SQLiteSchema(BaseSchemaProvider):

    def refresh(self, schema):
        for table in self.driver.execute_raw(SQL_TABLES):
            if table[1] == 'table':
                klass = dbo.Table
            else:
                klass = dbo.View
            t = klass(table[0], table[0])
            schema.add_object(t)
            for col in self.driver.execute_raw(('pragma table_info'
                                                '(\'{}\')').format(table[0])):
                uid = '{}#{}'.format(table[0], col[1])
                col = dbo.Column(uid, col[1], order=col[0])
                t.add_column(col)


class Driver(BaseDriver):
    dbapi = sqlite3
    schema_class = SQLiteSchema

    def get_connect_params(self):
        args = (self.config.get('db', ':memory:'),)
        kwargs = {}
        return args, kwargs


SQL_TABLES = """
SELECT name, type
FROM sqlite_master
WHERE TYPE in ('table', 'view');
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
