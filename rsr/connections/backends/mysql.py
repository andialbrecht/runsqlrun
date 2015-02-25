from rsr.connections.backends.base import BaseDriver
from rsr.schema import dbo
from rsr.schema.base import BaseSchemaProvider

try:
    import mysql.connector as mysql_connector
except ImportError:
    mysql_connector = None


class MySqlSchema(BaseSchemaProvider):

    def refresh(self, schema):
        tables = {}
        sql = SQL_TABLES % {'schema': self.driver.config['db']}
        for item in self.driver.execute_raw(sql):
            uid = '{}.{}'.format(item[0], item[1])
            if item[3] == 't':
                klass = dbo.Table
            else:
                klass = dbo.View
            t = klass(uid, item[1], item[2])
            schema.add_object(t)
            tables[uid] = t
        sql = SQL_COLUMNS % {'schema': self.driver.config['db']}
        for col in self.driver.execute_raw(sql):
            table_uid = '{}.{}'.format(col[0], col[1])
            table = tables[table_uid]
            col_uid = '{}.{}'.format(table_uid, col[2])
            col = dbo.Column(col_uid, col[2], description=col[4], order=col[3])
            table.add_column(col)


class Driver(BaseDriver):
    dbapi = mysql_connector
    schema_class = MySqlSchema

    def get_connect_params(self):
        args = ()
        kwargs = {}
        kwargs['host'] = self.config.get('host', 'localhost')
        if 'port' in self.config:
            kwargs['port'] = self.config['port']
        kwargs['user'] = self.config.get('username', None)
        kwargs['passwd'] = self.config.get('password', None)
        kwargs['database'] = self.config.get('db', None)
        return args, kwargs


SQL_TABLES = """
SELECT table_schema,
       table_name,
       table_comment,
       't'
FROM information_schema.tables
WHERE table_schema = '%(schema)s'
UNION
SELECT table_schema,
       table_name,
       null,
       'v'
FROM information_schema.views
WHERE table_schema = '%(schema)s'
"""


SQL_COLUMNS = """
SELECT table_schema,
       TABLE_NAME,
       COLUMN_NAME,
       ordinal_position,
       column_comment
FROM information_schema.columns
where table_schema = '%(schema)s'
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
