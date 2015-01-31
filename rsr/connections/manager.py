import json
import os
import uuid

from gi.repository import GObject
from xdg import BaseDirectory

from rsr.connections.backends import get_available_drivers
from rsr.connections.connection import Connection


CONNECTIONS_FILE = os.path.join(BaseDirectory.save_config_path('runsqlrun'),
                                'connections.json')


class ConnectionManager(GObject.GObject):

    __gsignals__ = {
        'connection-deleted': (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

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
                self._connections[key].update_config(data[key])
            else:
                conn = Connection(key, data[key])
                self._connections[key] = conn
                conn.start()
        # remove deleted connections
        for key in list(self._connections):
            if key not in data:
                conn = self._connections.pop(key)
                conn.keep_running = False
                conn.join()
                self.emit('connection-deleted', conn.key)

    def shutdown(self):
        for key in list(self._connections):
            conn = self._connections.pop(key)
            conn.keep_running = False
            conn.join()

    def get_connections(self):
        return self._connections.values()

    def get_connection(self, key):
        return self._connections.get(key, None)

    def get_available_drivers(self):
        return get_available_drivers()

    def test_connection(self, data):
        conn = Connection(None, data)
        try:
            conn.open()
            return True
        except Exception as err:
            return str(err).strip()

    def update_connection(self, data):
        if 'key' not in data:
            data['key'] = str(uuid.uuid4()).replace('-', '')
        key = data.pop('key')
        if os.path.exists(CONNECTIONS_FILE):
            with open(CONNECTIONS_FILE) as f:
                content = json.load(f)
        else:
            content = {}
        content[key] = data
        with open(CONNECTIONS_FILE, 'w') as f:
            json.dump(content, f)
        self.update_connections()
        return key

    def delete_connection(self, key):
        with open(CONNECTIONS_FILE) as f:
            content = json.load(f)
        if key in content:
            del content[key]
            with open(CONNECTIONS_FILE, 'w') as f:
                json.dump(content, f)
        self.update_connections()
