from gi.repository import Gio, GLib, Gtk

from rsr.headerbar import HeaderBar
from rsr.docview import DocViewer
from rsr.commands import commands


class MainWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__(application=app, title='RunSQLRun')
        self.app = app
        self.settings = Gio.Settings.new('org.runsqlrun')

        self.set_default_size(800, 600)

        self.set_titlebar(HeaderBar(self))

        self.docview = DocViewer(self)
        self.statusbar = Gtk.Statusbar()
        self.statusbar.set_margin_top(0)
        self.statusbar.set_margin_bottom(0)
        self.statusbar.push(100, 'Ready when you are')

        vbox = Gtk.VBox()
        vbox.pack_start(self.docview, True, True, 0)
        vbox.pack_start(self.statusbar, False, False, 0)
        self.add(vbox)
        # TODO: Statusbar

        # save and restore window settings
        if self.settings.get_value('window-maximized'):
            self.maximize()
        size_setting = self.settings.get_value('window-size')
        if isinstance(size_setting[0], int) \
           and isinstance(size_setting[1], int):
            self.resize(size_setting[0], size_setting[1])
        position_setting = self.settings.get_value('window-position')
        if len(position_setting) == 2 \
           and isinstance(position_setting[0], int) \
           and isinstance(position_setting[1], int):
            self.move(position_setting[0], position_setting[1])
        self.connect('window-state-event', self.on_window_state_event)
        self.connect('configure-event', self.on_configure_event)

        # Actions
        self._setup_actions()

        self.show_all()

    def _setup_actions(self):
        return

    def on_configure_event(self, widget, event):
        size = widget.get_size()
        self.settings.set_value(
            'window-size', GLib.Variant('ai', [size[0], size[1]]))

        position = widget.get_position()
        self.settings.set_value(
            'window-position', GLib.Variant('ai', [position[0], position[1]]))

    def on_window_state_event(self, widget, event):
        self.settings.set_boolean(
            'window-maximized',
            'GDK_WINDOW_STATE_MAXIMIZED' in event.new_window_state.value_names)

    def save_state(self):
        state = {'docview': self.docview.save_state()}
        return state

    def restore_state(self, state):
        self.docview.restore_state(state['docview'])
