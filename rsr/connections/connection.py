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
            self.db.execute(query)
            GObject.idle_add(query.emit, 'finished')
        if self.db is not None:
            self.db.close()

    def update_config(self, config):
        raise NotImplementedError()

    def get_label(self):
        return self.key

    def open(self):
        if self.db is None:
            self.db = backends.get_backend(self.config)
            if not self.db.connect():
                self.db = None
        return self.db is not None

    def run_query(self, query):
        self.queries.append(query)
