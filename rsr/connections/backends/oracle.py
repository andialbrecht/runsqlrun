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
        for table in self.driver.execute_raw(SQL_TABLES).fetchall():
            t = dbo.Table(table[0], table[0])
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
        if self.config.get('port', None):
            dsn = cx_Oracle.makedsn(self.config['host'],
                                    self.config['port'],
                                    self.config['db'])
        else:
            dsn = self.config['db']
        conn_str = '%s/%s@%s' % (self.config.get('username'),
                                 self.config.get('password'),
                                 dsn)
        return (conn_str,), {}

    def prepare_sql(self, sql):
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]
        return sql


SQL_TABLES = """
select table_name
from user_tables;
"""

SQL_COLUMNS = """
select table_name,
       column_name,
       column_id
from user_tab_columns;
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
