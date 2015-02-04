class SchemaProvider:

    def __init__(self, connection):
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
        self.backend.refresh_tables(self, lambda: None)

    def add_object(self, obj):
        self._objects[obj.uid] = obj

    def get_objects(self, types=None):
        return self._objects.values()
