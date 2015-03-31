class DbObject:

    type_key = None
    type_name = None

    def __init__(self, uid, name, description=None):
        self.uid = uid
        self.name = name
        self.description = description

    def get_type_name(self):
        return self.type_name


class DBObjectColumns(DbObject):

    def __init__(self, *args, **kwargs):
        super(DBObjectColumns, self).__init__(*args, **kwargs)
        self._columns = {}

    @property
    def columns(self):
        cols = list(self._columns.values())
        cols.sort(key=lambda k: k.order)
        return cols

    def add_column(self, col):
        self._columns[col.uid] = col


class Table(DBObjectColumns):
    type_key = 'table'
    type_name = 'Table'


class View(DBObjectColumns):
    type_key = 'view'
    type_name = 'View'

    def __init__(self, *args, **kwargs):
        self.statement = kwargs.pop('statement', None)
        super(View, self).__init__(*args, **kwargs)


class Column(DbObject):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', 0)
        super(Column, self).__init__(*args, **kwargs)
