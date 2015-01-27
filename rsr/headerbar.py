from gi.repository import Gio, Gtk

from rsr.commands import commands


class HeaderBar(Gtk.HeaderBar):

    def __init__(self, win):
        super(HeaderBar, self).__init__()
        self.win = win

        self.set_show_close_button(True)
        self.set_title('RunSQLRun')
        self.set_subtitle('Database query tool')

        self.pack_start(self._btn_from_command('app', 'neweditor'))
        self.pack_start(self._btn_from_command('editor', 'run'))

        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="preferences-system-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        btn.add(image)
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
