Working With Query Results
==========================

.. warning::

  LOBs (Large Object Binaries) are hold in memory to be displayed
  in the results list! So take care when running queries over tables
  that return such large objects, either LOBs, CLOBs or BLOBs of any
  kind. It will slow down the application. It's almost the same as
  running such queries in a terminal application like psql or sqlplus
  and waiting for the output to finish.
