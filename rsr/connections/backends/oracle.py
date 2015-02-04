from rsr.connections.backends.base import BaseDriver

try:
    import cx_Oracle
except ImportError as err:
    cx_Oracle = None


class Driver(BaseDriver):
    dbapi = cx_Oracle

    def get_connect_params(self):
        if self.config.get('port', None):
            dsn = cx_Oracle.makedsn(self.config['host'],
                                    self.config['port'],
                                    self.config['db'])
        else:
            dsn = self.config['db']
        conn_str = '%s/%s@%s' % (self.config.get('user'),
                                 self.config.get('password'),
                                 dsn)
        return (conn_str,), {}
