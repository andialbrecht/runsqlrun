from gi.repository import Gtk, GLib, Pango


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

        self.lst_statements = Gtk.TreeView()
        renderer = Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.MIDDLE)
        column = Gtk.TreeViewColumn("Statements", renderer, text=0)
        self.lst_statements.append_column(column)
        self.lst_statements_model = Gtk.ListStore(str)
        self.lst_statements.set_model(self.lst_statements_model)
        self.pack_start(self.lst_statements, True, True, 0)
        self.lst_statements.connect(
            'row-activated', self.on_statement_row_activated)

        self.browser = Gtk.TreeView()
        renderer = Gtk.CellRendererText(
            ellipsize=Pango.EllipsizeMode.MIDDLE)
        column = Gtk.TreeViewColumn("Tables / Views", renderer, text=0)
        self.browser.append_column(column)
        self.browser_model = Gtk.ListStore(str)
        self.browser.set_model(self.browser_model)
        self.pack_start(self.browser, True, True, 0)

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

        # update schema
        self.browser_model.clear()
        if worksheet.connection:
            worksheet.connection.schema.connect(
                'changed', self._update_browser)

    def _update_browser(self, schema):
        objects = sorted(schema.get_objects(types=['table', 'view']),
                         key=lambda i: i.name)
        for item in objects:
            self.browser_model.append([item.name])

    def on_statements_changed(self, editor):
        self.lst_statements_model.clear()
        for statement in editor.get_statements():
            sql = statement['statement'].replace('\r', ' ').replace('\n', ' ')
            self.lst_statements_model.append([sql.strip()])

    def on_statement_row_activated(self, listbox, row):
        self.worksheet.editor.set_cursor_position(row.statement['start'])
        self.worksheet.editor.grab_focus()
