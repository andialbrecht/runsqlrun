#!/bin/bash

# Run RunSQLRun from source checkout.
# This script is for development purposes only and works with
# fish shell.

glib-compile-schemas data/
glib-compile-resources --target=data/runsqlrun.gresource --sourcedir=data/ data/runsqlrun.gresource.xml
env GSETTINGS_SCHEMA_DIR=data/ python3 -m rsr
