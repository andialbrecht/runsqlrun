from gi.repository import Gtk


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
        item1 = IntrospectionItem(worksheet)
        stack.add_titled(item1.get_widget(), item1.name, item1.title)
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

        # UI
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_spacing(6)

        # Search entry
        entry = Gtk.Entry()
        entry.set_placeholder_text('Search (Ctrl+/)')
        box.pack_start(entry, False, False, 0)

        # Object list
        store = Gtk.ListStore(str)
        store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.store = store
        tree = Gtk.TreeView()
        tree.set_model(store)
        col = Gtk.TreeViewColumn('Object', Gtk.CellRendererText(), markup=0)
        tree.append_column(col)
        sw = Gtk.ScrolledWindow()
        sw.add(tree)
        box.pack_start(sw, True, True, 0)

        # Set main widget
        self.widget = box

        # Setup signals
        worksheet.connect('connection-changed', self.on_connection_changed)
        self.on_connection_changed(worksheet)

    def on_connection_changed(self, worksheet):
        if worksheet.connection != self.conn:
            self.store.clear()
            if self.sig_schema is not None:
                self.conn.schema.disconnect(self.sig_schema)
                self.sig_schema = None
            self.conn = worksheet.connection
            if self.conn is not None:
                self.conn.schema.connect('refreshed', self.on_schema_refreshed)
                self.on_schema_refreshed(self.conn.schema)

    def on_schema_refreshed(self, schema):
        self.store.clear()
        for item in schema.get_objects():
            self.store.append([item.name])

    def get_widget(self):
        return self.widget
