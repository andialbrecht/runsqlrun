.. _connecting:

Connecting to a Database
========================

Use the menu option "Manage connections" to view and manage database
connections.

However, you can just start to type your query and hit :kbd:`Ctrl+Enter`
to execute this query:

* if the current worksheet has no assigned connection, the connection
  manager dialog pops up. From there you can configure a connection
  which is assigned to the worksheet and will then be opened.
* if the current worksheet is assigned to connection, the connection
  will be opened,
* if the connection is already opened, you're fine.

In all cases the query is executed.

.. note::

  A worksheet may have a connection assigned. If so, the connection name
  is displayed in the window title and status bar.

  The assigned connection will be opened on demand, that is when you
  either first try to execute a query or hit :kbd:`F10` to open
  the connection manually.

Importan keyboard shortcuts for connections are:

:kbd:`F9`
  Assign a connection to a worksheet
:kbd:`F10`
  Open the connection
:kbd:`F11`
  Un-assign connection from worksheet


Defining a Database Connection
------------------------------

To define a new database connection either open the connection manager
dialog using the preferences menu. Or hit :kbd:`F9` to choose or create a
connection and to assign it directly to the current worksheet.

Just fill out the form that shows up when hitting the "Add" button in
the connection manager dialog.


Advanced Options
----------------

Opening a SSH Tunnel
~~~~~~~~~~~~~~~~~~~~

When editing a connection there's a tab the let's you define a custom
shell command. This command is executed in a subprocess before the
application tries to connect to the database and is terminated afterwards.

The purpose of this option is to support SSH tunnels when connecting to
a database. An example command could look like this:

.. code-block:: sh

  /usr/bin/ssh user@db.example.com -L 1521:dbname:1521
