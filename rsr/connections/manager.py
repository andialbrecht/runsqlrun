import os
import json

from gi.repository import GObject
from xdg import BaseDirectory

from rsr.connections.connection import Connection


CONNECTIONS_FILE = BaseDirectory.load_first_config(
    'runsqlrun', 'connections.json')


class ConnectionManager(GObject.GObject):

    def __init__(self, app):
        super(ConnectionManager, self).__init__()
        self.app = app
        self._connections = {}
        self.update_connections()

    def update_connections(self):
        if not os.path.exists(CONNECTIONS_FILE):
            return
        with open(CONNECTIONS_FILE) as f:
            data = json.load(f)
        for key in data:
            if key in self._connections:
                self._connections.update_config(data[key])
            else:
                conn = Connection(key, data[key])
                self._connections[key] = conn
                conn.start()

    def shutdown(self):
        for key in list(self._connections):
            conn = self._connections.pop(key)
            conn.keep_running = False
            conn.join()

    def get_connections(self):
        return self._connections.values()

    def get_connection(self, key):
        return self._connections.get(key, None)
