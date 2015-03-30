from gi.repository import GObject


class SchemaProvider(GObject.GObject):

    __gsignals__ = {
        'refreshed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, connection):
        super(SchemaProvider, self).__init__()
        self.connection = connection
        self._objects = {}

    @property
    def backend(self):
        if self.connection.db is None:
            return None
        else:
            return self.connection.db.schema

    def refresh(self):
        if self.backend is None:
            return
        self.backend.refresh(self)
        self.emit('refreshed')

    def add_object(self, obj):
        self._objects[obj.uid] = obj

    def get_objects(self, types=None):
        return self._objects.values()
