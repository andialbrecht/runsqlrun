from gi.repository import Gtk, GLib, Pango


class StatementListItem(Gtk.ListBoxRow):

    def __init__(self, statement):
        super(StatementListItem, self).__init__()
        self.statement = statement
        lbl_text = statement['statement'].replace('\r', ' ')
        lbl_text = lbl_text.replace('\n', ' ').strip()
        lbl = Gtk.Label(lbl_text)
        lbl.set_xalign(0)
        lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        lbl.set_line_wrap(False)
        self.add(lbl)


class EditorContext(Gtk.Box):

    def __init__(self, worksheet):
        super(EditorContext, self).__init__(
            orientation=Gtk.Orientation.VERTICAL)
        self.worksheet = worksheet

        self.set_size_request(200, 200)
        self.set_border_width(6)
        self.set_spacing(6)

        self.lbl_conn = Gtk.Label('')
        self.lbl_conn.set_xalign(0)
        self.pack_start(self.lbl_conn, False, True, 0)

        lbl = Gtk.Label()
        lbl.set_markup('<small>Statements</small>')
        lbl.set_xalign(0)
        self.pack_start(lbl, False, False, 0)

        self.lst_statements = Gtk.ListBox()
        self.pack_start(self.lst_statements, True, True, 0)
        self.lst_statements.connect(
            'row-activated', self.on_statement_row_activated)

        self.worksheet.connect(
            'connection-changed', self.on_connection_changed)
        self.on_connection_changed(worksheet)

        self.worksheet.editor.connect(
            'statements-changed', self.on_statements_changed)

    def on_connection_changed(self, worksheet):
        markup = '<small>Connected to</small>\n'
        if worksheet.connection is not None:
            conn = worksheet.connection.get_label()
        else:
            conn = 'Not connected.'
        markup += '<b>{}</b>'.format(GLib.markup_escape_text(conn))
        self.lbl_conn.set_markup(markup)

    def on_statements_changed(self, editor):
        for child in self.lst_statements.get_children():
            self.lst_statements.remove(child)
        for statement in editor.get_statements():
            self.lst_statements.add(StatementListItem(statement))
        self.lst_statements.show_all()

    def on_statement_row_activated(self, listbox, row):
        self.worksheet.editor.set_cursor_position(row.statement['start'])
        self.worksheet.editor.grab_focus()
