from gi.repository import Gtk, Pango, GObject

from rsr.utils import regex_fuzzy_match


class Sidebar(Gtk.Box):

    def __init__(self, worksheet):
        self.worksheet = worksheet

        super(Sidebar, self).__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_margin_top(12)
        self.set_margin_left(12)
        self.set_margin_right(12)
        self.set_margin_bottom(12)
        self.set_spacing(12)

        switcher = Gtk.StackSwitcher()
        switcher.props.halign = Gtk.Align.CENTER
        self.pack_start(switcher, False, False, 0)

        stack = Gtk.Stack()
        self.introspection = IntrospectionItem(worksheet)
        stack.add_titled(self.introspection.get_widget(),
                         self.introspection.name, self.introspection.title)
        stack.add_titled(Gtk.Label('Context'), 'context', 'Context')
        self.pack_start(stack, True, True, 0)

        switcher.set_stack(stack)
        self.show_all()

    def toggle(self):
        if self.is_visible():
            self.hide()
        else:
            self.show()


class SidebarItem:
    name = None
    title = None

    def __init__(self, worksheet):
        self.worksheet = worksheet

    def get_widget(self):
        raise NotImplementedError()


class IntrospectionItem(SidebarItem):
    name = 'schema'
    title = 'DB Schema'

    def __init__(self, worksheet):
        super(IntrospectionItem, self).__init__(worksheet)
        self.conn = None
        self.sig_schema = None
        self.sig_conn_state = None

        l = Gtk.Label()
        self.col_insensitive = l.get_style_context().get_color(
            Gtk.StateFlags.INSENSITIVE).to_color().to_string()

        # The stack
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)

        # Page 1: Please connect
        lbl = Gtk.Label(
            'No connection, no fun.\n\n'
            'Connect to a database (F10) and see database schema here.')
        lbl.set_valign(Gtk.Align.START)
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD)
        stack.add_titled(lbl, 'please', 'Please connect')

        # Page 2: Object list
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_spacing(6)

        # Search entry
        entry = Gtk.Entry()
        self.entry = entry
        entry.set_placeholder_text('Search (Alt+Shift+F)')
        box.pack_start(entry, False, False, 0)

        # Tree view
        tree = Gtk.TreeView()
        self.object_list = tree
        tree.set_headers_visible(False)
        model_filter = self._create_object_model([])
        tree.set_model(model_filter)
        col = Gtk.TreeViewColumn('Object', Gtk.CellRendererText(), markup=2)
        tree.append_column(col)
        sw = Gtk.ScrolledWindow()
        sw.add(tree)
        box.pack_start(sw, True, True, 0)
        tree.connect('row-activated', self.on_object_row_activated)

        entry.connect('changed', lambda e: tree.get_model().refilter())

        stack.add_titled(box, 'objects', 'Object list')

        # Page 3: Object details
        self.object_details = ObjectDetails(self)
        stack.add_titled(self.object_details, 'object-details', 'Details')

        # Set main widget
        self.widget = stack

        # Setup signals
        worksheet.connect('connection-changed', self.on_connection_changed)
        self.on_connection_changed(worksheet)

    def _create_object_model(self, data):
        # Object list
        store = Gtk.ListStore(object, str, str)
        store.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        if data:
            list(map(store.append, data))

        # Setup filtering
        def filter_func(model, iter_, data):
            term = self.entry.get_text().strip()
            if not term:
                return True
            match = regex_fuzzy_match(term, model[iter_][0].name)
            return match is not None
        model_filter = store.filter_new()
        model_filter.set_visible_func(filter_func)
        return model_filter

    def on_connection_changed(self, worksheet):
        # Update signal handlers and internal state if needed
        if worksheet.connection != self.conn:
            self.object_list.get_model().get_model().clear()
            # TODO: Write a helper that connects and disconnects automagically
            #   storing a reference to the sighandler ID on its own.
            #   Something like utils.connect(self, self.conn.schema,
            #   'refreshed', callback), utils.disconnect_all(self,
            #   self.conn.schema) or disconnect by callback function...?
            #   This reference saving in self.sig_* is annoying.
            if self.sig_schema is not None:
                self.conn.schema.disconnect(self.sig_schema)
                self.sig_schema = None
            if self.sig_conn_state is not None:
                self.conn.disconnect(self.sig_conn_state)
                self.sig_conn_state = None
            self.conn = worksheet.connection
            if self.conn is not None:
                self.conn.connect('state-changed', self.on_connstate_changed)
                self.conn.schema.connect('refreshed', self.on_schema_refreshed)
                self.on_schema_refreshed(self.conn.schema)
            self.on_connstate_changed(self.conn)
        else:
            return

    def on_connstate_changed(self, conn):
        # Update stack view to display correct page
        if conn is None or not conn.is_open():
            self.widget.set_visible_child_name('please')
        else:
            self.widget.set_visible_child_name('objects')

    def on_schema_refreshed(self, schema):
        # Prepare data for list store
        data = []
        for item in schema.get_objects():
            markup = '{}\n<span font-size="small" color="{}">{}'.format(
                *list(map(GObject.markup_escape_text, [
                    item.name, self.col_insensitive, item.get_type_name()]))
            )
            if item.description:
                markup += ': {}'.format(
                    GObject.markup_escape_text(item.description))
            markup += '</span>'
            data.append([item, item.name, markup])
        # The model is re-created on each refresh. Otherwise GTK reports
        # some strange errors about TreeModelFilter and ListStore not in
        # sync. The app seems to run fine anyway, but it bloats the terminal
        # with Gtk Critical error messages.
        # This seems to happen, when the ListStore is changed after the
        # model filter is created.
        model_filter = self._create_object_model(data)
        # assign new model to tree view
        self.object_list.set_model(model_filter)
        # scroll to first entry
        store = model_filter.get_model()
        iter_ = store.get_iter_first()
        if iter_ is not None:
            self.object_list.scroll_to_cell(store.get_path(iter_), None,
                                            False, 0, 0)

    def on_object_row_activated(self, treeview, path, column):
        model = treeview.get_model()
        obj = model.get_value(model.get_iter(path), 0)
        self.object_details.set_object(obj)
        self.widget.set_visible_child_name('object-details')
        self.object_details.btn_back.grab_focus()

    def get_widget(self):
        return self.widget

    def search(self):
        if self.conn is None or not self.conn.is_open():
            return
        self.widget.set_visible_child_name('objects')
        self.entry.grab_focus()


class ObjectDetails(Gtk.Box):

    def __init__(self, introspection):
        super(ObjectDetails, self).__init__()
        self.introspection = introspection
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(6)
        self.lbl_name = Gtk.Label()
        self.lbl_name.set_valign(Gtk.Align.START)
        self.lbl_description = Gtk.Label()
        self.lbl_description.set_valign(Gtk.Align.START)
        self.btn_back = Gtk.Button('Back')
        self.btn_back.connect('activate', self.on_back_button_activated)
        self.pack_start(self.btn_back, False, False, 0)
        self.pack_start(self.lbl_name, False, False, 0)
        self.pack_start(self.lbl_description, False, False, 0)

    def on_back_button_activated(self, btn):
        self.introspection.widget.set_visible_child_name('objects')
        self.introspection.object_list.grab_focus()

    def set_object(self, obj):
        self.lbl_name.set_markup('{}: <b>{}</b>'.format(
            GObject.markup_escape_text(obj.get_type_name()),
            GObject.markup_escape_text(obj.name)))
        self.lbl_description.set_text(obj.description or '')
