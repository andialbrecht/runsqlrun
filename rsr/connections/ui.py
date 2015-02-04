import time

from gi.repository import Gtk, GObject, Gio


class ConnectionDialog(Gtk.Dialog):

    def __init__(self, win, title='Choose Connection',
                 show_header_buttons=True):
        self.win = win
        self.app = win.app
        super(ConnectionDialog, self).__init__(
            title, win,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            use_header_bar=True)

        # Response buttons
        if show_header_buttons:
            self._btn_cancel = self.add_button('_Cancel',
                                               Gtk.ResponseType.CANCEL)
            self._btn_choose = self.add_button('_Connect', Gtk.ResponseType.OK)
            self.set_default_response(Gtk.ResponseType.OK)
        else:
            self._btn_choose = self._btn_cancel = None

        hb = self.get_header_bar()
        self._btn_form_back = Gtk.Button()
        icon = Gio.ThemedIcon(name='back')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self._btn_form_back.add(image)
        self._btn_form_back.connect('clicked', self.on_show_list)
        hb.pack_start(self._btn_form_back)

        self.builder = Gtk.Builder()
        self.builder.add_from_resource('/org/runsqlrun/connection_dialog.ui')

        content_area = self.get_content_area()
        content_area.set_border_width(12)
        content_area.set_spacing(6)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

        page_list = self._setup_list_page(self.builder)
        stack.add_named(page_list, 'list')

        page_form = self._setup_form_page(self.builder)
        self._edit_key = None
        stack.add_named(page_form, 'form')

        content_area.pack_start(stack, True, True, 0)

        self.stack = stack

        self.show_all()
        self._btn_form_back.hide()

    def _setup_list_page(self, builder):
        page = builder.get_object('page_list')

        store = Gtk.ListStore(str, str, str)
        store.set_sort_column_id(2, Gtk.SortType.ASCENDING)
        self.conn_list = builder.get_object('conn_list')
        column = Gtk.TreeViewColumn(
            'Connection', Gtk.CellRendererText(), markup=1)
        self.conn_list.append_column(column)
        self.conn_list.set_model(store)
        sel = self.conn_list.get_selection()
        sel.connect('changed', self.on_selected_conn_changed)
        self.refresh_connection_list()
        self.conn_list.connect('row-activated', self.on_connlist_row_activated)

        btn_add = builder.get_object('btn_add')
        btn_add.connect('clicked', self.on_add_connection)

        btn_del = builder.get_object('btn_delete')
        btn_del.connect('clicked', self.on_delete_connection)

        btn_edit = builder.get_object('btn_edit')
        btn_edit.connect('clicked', self.on_edit_connection)

        return page

    def refresh_connection_list(self, key=None):
        store = self.conn_list.get_model()
        store.clear()
        for conn in self.app.connection_manager.get_connections():
            lbl = GObject.markup_escape_text(conn.get_label())
            if conn.config.get('description'):
                lbl += '\n<small>{}</small>'.format(
                    GObject.markup_escape_text(conn.config['description']))
            store.append([conn.key, lbl, conn.get_label()])
        if key is not None:
            iter_ = store.get_iter_first()
            while iter_:
                if store.get_value(iter_, 0) == key:
                    selection = self.conn_list.get_selection()
                    selection.select_iter(iter_)
                    break
                iter_ = store.iter_next(iter_)

    def _setup_form_page(self, builder):
        page = builder.get_object('page_form')

        store = Gtk.ListStore(str, str)
        driver_combo = builder.get_object('driver_combo')
        driver_combo.set_id_column(0)
        driver_combo.set_entry_text_column(1)
        driver_combo.set_model(store)
        for spec in self.app.connection_manager.get_available_drivers():
            store.append([spec.key, spec.name])

        builder.get_object('name').connect('changed', self._validate_name)
        builder.get_object('driver_combo').connect('changed',
                                                   self._validate_driver)

        btn_test = builder.get_object('btn_test')
        btn_test.set_sensitive(False)
        btn_test.connect('clicked', self.on_test_connection)

        btn_save = builder.get_object('btn_save')
        btn_save.set_sensitive(False)
        btn_save.connect('clicked', self.on_save_connection)

        return page

    def _validate_name(self, entry, *args):
        if not entry.get_text().strip():
            entry.set_property('secondary-icon-stock', 'gtk-dialog-info')
        else:
            entry.set_property('secondary-icon-stock', None)

    def _validate_driver(self, combo, *args):
        entry = self.builder.get_object('driver_combo_entry')
        self.builder.get_object('btn_test').set_sensitive(
            bool(combo.get_active_id()))
        self.builder.get_object('btn_save').set_sensitive(
            bool(combo.get_active_id()))
        if not combo.get_active_id():
            entry.set_property('secondary-icon-stock', 'gtk-dialog-warning')
        else:
            entry.set_property('secondary-icon-stock', None)

    def on_test_connection(self, *args):
        data = self.serialize_form()
        result = self.app.connection_manager.test_connection(data)
        if result is True:
            lbl = '✓ Yepp, that works.'
        else:
            lbl = '✗ {}'.format(result)
        self.builder.get_object('lbl_test_result').set_text(lbl)

    def on_save_connection(self, *args):
        data = self.serialize_form()
        if self._edit_key is not None:
            data['key'] = self._edit_key
        key = self.app.connection_manager.update_connection(data)
        self.refresh_connection_list(key)
        self.on_show_list()
        self.conn_list.grab_focus()

    def on_edit_connection(self, *args):
        conn = self.get_connection()
        config = conn.config.copy()
        if conn.has_session_password():
            config.pop('password', None)
        self._update_form(conn.key, config)
        self.on_show_form()

    def on_add_connection(self, *args):
        self._update_form(None, {})
        self.on_show_form()

    def _update_form(self, key, config):
        for field in ('name', 'description', 'host', 'port',
                      'username', 'password', 'db'):
            widget = self.builder.get_object(field)
            widget.set_text(str(config.get(field, '')))
        self.builder.get_object('driver_combo').set_active_id(
            config.get('driver', None))
        self.builder.get_object('cmd_ssh').get_buffer().set_text(
            config.get('cmd_ssh', ''))
        self._edit_key = key

    def on_delete_connection(self, *args):
        conn = self.get_connection()
        dlg = Gtk.MessageDialog(self,
                                Gtk.DialogFlags.DESTROY_WITH_PARENT |
                                Gtk.DialogFlags.MODAL,
                                Gtk.MessageType.WARNING,
                                Gtk.ButtonsType.OK_CANCEL)
        dlg.set_title('Delete Connection')
        dlg.set_markup('Delete connection <b>{}</b>?'.format(
                       GObject.markup_escape_text(conn.get_label())))
        dlg.format_secondary_text('There\'s no undo.')
        if dlg.run() == Gtk.ResponseType.OK:
            self.app.connection_manager.delete_connection(conn.key)
            self.refresh_connection_list()
            self.conn_list.grab_focus()
        dlg.destroy()

    def serialize_form(self):
        data = {}
        for field in ('name', 'description', 'host', 'port',
                      'username', 'password', 'db'):
            widget = self.builder.get_object(field)
            value = widget.get_text().strip()
            if value:
                if field == 'port':
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                data[field] = value
        data['driver'] = self.builder.get_object(
            'driver_combo').get_active_id()
        buf = self.builder.get_object('cmd_ssh').get_buffer()
        data['cmd_ssh'] = buf.get_text(*buf.get_bounds(),
                                       include_hidden_chars=False)
        return data

    def on_show_form(self, *args):
        self.stack.set_visible_child_name('form')
        if self._btn_choose is not None:
            self._btn_choose.set_sensitive(False)
            self._btn_cancel.hide()
        self._btn_form_back.show()
        self.builder.get_object('name').grab_focus()

    def on_show_list(self, *args):
        self.stack.set_visible_child_name('list')
        if self._btn_choose is not None:
            self._btn_choose.set_sensitive(True)
            self._btn_cancel.show()
        self._btn_form_back.hide()

    def on_connlist_row_activated(self, treeview, path, column):
        self.response(Gtk.ResponseType.OK)

    def on_selected_conn_changed(self, selection):
        enabled = selection.count_selected_rows() != 0
        if self._btn_choose is not None:
            self._btn_choose.set_sensitive(enabled)
        self.builder.get_object('btn_delete').set_sensitive(enabled)
        self.builder.get_object('btn_edit').set_sensitive(enabled)

    def get_connection(self):
        selection = self.conn_list.get_selection()
        model, rows = selection.get_selected_rows()
        if not rows:
            return None
        key = model.get_value(model.get_iter(rows[0]), 0)
        return self.app.connection_manager.get_connection(key)


