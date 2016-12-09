import re
from functools import partial

from gi.repository import Gtk

from rsr.worksheet import Worksheet


class DocViewer(Gtk.Notebook):

    def __init__(self, win):
        super(DocViewer, self).__init__()
        self.win = win
        self.set_scrollable(True)

        self.connect('page-added', self.on_page_count_changed)
        self.connect('page-removed', self.on_page_count_changed)

    def on_page_count_changed(self, *args):
        enabled = self.get_n_pages() != 0
        for name in self.win.app.action_groups['editor'].list_actions():
            self.win.app.lookup_action(name).set_enabled(enabled)

        # Somehow GTK seems to change colors of child widgets if
        # tabs are shown or not.
        # self.set_show_tabs(self.get_n_pages() > 1)

    def save_state(self):
        state = {
            'worksheets': [],
            'current': self.get_current_page()
        }
        for i in range(self.get_n_pages()):
            page = self.get_nth_page(i)
            state['worksheets'].append(page.save_state())
        return state

    def restore_state(self, state):
        for data in state['worksheets']:
            worksheet = self.add_worksheet()
            worksheet.restore_state(data)
        self.set_current_page(state['current'])
        if self.get_n_pages() == 0:
            worksheet = self.add_worksheet()
            worksheet.editor.set_text(WELCOME_MSG)

    def add_worksheet(self):
        worksheet = Worksheet(self.win)
        self.append_page(worksheet, self._get_notebook_label(worksheet))
        worksheet.show_all()
        self.set_current_page(self.get_n_pages() - 1)
        worksheet.editor.grab_focus()
        return worksheet

    def _get_notebook_label(self, worksheet):
        # Label from worksheet
        label = worksheet.get_tab_label()
        # FIXME: This should be handled by the editor, not the docviewer.
        worksheet.editor.buffer.connect(
            'changed', partial(self.on_buffer_changed, label))
        # Close button
        img = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        _, w, h = Gtk.IconSize.lookup(Gtk.IconSize.MENU)
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_focus_on_click(False)
        btn.add(img)
        btn.connect(
            'clicked', lambda b, w: self.remove_worksheet(w), worksheet)
        # Put it together
        hbox = Gtk.HBox()
        hbox.pack_start(label, True, True, 3)
        hbox.pack_end(btn, False, False, 0)
        hbox.show_all()
        return hbox

    def on_buffer_changed(self, label, buffer):
        txt = buffer.get_text(*buffer.get_bounds(), include_hidden_chars=False)
        txt = re.sub(r'[ \r\n\t]+', ' ', txt).strip()
        txt_stripped = txt[:20].strip()
        if len(txt_stripped) < len(txt):
            txt_stripped += '…'
        if not txt_stripped:
            txt_stripped = 'SQL Editor'
        label.set_text(txt_stripped)

    def close_current_editor(self):
        self.remove_page(self.get_current_page())

    def get_current_editor(self):
        return self.get_nth_page(self.get_current_page())

    def switch_to_editor(self, num):
        if num > self.get_n_pages() or num < 0:
            return
        self.set_current_page(num - 1)

    def remove_worksheet(self, worksheet):
        idx = self.page_num(worksheet)
        if idx == -1:
            return
        self.remove_page(idx)


WELCOME_MSG = """/* Start typing your SQL here.

   Some helpful shortcuts to get started:

        Ctrl+N  Open new SQL Editor
    Ctrl+Enter  Run statement at cursor
            F9  Choose or add a database connection
           F10  Open db connection without executing a query
                This is needed to have completions for database objects.
           F11  Disconnect from database and revoke assignment from editor.
        Ctrl+W  Close current SQL editor
        Ctrl+Q  Close RunSQLRun

   Any feedback is highly appreciated!

   Issue tracker: https://github.com/andialbrecht/runsqlrun

   Have fun!

*/
"""
