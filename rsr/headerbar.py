from gi.repository import Gio, Gtk

from rsr.commands import commands
from rsr.connections.ui import ConnectionDialog


class HeaderBar(Gtk.HeaderBar):

    def __init__(self, win):
        super(HeaderBar, self).__init__()
        self.win = win

        self.set_show_close_button(True)
        self.set_title('RunSQLRun')
        self.set_subtitle('Database query tool')

        self.pack_start(self._btn_from_command('app', 'neweditor'))
        self.pack_start(self._btn_from_command('editor', 'run'))

        # gears button
        menu = Gio.Menu()
        action = Gio.SimpleAction.new('manage_connections', None)
        action.connect('activate', self.on_manage_connections)
        self.win.app.add_action(action)
        menu.append('Manage connections', 'app.manage_connections')
        btn = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="preferences-system-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        btn.add(image)
        btn.set_popover(Gtk.Popover.new_from_model(btn, menu))
        self.pack_end(btn)

    def _btn_from_command(self, group, name):
        btn = Gtk.Button()
        btn.set_action_name('app.{}_{}'.format(group, name))
        data = commands[group]['actions'][name]
        icon = Gio.ThemedIcon(name=data['icon'])
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        btn.add(image)
        btn.set_tooltip_text('{} [{}]'.format(
                             data['description'], data['shortcut']))
        return btn

    def on_button_add_clicked(self, *args):
        self.win.docview.add_worksheet()

    def on_manage_connections(self, *args):
        dlg = ConnectionDialog(self.win, 'Manage Connections', False)
        dlg.run()
        dlg.destroy()
