import threading
import time

from gi.repository import GObject

from rsr.connections import backends
from rsr.schema.provider import SchemaProvider


class Connection(GObject.GObject, threading.Thread):

    __gsignals__ = {
        'state-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, key, config):
        GObject.GObject.__init__(self)
        threading.Thread.__init__(self)
        self.key = key
        self.config = config
        self.queries = list()
        self.db = None
        self.schema = SchemaProvider(self)
        self.keep_running = True
        self._session_pwd = False
        self._connect_request = False

    def run(self):
        while self.keep_running:
            if self._connect_request:
                try:
                    if not self.open():
                        continue
                except Exception:
                    pass
                self._connect_request = False
            if not self.queries:
                time.sleep(.05)
                continue
            query = self.queries.pop()
            try:
                if not self.open():
                    continue
            except Exception as err:
                query.finished = True
                query.failed = True
                query.error = str(err).strip()
                GObject.idle_add(query.emit, 'finished')
                # Reset session password
                self._session_pwd = None
                continue
            GObject.idle_add(query.emit, 'started')
            query.start_time = time.time()
            query.pending = False
            try:
                self.db.execute(query)
            except Exception as err:
                query.failed = True
                query.error = str(err)
            query.execution_duration = time.time() - query.start_time
            query.finished = True
            GObject.idle_add(query.emit, 'finished')
        if self.db is not None:
            self.db.close()
            self.db = None
            self.emit('state-changed')

    def is_open(self):
        return self.db is not None

    def update_config(self, config):
        # TODO: if the connection is open something should happen...
        self.config = config

    def requires_password(self):
        password = self.config.get('password', None)
        if password is None or not password.strip():
            return not self._session_pwd_set
        return False

    def set_session_password(self, password):
        self._session_pwd_set = True
        self.config['password'] = password

    def has_session_password(self):
        return self._session_pwd

    def get_label(self):
        lbl = self.config.get('name')
        if not lbl:
            # TODO: add some URI building like sqlalchemy does it as a fallback
            parts = []
            if self.config.get('db'):
                parts.append(self.config.get('db'))
            if self.config.get('host'):
                parts.append(self.config.get('host'))
            if parts:
                lbl = '@'.join(parts)
            else:
                lbl = self.key
        return lbl

    def open(self):
        if self.db is None:
            self.db = backends.get_backend(self.config)
            if not self.db.connect():
                self.db = None
            self.schema.refresh()
            self.emit('state-changed')
        return self.db is not None

    def request_open(self):
        """This is called from the main thread to open a connection."""
        self._connect_request = True

    def run_query(self, query):
        self.queries.append(query)
