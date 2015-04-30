.. _getting_started:

Getting Started
===============


Requirements
------------

.. include:: ../README.md
   :start-after: ## Requirements
   :end-before: ## Run RunSQLRun


Installation
------------

For now there's only the source code on `Github`_. So you'll have
to check out the sources:

.. sourcecode:: bash

  $ git clone https://github.com/andialbrecht/runsqlrun.git
  $ cd runsqlrun
  $ make  # This is only required once or when you update the sources.
  $ python3 -m rsr


Running Your First Query
------------------------

RunSQLRun opens with a new worksheet on first run. On later runs it restores
the current state of the application. Just type a SQL statement like

.. sourcecode:: sql

  SELECT 'Hello World!';

and hit :kbd:`Ctrl+Enter`. A dialog pops up that asks for some details about
the database you want to connect to and finally runs this statement.

Refer to :ref:`connecting` for details on how to connect to your database.


.. _Github: https://github.com/andialbrecht/runsqlrun