class ConnectionIndicator(Gtk.Box):

    def __init__(self, win):
        super(ConnectionIndicator, self).__init__()
        self.win = win

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(6)
        self.lbl_conn = Gtk.Label()
        self.lbl_query = Gtk.Label()
        self.pack_start(self.lbl_query, True, False, 0)
        self.pack_start(self.lbl_conn, True, False, 0)

        self._editor = None
        self._sig_conn_changed = None
        self._sig_query_changed = None
        self._sig_connstate_changed = None
        self.win.docview.connect('switch-page', self.on_editor_changed)
        self.win.docview.connect('page-removed', self.on_page_removed)

    def on_page_removed(self, docview, *args):
        if docview.get_n_pages() == 0:
            self.on_editor_changed(docview, None, None)

    def on_editor_changed(self, docview, page, num, *args):
        editor = page
        if self._editor is not None:
            self._editor.disconnect(self._sig_conn_changed)
            self._editor.disconnect(self._sig_query_changed)
            self._editor = None
            self._sig_conn_changed = None
            self._sig_query_changed = None
        if editor is not None:
            self._editor = editor
            self._sig_conn_changed = editor.connect(
                'connection-changed', self.on_connection_changed)
            self._sig_query_changed = editor.connect(
                'active-query-changed', self.on_query_changed)
        self.on_connection_changed(editor)
        self.on_query_changed(editor)

    def on_connection_changed(self, editor):
        if editor is None or not editor.connection:
            self.lbl_conn.set_text('[Not connected]')
            self.win.headerbar.set_subtitle('Database Query Tool')
        else:
            lbl = editor.connection.get_label()
            if editor.connection.is_open():
                state = Gtk.StateType.NORMAL
            else:
                state = Gtk.StateType.INSENSITIVE
                lbl += ' - Not connected'
            self.lbl_conn.set_state(state)
            self.lbl_conn.set_text(lbl)
            subtitle = editor.connection.get_label()
            if editor.connection.config.get('description'):
                subtitle += ' · {}'.format(
                    editor.connection.config['description'])
            self.win.headerbar.set_subtitle(subtitle)
            editor.connection.connect(
                'state-changed', lambda *a: self.on_connection_changed(editor))

    def on_query_changed(self, editor):
        if editor is None:
            self.lbl_query.set_text('')
            return
        query = editor.get_active_query()
        if query is None or query.failed:
            self.lbl_query.set_text('')
        elif query.finished:
            self.lbl_query.set_text(query.get_result_summary())
        elif query.pending:
            self.lbl_query.set_text('Pending...')
            GObject.timeout_add(10, self.on_query_changed, self._editor)
        else:
            duration = time.time() - query.start_time
            self.lbl_query.set_text('Running for %.3f seconds' % duration)
            GObject.timeout_add(10, self.on_query_changed, self._editor)
