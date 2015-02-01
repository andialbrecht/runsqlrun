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
