import json
import os

from gi.repository import GObject, Gio
from xdg import BaseDirectory

CONFIG_FILE = os.path.join(BaseDirectory.save_config_path('runsqlrun'),
                           'config.json')

name = 'runsqlrun'
version = '0.4.2-dev0'
description = 'A database UI.'
author = 'Andi Albrecht'
author_email = 'albrecht.andi@gmail.com'
url = 'http://runsqlrun.org'


class Config(GObject.GObject):

    ui_dark_theme = GObject.Property(type=bool, default=False)
    ui_style_scheme = GObject.Property(type=str, default='classic')

    font_use_system_font = GObject.Property(type=bool, default=True)
    font_fontname = GObject.Property(type=str, default='Monospace 13')
    editor_tab_width = GObject.Property(type=int, default=2)
    editor_show_line_numbers = GObject.Property(type=bool, default=True)

    def __init__(self):
        GObject.GObject.__init__(self)

    def get_fontname(self):
        if self.font_use_system_font:
            schema = 'org.gnome.desktop.interface'
            if schema in Gio.Settings.list_schemas():
                settings = Gio.Settings(schema)
                font_name = settings.get_string('monospace-font-name')
            else:
                font_name = 'Monospace 13'
            return font_name
        else:
            return self.font_fontname

    def save(self):
        data = {}
        for gspec in self.list_properties():
            data[gspec.name] = self.get_property(gspec.name)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)


def load():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    conf = Config()
    for gspec in conf.list_properties():
        if gspec.name in data:
            conf.set_property(gspec.name, data[gspec.name])
    return conf
