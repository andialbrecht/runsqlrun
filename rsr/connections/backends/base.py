class BaseDriver:

    dbapi = None
    schema_class = None

    def __init__(self, config):
        self.config = config
        self._conn = None

    @property
    def schema(self):
        if self.schema_class is None:
            return
        return self.schema_class(self)

    def get_connect_params(self):
        raise NotImplementedError()

    def connect(self):
        assert self.dbapi is not None
        args, kwargs = self.get_connect_params()
        self._conn = self.dbapi.connect(*args, **kwargs)
        return True

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def prepare_sql(self, sql):
        return sql

    def execute(self, query):
        cur = self._conn.cursor()
        cur.execute(self.prepare_sql(query.sql))
        query.description = cur.description
        query.result = cur.fetchall()
        cur.close()

    def execute_raw(self, sql):
        cur = self._conn.cursor()
        cur.execute(self.prepare_sql(sql))
        return cur
