from gi.repository import Gtk

from rsr.connections.query import Query
from rsr.connections.ui import ConnectionDialog
from rsr.worksheet.editor import Editor
from rsr.worksheet.results import Results


class Worksheet(Gtk.VPaned):

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

        sw = Gtk.ScrolledWindow()
        sw.add(self.results)
        self.add2(sw)

        self.connect('realize', self.on_map_event)

    def on_map_event(self, *args):
        if self.get_position() != 0:
            return
        height = self.get_parent().get_allocation().height
        self.set_position(int(height / 3) * 2)

    def save_state(self):
        if self.connection is not None:
            conn_key = self.connection.key
        else:
            conn_key = None
        return {
            'content': self.editor.get_text(),
            'split_pos': self.get_position(),
            'connection': conn_key
        }

    def restore_state(self, state):
        self.editor.set_text(state['content'])
        self.set_position(state.get('split_pos', 0))
        self.set_connection(state.get('connection', None))

    def get_tab_label(self):
        return Gtk.Label('SQL Editor')

    def assume_connection(self):
        if self.connection is not None:
            return True
        dlg = ConnectionDialog(self.win)
        if dlg.run() == Gtk.ResponseType.OK:
            self.connection = dlg.get_connection()
        dlg.destroy()
        return self.connection is not None

    def set_connection(self, key):
        if key is None:
            self.connetion = None
        else:
            self.connection = self.app.connection_manager.get_connection(key)

    def run_query(self):
        if not self.assume_connection():
            return
        query = Query(self.editor.get_text())
        self.results.set_query(query)
        self.connection.run_query(query)
