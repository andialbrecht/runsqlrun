from gi.repository import Gtk, GObject, Pango


class Results(Gtk.TreeView):

    def __init__(self):
        super(Results, self).__init__()
        self.set_reorderable(False)
        self.set_enable_search(False)
        self.set_fixed_height_mode(True)
        self._active_query = None

    def set_query(self, query):
        self._active_query = query
        self.clear_results()
        query.connect('finished', self.on_query_finished)

    def get_active_query(self):
        return self._active_query

    def on_query_finished(self, query):
        if query.failed:
            print(query.error)
            return
        for idx, item in enumerate(query.description):
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
            col = Gtk.TreeViewColumn(
                item[0].replace('_', '__'), renderer, text=idx)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(100)
            col.set_resizable(True)
            self.append_column(col)
        model = CustomTreeModel(query.result)
        self.set_model(model)

    def clear_results(self):
        for column in self.get_columns():
            self.remove_column(column)
        self.set_model(None)


class CustomTreeModel(GObject.GObject, Gtk.TreeModel):

    def __init__(self, data):
        self.data = data
        self._num_rows = len(self.data)
        if self.data:
            self._n_columns = len(self.data[0])
        else:
            self._n_columns = 0
        GObject.GObject.__init__(self)

    def do_get_iter(self, path):
        """Returns a new TreeIter that points at path.

        The implementation returns a 2-tuple (bool, TreeIter|None).
        """
        indices = path.get_indices()
        if indices[0] < self._num_rows:
            iter_ = Gtk.TreeIter()
            iter_.user_data = indices[0]
            return (True, iter_)
        else:
            return (False, None)

    def do_iter_next(self, iter_):
        """Returns an iter pointing to the next column or None.

        The implementation returns a 2-tuple (bool, TreeIter|None).
        """
        if iter_.user_data is None and self._num_rows != 0:
            iter_.user_data = 0
            return (True, iter_)
        elif iter_.user_data < self._num_rows - 1:
            iter_.user_data += 1
            return (True, iter_)
        else:
            return (False, None)

    def do_iter_has_child(self, iter_):
        """True if iter has children."""
        return False

    def do_iter_nth_child(self, iter_, n):
        """Return iter that is set to the nth child of iter."""
        # We've got a flat list here, so iter_ is always None and the
        # nth child is the row.
        iter_ = Gtk.TreeIter()
        iter_.user_data = n
        return (True, iter_)

    def do_get_path(self, iter_):
        """Returns tree path references by iter."""
        if iter_.user_data is not None:
            path = Gtk.TreePath((iter_.user_data,))
            return path
        else:
            return None

    def do_get_value(self, iter_, column):
        """Returns the value for iter and column."""
        data = str(self.data[iter_.user_data][column])
        lines = data.splitlines()
        if lines:
            return lines[0]
        else:
            return data

    def do_get_n_columns(self):
        """Returns the number of columns."""
        return self._n_columns

    def do_get_column_type(self, column):
        """Returns the type of the column."""
        # Here we only have strings.
        return str

    def do_get_flags(self):
        """Returns the flags supported by this interface."""
        return Gtk.TreeModelFlags.ITERS_PERSIST
