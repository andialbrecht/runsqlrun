class BaseDriver:

    dbapi = None

    def __init__(self, config):
        self.config = config
        self._conn = None

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

    def execute(self, query):
        cur = self._conn.cursor()
        cur.execute(query.sql)
        query.description = cur.description
        query.result = cur.fetchall()
        cur.close()
