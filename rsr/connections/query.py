from gi.repository import GObject


class Query(GObject.GObject):

    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'finished': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, sql):
        super(Query, self).__init__()
        self.sql = sql
