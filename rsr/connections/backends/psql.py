from rsr.connections.backends.base import BaseDriver

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class Driver(BaseDriver):
    dbapi = psycopg2

    def get_connect_params(self):
        args = ()
        kwargs = {}
        kwargs['host'] = self.config.get('host', 'localhost')
        kwargs['port'] = self.config.get('port', 5432)
        kwargs['user'] = self.config.get('user', None)
        kwargs['password'] = self.config.get('password', None)
        kwargs['dbname'] = self.config.get('db', None)
        return args, kwargs
