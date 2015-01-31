from gi.repository import Gtk, GObject

from rsr.connections.query import Query
from rsr.connections.ui import ConnectionDialog
from rsr.worksheet.editor import Editor
from rsr.worksheet.results import Results


class Worksheet(Gtk.VPaned):

    __gsignals__ = {
        'connection-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'active-query-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, win):
        super(Worksheet, self).__init__()
        self.win = win
        self.app = win.app
        self.editor = Editor()
        self.results = Results()
        self.connection = None

        sw = Gtk.ScrolledWindow()
        sw.add(self.editor)
        self.add1(sw)

        self.add2(self.results)

        self.connect('realize', self.on_map_event)
        self.app.connection_manager.connect(
            'connection-deleted', self.on_connection_deleted)

    def on_map_event(self, *args):
        if self.get_position() != 0:
            return
        height = self.get_parent().get_allocation().height
        self.set_position(int(height / 3) * 2)

    def on_connection_deleted(self, manager, key):
        if self.connection is not None and self.connection.key == key:
            self.set_connection(None)

    def save_state(self):
        if self.connection is not None:
            conn_key = self.connection.key
        else:
            conn_key = None
        return {
            'content': self.editor.get_text(),
            'split_pos': self.get_position(),
            'connection': conn_key,
            'cursor': self.editor.get_cursor_position(),
        }

    def restore_state(self, state):
        self.editor.set_text(state['content'])
        self.set_position(state.get('split_pos', 0))
        self.set_connection(state.get('connection', None))
        self.editor.set_cursor_position(state.get('cursor', None))

    def get_tab_label(self):
        return Gtk.Label('SQL Editor')

    def assume_connection(self, force=False):
        if self.connection is not None and not force:
            return True
        dlg = ConnectionDialog(self.win)
        if dlg.run() == Gtk.ResponseType.OK:
            self.connection = dlg.get_connection()
            self.emit('connection-changed')
        dlg.destroy()
        return self.connection is not None

    def set_connection(self, key):
        if key is None:
            self.connection = None
        else:
            self.connection = self.app.connection_manager.get_connection(key)
        self.emit('connection-changed')

    def get_active_query(self):
        return self.results.get_active_query()

    def run_query(self):
        stmt = self.editor.get_statement_at_cursor()
        if stmt is None:
            return
        if not self.assume_connection():
            return
        query = Query(stmt)
        self.results.set_query(query)
        self.emit('active-query-changed')
        self.connection.run_query(query)
