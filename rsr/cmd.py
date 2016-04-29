import locale
import os
import signal
import sys
from argparse import ArgumentParser

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gio, GLib, Gtk

from rsr import __version__
from rsr import paths
from rsr.app import Application

parser = ArgumentParser(prog='runsqlrun', description='Run SQL statements')
parser.add_argument(
    '--version', action='version', version='%(prog)s ' + __version__)

# See issue3. Unfortunately this needs to be done before opening
# any Oracle connection.
os.environ.setdefault('NLS_LANG', '.AL32UTF8')

locale.setlocale(locale.LC_ALL, '.'.join(locale.getlocale()))


def main():
    parser.parse_args()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    GLib.set_application_name('RunSQLRun')
    GLib.set_prgname('runsqlrun')

    resource = Gio.resource_load(
        os.path.join(paths.data_dir, 'runsqlrun.gresource'))
    Gio.Resource._register(resource)

    Gtk.Settings.get_default().set_property(
        'gtk-application-prefer-dark-theme', True)

    app = Application()
    sys.exit(app.run(sys.argv))
