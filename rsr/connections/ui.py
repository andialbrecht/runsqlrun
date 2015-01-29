from gi.repository import Gtk


class ConnectionDialog(Gtk.Dialog):

    def __init__(self, win):
        self.win = win
        self.app = win.app
        super(ConnectionDialog, self).__init__(
            'Choose Connection', win,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)

        self.add_button('_Cancel', Gtk.ResponseType.CANCEL)
        self._btn_choose = self.add_button('_Connect', Gtk.ResponseType.OK)

        builder = Gtk.Builder()
        builder.add_from_resource('/org/runsqlrun/connection_dialog.ui')

        content_area = self.get_content_area()
        content_area.set_border_width(12)
        content_area.set_spacing(6)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)

        page_list = self._setup_list_page(builder)
        btn_add = builder.get_object('btn_add')
        btn_add.connect('clicked', self.on_show_form)
        stack.add_named(page_list, 'list')

        page_form = builder.get_object('page_form')
        stack.add_named(page_form, 'form')

        content_area.pack_start(stack, True, True, 0)

        self.stack = stack

        self.show_all()

    def _setup_list_page(self, builder):
        page = builder.get_object('page_list')
        store = Gtk.ListStore(str, str)
        for conn in self.app.connection_manager.get_connections():
            store.append([conn.key, conn.get_label()])
        self.conn_list = builder.get_object('conn_list')
        column = Gtk.TreeViewColumn(
            'Connection', Gtk.CellRendererText(), text=1)
        self.conn_list.append_column(column)
        self.conn_list.set_model(store)
        self.conn_list.connect('row-activated', self.on_connlist_row_activated)
        return page

    def on_show_form(self, *args):
        self.stack.set_visible_child_name('form')
        self._btn_choose.set_sensitive(False)

    def on_connlist_row_activated(self, treeview, path, column):
        self.response(Gtk.ResponseType.OK)

    def get_connection(self):
        selection = self.conn_list.get_selection()
        model, rows = selection.get_selected_rows()
        if not rows:
            return None
        key = model.get_value(model.get_iter(rows[0]), 0)
        return self.app.connection_manager.get_connection(key)


class ConnectionIndicator(Gtk.Label):

    def __init__(self, win):
        super(ConnectionIndicator, self).__init__()
        self.win = win
        self._editor = None
        self._sig_conn_changed = None
        self.win.docview.connect('switch-page', self.on_editor_changed)
        self.win.docview.connect('page-removed', self.on_page_removed)

    def on_page_removed(self, docview, *args):
        if docview.get_n_pages() == 0:
            self.on_editor_changed(docview, None, None)

    def on_editor_changed(self, docview, page, num, *args):
        editor = page
        if self._editor is not None:
            self._editor.disconnect(self._sig_conn_changed)
            self._editor = None
            self._sig_conn_changed = None
        if editor is not None:
            self._sig_conn_changed = editor.connect(
                'connection-changed', self.on_connection_changed)
            self._editor = editor
        self.on_connection_changed(editor)

    def on_connection_changed(self, editor):
        if editor is None or not editor.connection:
            self.set_text('[Not connected]')
            self.win.headerbar.set_subtitle('Database Query Tool')
        else:
            self.set_text(editor.connection.key)
            self.win.headerbar.set_subtitle(editor.connection.key)
