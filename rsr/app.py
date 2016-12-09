import os
import json
from functools import partial

import xdg.BaseDirectory
from gi.repository import Gio, Gtk

from rsr import config
from rsr.commands import commands
from rsr.connections.manager import ConnectionManager
from rsr.mainwin import MainWindow
from rsr.preferences import PreferencesDialog


class Application(Gtk.Application):

    def __init__(self, args):
        super(Application, self).__init__(
            application_id='org.runsqlrun',
            flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.args = args
        self.win = None

    def build_app_menu(self):
        builder = Gtk.Builder()
        builder.add_from_resource('/org/runsqlrun/appmenu.ui')
        menu = builder.get_object('appmenu')
        self.set_app_menu(menu)

        newEditorAction = Gio.SimpleAction.new('editor-new', None)
        newEditorAction.connect('activate', self.on_new_editor)
        self.add_action(newEditorAction)

        closeEditorAction = Gio.SimpleAction.new('editor-close', None)
        closeEditorAction.connect('activate', self.on_close_editor)
        self.add_action(closeEditorAction)

        preferencesAction = Gio.SimpleAction.new('preferences', None)
        preferencesAction.connect('activate', self.on_show_preferences)
        self.add_action(preferencesAction)

        quitAction = Gio.SimpleAction.new('quit', None)
        quitAction.connect('activate', self.on_quit)
        self.add_action(quitAction)

    def on_new_editor(self, *args):
        self.win.docview.add_worksheet()

    def on_close_editor(self, *args):
        self.win.docview.close_current_editor()

    def on_show_preferences(self, *args):
        dlg = PreferencesDialog(self)
        dlg.run()
        dlg.destroy()

    def on_quit(self, *args):
        self.win.destroy()

    def do_window_removed(self, window):
        self.connection_manager.shutdown()
        state = window.save_state()
        statefile = os.path.join(
            xdg.BaseDirectory.save_config_path('runsqlrun'), 'state')
        with open(statefile, 'w') as f:
            json.dump(state, f)
        self.config.save()
        Gtk.Application.do_window_removed(self, window)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.build_app_menu()

    def _generic_callback(self, group, callback, cbargs, *args):
        if group == 'editor':
            cb = self.win.docview.get_current_editor()
        else:
            cb = self
        for part in callback.split('.'):
            cb = getattr(cb, part)
        cb(*cbargs)
        return True

    def on_use_dark_theme(self, *args):
        Gtk.Settings.get_default().set_property(
            'gtk-application-prefer-dark-theme',
            self.config.ui_dark_theme)

    def do_activate(self):
        self.connection_manager = ConnectionManager(self)
        self.config = config.load()
        self.config.connect('notify::ui-dark-theme', self.on_use_dark_theme)
        self.on_use_dark_theme()
        self.action_groups = {}
        accel_group = Gtk.AccelGroup()
        for group_key in commands:
            group = Gio.SimpleActionGroup()
            self.action_groups[group_key] = group
            data = commands[group_key]
            for action_key in data['actions']:
                action_data = data['actions'][action_key]
                action = Gio.SimpleAction.new(
                    '{}_{}'.format(group_key, action_key), None)
                callback = partial(self._generic_callback,
                                   group_key, action_data['callback'],
                                   action_data.get('args', ()))
                action.connect('activate', callback)
                group.insert(action)
                key, mod = Gtk.accelerator_parse(action_data['shortcut'])
                accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, callback)
                self.add_action(action)

        if self.win is None:
            self.win = MainWindow(self)
            statefile = os.path.join(
                xdg.BaseDirectory.save_config_path('runsqlrun'), 'state')
            if os.path.isfile(statefile):
                with open(statefile) as f:
                    state = json.load(f)
                self.win.restore_state(state)
        self.win.add_accel_group(accel_group)
        self.win.present()
