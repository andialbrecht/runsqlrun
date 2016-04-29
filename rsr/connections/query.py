import locale

from gi.repository import GObject


class Query(GObject.GObject):

    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'finished': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, sql):
        super(Query, self).__init__()
        self.sql = sql
        self.pending = True
        self.finished = False
        self.failed = False
        self.error = None
        self.result = None
        self.description = None
        self.rowcount = None
        self.start_time = None
        self.execution_duration = None

    def get_result_summary(self):
        """Returns a single line string describing the result."""
        if not self.finished:
            return None
        if self.result is not None:
            return '{} rows, {} seconds'.format(
                locale.format('%d', len(self.result), grouping=True),
                locale.format('%.3f', self.execution_duration, grouping=True))
        else:
            return '{} rows affected, {} seconds'.format(
                locale.format('%d', self.rowcount, grouping=True),
                locale.foramt('%.3f', self.execution_duration, grouping=True))
