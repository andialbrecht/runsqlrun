import signal
import sys
from argparse import ArgumentParser

from gi.repository import Gio, GLib

from rsr import __version__
from rsr.app import Application

parser = ArgumentParser(prog='runsqlrun', description='Run SQL statements')
parser.add_argument(
    '--version', action='version', version='%(prog)s ' + __version__)


def main():
    parser.parse_args()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    GLib.set_application_name('RunSQLRun')
    GLib.set_prgname('runsqlrun')

    resource = Gio.resource_load('data/runsqlrun.gresource')
    Gio.Resource._register(resource)

    app = Application()
    sys.exit(app.run(sys.argv))
