import threading
import time

from gi.repository import GObject

from rsr.connections import backends


class Connection(threading.Thread):

    def __init__(self, key, config):
        super(Connection, self).__init__()
        self.key = key
        self.config = config
        self.queries = list()
        self.db = None
        self.keep_running = True

    def run(self):
        while self.keep_running:
            if not self.queries:
                time.sleep(.05)
                continue
            query = self.queries.pop()
            if not self.open():
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

    def update_config(self, config):
        # TODO: if the connection is open something should happen...
        self.config = config

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
        return self.db is not None

    def run_query(self, query):
        self.queries.append(query)
