from rsr.connections.backends.base import BaseDriver
from rsr.schema import dbo
from rsr.schema.base import BaseSchemaProvider

try:
    import cx_Oracle
except ImportError as err:
    cx_Oracle = None


class OracleSchema(BaseSchemaProvider):

    def refresh(self, schema):
        tables = {}
        for item in self.driver.execute_raw(SQL_TABLES).fetchall():
            if item[1] == 't':
                klass = dbo.Table
            else:
                klass = dbo.View
            t = klass(item[0], item[0])
            schema.add_object(t)
            tables[t.uid] = t
        for col in self.driver.execute_raw(SQL_COLUMNS):
            table = tables[col[0]]
            uid = '{}#{}'.format(col[0], col[1])
            col = dbo.Column(uid, col[1], order=col[2])
            table.add_column(col)


class Driver(BaseDriver):
    dbapi = cx_Oracle
    schema_class = OracleSchema

    def get_connect_params(self):
        # derived from sqlalchemy.databases.oracle
        if self.config.get('db'):
            # if we have a database, then we have a remote host
            if self.config.get('port'):
                port = int(self.config.get('port'))
            else:
                port = 1521
            dsn = self.dbapi.makedsn(
                self.config.get('host', 'localhost'), port,
                self.config.get('db'))
        else:
            # we have a local tnsname
            dsn = self.config.get('host', 'localhost')

        opts = dict(user=self.config.get('username'),
                    password=self.config.get('password'),
                    dsn=dsn)
        # TODO: Implement mode setting for Oracle connections.
        # This is the old code from CrunchyFCrog:
        # if 'mode' in url.query:
        #     opts['mode'] = url.query['mode']
        #     if isinstance(opts['mode'], basestring):
        #         mode = opts['mode'].upper()
        #         if mode == 'SYSDBA':
        #             opts['mode'] = self.dbapi.SYSDBA
        #         elif mode == 'SYSOPER':
        #             opts['mode'] = self.dbapi.SYSOPER
        #         else:
        #             opts['mode'] = int(opts['mode'])
        return tuple(), opts

    def prepare_sql(self, sql):
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]
        return sql


SQL_TABLES = """
select table_name, 't' as type
from user_tables
union
select view_name, 'v' as type
from user_views;
"""

SQL_COLUMNS = """
SELECT table_name,
       column_name,
       column_id
FROM user_tab_columns;
"""

SQL_FK_CONSTRAINTS = """
SELECT a.table_name,
       a.column_name,
       a.constraint_name,
       c_pk.table_name r_table_name,
       b.column_name
FROM user_cons_columns a
JOIN user_constraints c ON a.owner = c.owner
    AND a.constraint_name = c.constraint_name
JOIN user_constraints c_pk ON c.r_owner = c_pk.owner
    AND c.r_constraint_name = c_pk.constraint_name
JOIN user_cons_columns b on b.owner = c_pk.owner
    and b.constraint_name = c_pk.constraint_name
WHERE c.constraint_type = 'R'
"""
