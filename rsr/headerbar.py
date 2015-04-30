from gi.repository import Gio, Gtk
from gi.repository.GdkPixbuf import Pixbuf

from rsr import __version__
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

        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self.on_show_about)
        self.win.app.add_action(action)
        menu.append('About RunSQLRun', 'app.about')

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
        dlg = ConnectionDialog(self.win, mode=ConnectionDialog.MODE_MANAGE)
        dlg.run()
        dlg.destroy()

    def on_show_about(self, *args):
        dlg = Gtk.AboutDialog('RunSQLRun', self.win)
        logo = Pixbuf.new_from_resource(
            '/org/runsqlrun/icons/128x128/runsqlrun.png')
        dlg.set_logo(logo)
        dlg.set_program_name('RunSQLRun')
        dlg.set_version(__version__)
        dlg.set_copyright('2015 Andi Albrecht <albrecht.andi@gmail.com>')
        dlg.set_license_type(Gtk.License.MIT_X11)
        dlg.set_website('http://runsqlrun.org')
        dlg.set_authors(['Andi Albrecht'])
        dlg.run()
        dlg.destroy()
