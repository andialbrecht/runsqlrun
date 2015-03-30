from gi.repository import Gtk, GObject

from rsr.connections.query import Query
from rsr.connections.ui import ConnectionDialog
from rsr.worksheet.editor import Editor
from rsr.worksheet.results import Results
from rsr.worksheet.sidebar import Sidebar


class Worksheet(Gtk.VPaned):

    __gsignals__ = {
        'connection-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'active-query-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, win):
        super(Worksheet, self).__init__()
        self.win = win
        self.app = win.app
        self.connection = None
        self.editor = Editor(self)
        self.results = Results(self)
        self.sidebar = Sidebar(self)

        sw = Gtk.ScrolledWindow()
        sw.add(self.editor)

        paned = Gtk.HPaned()
        paned.add1(sw)
        paned.add2(self.sidebar)
        self._paned_sidebar = paned
        width = self.win.get_allocation().width - 300
        paned.set_position(width)
        self.add1(paned)

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
            'sidebar_width': self._paned_sidebar.get_position(),
            'connection': conn_key,
            'cursor': self.editor.get_cursor_position(),
        }

    def restore_state(self, state):
        self.editor.set_text(state['content'])
        self.set_position(state.get('split_pos', 0))
        width = self.win.get_allocation().width - 300
        self._paned_sidebar.set_position(state.get('sidebar_width', width))
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

    def assume_password(self):
        if self.connection is None:
            return False
        result = True
        if self.connection.requires_password():
            result = False
            dlg = Gtk.Dialog('Enter password', self.win,
                             Gtk.DialogFlags.DESTROY_WITH_PARENT |
                             Gtk.DialogFlags.MODAL,
                             use_header_bar=True)
            dlg.add_button('_Cancel', Gtk.ResponseType.CANCEL)
            dlg.add_button('_Ok', Gtk.ResponseType.OK)
            dlg.set_default_response(Gtk.ResponseType.OK)
            box = dlg.get_content_area()
            box.set_border_width(12)
            box.set_spacing(6)
            lbl = Gtk.Label()
            lbl.set_markup('Password required for <b>{}</b>.'.format(
                GObject.markup_escape_text(
                    self.connection.get_label())))
            box.pack_start(lbl, True, True, 0)
            entry = Gtk.Entry()
            entry.set_visibility(False)
            entry.set_invisible_char('*')
            entry.connect(
                'activate', lambda *a: dlg.response(Gtk.ResponseType.OK))
            box.pack_start(entry, True, True, 0)
            box.show_all()
            if dlg.run() == Gtk.ResponseType.OK:
                self.connection.set_session_password(entry.get_text())
                result = True
            dlg.destroy()
        return result

    def open_connection(self):
        if not self.assume_connection():
            return
        if not self.assume_password():
            return
        self.connection.request_open()

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
        if not self.assume_password():
            return
        query = Query(stmt)
        self.results.set_query(query)
        self.emit('active-query-changed')
        self.connection.run_query(query)
