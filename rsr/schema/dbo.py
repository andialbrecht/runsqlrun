class DbObject:

    type_key = None
    type_label = None

    def __init__(self, uid, name, description=None):
        self.uid = uid
        self.name = name
        self.description = description

    def get_type_name(self):
        return self.type_label


class Table(DbObject):
    type_key = 'table'
    type_name = 'Table'

    def __init__(self, *args, **kwargs):
        super(Table, self).__init__(*args, **kwargs)
        self._columns = {}

    @property
    def columns(self):
        cols = list(self._columns.values())
        cols.sort(key=lambda k: k.order)
        return cols

    def add_column(self, col):
        self._columns[col.uid] = col


class Column(DbObject):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', 0)
        super(Column, self).__init__(*args, **kwargs)
