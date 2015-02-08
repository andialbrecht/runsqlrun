import time

from gi.repository import Gtk, GObject, Pango, Gdk, Gio


class Results(Gtk.Notebook):

    def __init__(self):
        super(Results, self).__init__()
        self._active_query = None

        self.data = DataList(self)
        sw = Gtk.ScrolledWindow()
        sw.add(self.data)
        self.append_page(sw, Gtk.Label('Results'))

        self.log = QueryLog()
        sw = Gtk.ScrolledWindow()
        sw.add(self.log)
        self.append_page(sw, Gtk.Label('Log'))

    def set_query(self, query):
        self._active_query = query
        self.data.set_query(query)
        self.log.add_query(query)
        self.set_current_page(1)

    def get_active_query(self):
        return self._active_query


class DataList(Gtk.TreeView):

    def __init__(self, results):
        super(DataList, self).__init__()
        self.set_reorderable(False)
        self.set_enable_search(False)
        self.set_fixed_height_mode(True)
        # Selection is handled by button-press-event
        self.get_selection().set_mode(Gtk.SelectionMode.NONE)
        self.results = results
        # The cell menu needs to be created outside the callback for the
        # button-press-event. Otherwise it just don't show or flickers.
        self.cell_menu = Gtk.Menu()
        self.connect('button-press-event', self.on_button_pressed)

    def set_query(self, query):
        self.clear_results()
        query.connect('finished', self.on_query_finished)

    def on_query_finished(self, query):
        if query.failed:
            return
        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1, .5)
        renderer.set_property('weight', Pango.Weight.BOLD)
        col = Gtk.TreeViewColumn('#', renderer, markup=0)
        col.set_property('alignment', 1)
        col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col.set_fixed_width(50)
        col.set_resizable(True)
        self.append_column(col)
        for idx, item in enumerate(query.description):
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
            col = Gtk.TreeViewColumn(
                item[0].replace('_', '__'), renderer, markup=idx + 1)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(100)
            col.set_resizable(True)
            self.append_column(col)
        model = CustomTreeModel(query.result)
        self.set_model(model)
        self.results.set_current_page(0)

    def clear_results(self):
        model = self.get_model()
        del model
        self.set_model(None)
        for column in self.get_columns():
            self.remove_column(column)

    def on_button_pressed(self, treeview, event):
        if event.button == Gdk.BUTTON_SECONDARY:
            pthinfo = treeview.get_path_at_pos(event.x, event.y)
            if pthinfo is None:
                return
            path, column, cellx, celly = pthinfo
            if column == self.get_columns()[0]:
                return
            popup = self.get_cell_popup(path, column)
            popup.popup(None, None, None, None, event.button, event.time)
            return True

    def get_cell_popup(self, path, column):
        model = self.get_model()
        iter_ = model.get_iter(path)
        value = model.get_raw_value(iter_, self.get_columns().index(column))
        self.cell_menu.forall(self.cell_menu.remove)
        item = Gtk.MenuItem('Copy to clipboard')
        item.connect('activate',
                     lambda *a: self.copy_value_to_clipboard(value))
        item.show()
        self.cell_menu.append(item)
        return self.cell_menu

    def copy_value_to_clipboard(self, value):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(str(value), -1)


class CustomTreeModel(GObject.GObject, Gtk.TreeModel):

    def __init__(self, data):
        self.data = data
        self._num_rows = len(self.data)
        if self.data:
            self._n_columns = len(self.data[0])
        else:
            self._n_columns = 0
        lbl = Gtk.Label()
        context = lbl.get_style_context()
        col = context.get_color(Gtk.StateFlags.INSENSITIVE)
        self._col_insensitive_str = col.to_color().to_string()
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

    def get_raw_value(self, iter_, column):
        return self.data[iter_.user_data][column - 1]

    def do_get_value(self, iter_, column):
        """Returns the value for iter and column."""
        if column == 0:
            return self._markup_rownum(iter_.user_data + 1)
        value = self.data[iter_.user_data][column - 1]
        if value is None:
            return self._markup_none(value)
        elif isinstance(value, memoryview):
            return self._markup_blob(value)
        else:
            data = str(value)
            lines = data.splitlines()
            if lines:
                return GObject.markup_escape_text(lines[0])
            else:
                return GObject.markup_escape_text(data)

    def _markup_rownum(self, value):
        return '<span color="{}">{}</span>'.format(
            self._col_insensitive_str, value)

    def _markup_none(self, value):
        return '<span color="{}">NULL</span>'.format(
            self._col_insensitive_str)

    def _markup_blob(self, value):
        mime, _ = Gio.content_type_guess(None, value)
        if mime is not None:
            txt = '{} ({})'.format(
                Gio.content_type_get_description(mime), mime)
        else:
            txt = 'LOB'
        return '<span color="{}">{}</span>'.format(
            self._col_insensitive_str,
            GObject.markup_escape_text(txt))

    def do_get_n_columns(self):
        """Returns the number of columns."""
        return self._n_columns

    def do_get_column_type(self, column):
        """Returns the type of the column."""
        # Here we only have strings.
        return str

    def do_get_flags(self):
        """Returns the flags supported by this interface."""
        return (Gtk.TreeModelFlags.ITERS_PERSIST
                | Gtk.TreeModelFlags.LIST_ONLY)


class QueryLog(Gtk.TreeView):

    def __init__(self):
        super(QueryLog, self).__init__()
        model = Gtk.ListStore(str, Gdk.RGBA)
        self.set_model(model)
        column = Gtk.TreeViewColumn(
            '', Gtk.CellRendererText(), markup=0, foreground_rgba=1)
        self.append_column(column)
        self.set_headers_visible(False)
        self.set_reorderable(False)
        self.set_enable_search(False)
        lbl = Gtk.Label()
        context = lbl.get_style_context()
        self.dimmed_fg = context.get_color(Gtk.StateFlags.INSENSITIVE)
        self.col_error = self.dimmed_fg.copy()
        self.col_error.red = max(self.col_error.red * 1.7, 1)
        self.col_error.green *= 0.7
        self.col_error.blue *= 0.7
        font_desc = Pango.FontDescription.from_string('Ubuntu Mono 12')
        self.modify_font(font_desc)

    def add_query(self, query):
        model = self.get_model()
        if model.get_iter_first():
            model.set_value(model.get_iter_first(), 1, self.dimmed_fg)
        finished = query.finished
        model.prepend([self._get_markup(query), None])
        self.scroll_to_cell(model.get_path(model.get_iter_first()),
                            self.get_column(0), False, 0, 0)
        if not finished:
            GObject.timeout_add(17, self._update_current, query)

    def _update_current(self, query):
        model = self.get_model()
        model.set_value(model.get_iter_first(), 0, self._get_markup(query))
        if not query.finished:
            GObject.timeout_add(17, self._update_current, query)
        elif query.failed:
            model.set_value(model.get_iter_first(), 1, self.col_error)

    def _get_markup(self, query):
        if query.finished:
            if query.failed:
                markup = '✗ '
            else:
                markup = '✓ '
        else:
            markup = ''
        markup += GObject.markup_escape_text(query.sql.strip())
        if query.finished:
            if query.failed:
                content = query.error.strip()
            else:
                content = query.get_result_summary()
            markup += '\n<small>%s</small>' % GObject.markup_escape_text(
                content)
        elif query.pending:
            markup += '\n<small>Pending...</small>'
        else:
            markup += '\n<small>Running for %.3f seconds</small>' % (
                time.time() - query.start_time)
        return markup
