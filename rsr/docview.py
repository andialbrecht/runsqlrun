import re
from functools import partial

from gi.repository import Gtk

from rsr.worksheet import Worksheet


class DocViewer(Gtk.Notebook):

    def __init__(self, win):
        super(DocViewer, self).__init__()
        self.win = win

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

    def add_worksheet(self):
        worksheet = Worksheet(self.win)
        label = worksheet.get_tab_label()
        self.append_page(worksheet, label)
        worksheet.show_all()
        self.set_current_page(self.get_n_pages() - 1)
        worksheet.editor.grab_focus()
        worksheet.editor.buffer.connect(
            'changed', partial(self.on_buffer_changed, label))
        return worksheet

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
