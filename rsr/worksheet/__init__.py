from gi.repository import Gtk, GtkSource, Pango

from rsr.connections.query import Query
from rsr.connections.ui import ConnectionDialog
from rsr.worksheet.results import Results


class Editor(GtkSource.View):

    def __init__(self):
        super(Editor, self).__init__()
        self.buffer = GtkSource.Buffer()
        lang_manager = GtkSource.LanguageManager()
        self.buffer.set_language(lang_manager.get_language('sql'))
        self.set_buffer(self.buffer)
        # TODO: Move to configuration
        font_desc = Pango.FontDescription.from_string('Ubuntu Mono 16')
        self.modify_font(font_desc)

    def get_text(self):
        buf = self.get_buffer()
        return buf.get_text(*buf.get_bounds(), include_hidden_chars=False)

    def set_text(self, text):
        self.get_buffer().set_text(text)


class Worksheet(Gtk.VPaned):

    def __init__(self, win):
        super(Worksheet, self).__init__()
        self.win = win
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
        return {
            'content': self.editor.get_text(),
            'split_pos': self.get_position()
        }

    def restore_state(self, state):
        self.editor.set_text(state['content'])
        self.set_position(state.get('split_pos', 0))

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

    def run_query(self):
        if not self.assume_connection():
            return
        query = Query(self.editor.get_text())
        self.results.set_query(query)
        self.connection.run_query(query)
