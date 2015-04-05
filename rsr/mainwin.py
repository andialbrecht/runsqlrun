from gi.repository import Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf

from rsr.connections.ui import ConnectionIndicator
from rsr.docview import DocViewer
from rsr.headerbar import HeaderBar


class MainWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__(application=app, title='RunSQLRun')
        self.app = app

        self.set_default_size(800, 600)
        self.set_icon(Pixbuf.new_from_resource(
            '/org/runsqlrun/icons/runsqlrun.svg'))

        self.headerbar = HeaderBar(self)
        self.set_titlebar(self.headerbar)

        self.docview = DocViewer(self)
        self.statusbar = Gtk.Statusbar()
        self.statusbar.set_margin_top(0)
        self.statusbar.set_margin_bottom(0)
        self.statusbar.push(303, 'Ready when you are')
        GObject.timeout_add(3000, self.statusbar.pop, 303)
        self.statusbar.set_spacing(6)
        self.statusbar.pack_end(ConnectionIndicator(self), False, False, 0)

        vbox = Gtk.VBox()
        vbox.pack_start(self.docview, True, True, 0)
        vbox.pack_start(self.statusbar, False, False, 0)
        self.add(vbox)
        # TODO: Statusbar

        # save and restore window settings
        if self.app.config.get('window-maximized'):
            self.maximize()
        size_setting = self.app.config.get('window-size')
        if size_setting is not None:
            self.resize(size_setting[0], size_setting[1])
        position_setting = self.app.config.get('window-position')
        if position_setting is not None:
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
        self.app.config['window-size'] = [size[0], size[1]]

        position = widget.get_position()
        self.app.config['window-position'] = [position[0], position[1]]

    def on_window_state_event(self, widget, event):
        maximized = (
            'GDK_WINDOW_STATE_MAXIMIZED' in event.new_window_state.value_names)
        self.app.config['window-maximized'] = maximized

    def save_state(self):
        state = {'docview': self.docview.save_state()}
        return state

    def restore_state(self, state):
        self.docview.restore_state(state['docview'])
