# RunSQLRun

[![Build Status](https://travis-ci.org/andialbrecht/runsqlrun.svg)](https://travis-ci.org/andialbrecht/runsqlrun)

RunSQLRun is a database query tool.

![Screenshot of RunSQLRun](http://runsqlrun.org/static/runsqlrun_query.png)

## Requirements

To run RunSQLRun you'll need the following system packages
on Debian / Ubuntu systems. The package names may vary
on other distributions:

- python3
- python3-gi
- python3-keyring
- python3-sqlparse

In addition you'll need to install a database driver for
each database management system you'd like to connect to:

- PostgreSQL: python3-psycopg2
- MariaDB/MySQL: python3-mysql.connector
- Oracle: cx_Oracle
- SQLite: Your Python distribution should ship a module for this database.

## Run RunSQLRun

To run RunSQLRun without installation change to the directory
where this README is located and run

    $ make
    $ python3 -m rsr

Calling "make" is only required once or when you update a source
checkout. It generates some files required to run the application.


## Links

Source: https://github.com/andialbrecht/runsqlrun/


Copyright (c) 2015 Andi Albrecht <albrecht.andi@gmail.com>

RunSQLRun is licensed under the terms of the MIT license.
See the file LICENSE for details.
