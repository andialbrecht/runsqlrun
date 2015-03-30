from gi.repository import Gtk, Pango


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

        stack.add_titled(box, 'objects', 'Object list')

        # Set main widget
        self.widget = stack

        # Setup signals
        worksheet.connect('connection-changed', self.on_connection_changed)
        self.on_connection_changed(worksheet)

    def on_connection_changed(self, worksheet):
        # Update signal handlers and internal state if needed
        if worksheet.connection != self.conn:
            self.store.clear()
            if self.sig_schema is not None:
                self.conn.schema.disconnect(self.sig_schema)
                self.sig_schema = None
            self.conn = worksheet.connection
            if self.conn is not None:
                self.conn.schema.connect('refreshed', self.on_schema_refreshed)
                self.on_schema_refreshed(self.conn.schema)
        else:
            return

        # Update stack view to display correct page
        if self.conn is None:
            self.widget.set_visible_child_name('please')
        else:
            self.widget.set_visible_child_name('objects')

    def on_schema_refreshed(self, schema):
        self.store.clear()
        for item in schema.get_objects():
            self.store.append([item.name])

    def get_widget(self):
        return self.widget
