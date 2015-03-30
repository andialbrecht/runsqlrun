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
        self.set_spacing(6)

        switcher = Gtk.StackSwitcher()
        switcher.props.halign = Gtk.Align.CENTER
        self.pack_start(switcher, False, False, 0)

        stack = Gtk.Stack()
        stack.add_titled(Gtk.Label('Introspection'), 'schema', 'DB Schema')
        stack.add_titled(Gtk.Label('Context'), 'context', 'Context')
        self.pack_start(stack, True, True, 0)

        switcher.set_stack(stack)
        self.show_all()

    def toggle(self):
        if self.is_visible():
            self.hide()
        else:
            self.show()
