import csv
import mimetypes
import tempfile
import time
from collections import defaultdict
from enum import Enum

from gi.repository import Gtk, GObject, Pango, Gdk, Gio


class Results(Gtk.Notebook):

    def __init__(self, worksheet):
        super(Results, self).__init__()
        self.win = worksheet.win
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
        self._selection = ResultSelection(self)
        self.results = results
        self.win = results.win
        # The cell menu needs to be created outside the callback for the
        # button-press-event. Otherwise it just don't show or flickers.
        self.cell_menu = Gtk.Menu()
        self.connect('button-press-event', self.on_button_pressed)

    def set_query(self, query):
        self.clear_results()
        query.connect('finished', self.on_query_finished)

    def on_query_finished(self, query):
        if query.failed or query.result is None:
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
        offset_bg = len(query.description) * 2
        for idx, item in enumerate(query.description):
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
            col = Gtk.TreeViewColumn(
                item[0].replace('_', '__'), renderer, markup=idx + 1,
                background_rgba=offset_bg + idx)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(100)
            col.set_resizable(True)
            col.connect('clicked', self.on_column_header_clicked)
            self.append_column(col)
        self.set_headers_clickable(True)
        model = CustomTreeModel(query.result, self._selection)
        self.set_model(model)
        self.results.set_current_page(0)

    def clear_results(self):
        model = self.get_model()
        del model
        self.set_model(None)
        for column in self.get_columns():
            self.remove_column(column)
        self._selection.reset_selection()

    def on_button_pressed(self, treeview, event):
        if event.button == Gdk.BUTTON_SECONDARY:
            path, column = self._get_pathinfo_at_event(event)
            if column == self.get_columns()[0] or path is None:
                return
            popup = self.get_cell_popup(path, column)
            if not popup.get_children():
                return
            popup.popup(None, None, None, None, event.button, event.time)
            return True
        elif event.button == Gdk.BUTTON_PRIMARY:
            self._update_selection(event)

    def on_column_header_clicked(self, column):
        self._selection.select_column(column)
        self.queue_draw()

    def _get_pathinfo_at_event(self, event):
        """Returns a 2-tuple (path, column).

        Both values can be None.
        """
        pthinfo = self.get_path_at_pos(event.x, event.y)
        if pthinfo is None:
            return None, None
        path, column, cellx, celly = pthinfo
        return path, column

    def get_cell_popup(self, path, column):
        assert path is not None
        model = self.get_model()
        iter_ = model.get_iter(path)
        value = model.get_raw_value(iter_, self.get_columns().index(column))
        self.cell_menu.forall(self.cell_menu.remove)
        seltype = self._selection.get_active_selection_type()
        if seltype in (
            ResultSelection.Type.Nothing, ResultSelection.Type.Single):
            self._add_items_for_single_cell(model, value)
        elif seltype in (ResultSelection.Type.Columns,
                         ResultSelection.Type.Rows,
                         ResultSelection.Type.Multiple):
            self._add_items_for_row_cols(model, value)
        return self.cell_menu

    def _add_items_for_single_cell(self, model, value):
        if model.is_blob_value(value):
            content_type = Gio.content_type_guess(None, value)[0]
            if Gio.app_info_get_all_for_type(content_type):
                item = Gtk.MenuItem('View contents')
                item.connect(
                    'activate',
                    lambda *a: self.view_blob_contents(value, content_type))
                item.show()
                self.cell_menu.append(item)
            item = Gtk.MenuItem('Save contents')
            item.connect(
                'activate',
                lambda *a: self.save_blob_contents(value, content_type))
            item.show()
            self.cell_menu.append(item)
        else:
            item = Gtk.MenuItem('Copy value to clipboard')
            item.connect('activate',
                         lambda *a: self.copy_value_to_clipboard(value))
            item.show()
            self.cell_menu.append(item)
            item = Gtk.MenuItem('View value')
            item.connect('activate',
                         lambda *a: self.view_value(value))
            item.show()
            self.cell_menu.append(item)

    def _add_items_for_row_cols(self, model, value):
        item = Gtk.MenuItem('Export selection')
        item.show()
        item.connect('activate', lambda *a: self.export_selected())
        self.cell_menu.append(item)

    def _update_selection(self, event):
        additive = event.state == Gdk.ModifierType.CONTROL_MASK
        path, column = self._get_pathinfo_at_event(event)
        if column == self.get_columns()[0]:
            self._selection.select_row(path, additive)
        else:
            self._selection.select_cell(path, column, additive)
        self.queue_draw()

    def copy_value_to_clipboard(self, value):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(str(value), -1)

    def view_value(self, value):
        dlg = DataViewer(self.win, value)
        dlg.run()
        dlg.destroy()

    def view_blob_contents(self, value, content_type):
        dlg = Gtk.AppChooserDialog.new_for_content_type(
            self.win, Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
            content_type)
        if dlg.run() == Gtk.ResponseType.OK:
            app_info = dlg.get_app_info()
            if app_info is not None:
                fd, name = tempfile.mkstemp(
                    mimetypes.guess_extension(content_type) or '.blob')
                with open(name, 'wb') as f:
                    f.write(value)
                app_info.launch_uris(['file://%s' % name])
        dlg.destroy()

    def save_blob_contents(self, value, content_type):
        dlg = Gtk.FileChooserDialog(
            'Save Contents', self.win, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            with open(dlg.get_filename(), 'wb') as f:
                f.write(value)
        dlg.destroy()

    def export_selected(self):
        def to_csv(value):
            if value is None:
                return ''
            elif isinstance(value, memoryview):
                return ''
            return str(value)

        dlg = Gtk.FileChooserDialog(
            'Export Selection', self.win, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        file_filter = Gtk.FileFilter()
        file_filter.set_name('CSV files')
        file_filter.add_mime_type('text/csv')
        dlg.add_filter(file_filter)
        dlg.set_current_name('export.csv')
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            with open(dlg.get_filename(), 'w') as f:
                writer = csv.writer(f)
                for row in self._selection.get_export_data():
                    writer.writerow(list(map(to_csv, row)))
        dlg.destroy()


class CustomTreeModel(GObject.GObject, Gtk.TreeModel):

    def __init__(self, data, selection):
        self.data = data
        self.result_selection = selection
        self._num_rows = len(self.data)
        if self.data:
            self._n_columns = len(self.data[0])
        else:
            self._n_columns = 0
        lbl = Gtk.Label()
        context = lbl.get_style_context()
        col = context.get_color(Gtk.StateFlags.INSENSITIVE)
        self._col_insensitive_str = col.to_color().to_string()
        self._col_bg_selected = context.get_background_color(
            Gtk.StateFlags.SELECTED)
        self._col_bg_normal = context.get_background_color(
            Gtk.StateFlags.NORMAL)
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

    def is_blob_value(self, value):
        return isinstance(value, memoryview)

    def do_get_value(self, iter_, column):
        """Returns the value for iter and column."""
        if column == 0:
            return self._markup_rownum(iter_.user_data + 1)
        if column >= self._n_columns + 1:
            value_col = column - (self._n_columns * 2) + 1
            if self.result_selection.is_selected(iter_.user_data, value_col):
                return self._col_bg_selected
            else:
                return self._col_bg_normal
        value = self.data[iter_.user_data][column - 1]
        if value is None:
            return self._markup_none(value)
        elif self.is_blob_value(value):
            return self._markup_blob(value)
        else:
            data = str(value)
            lines = data.splitlines()
            if len(lines) > 1:
                return '{} <span color="{}">[...]</span>'.format(
                    GObject.markup_escape_text(lines[0]),
                    self._col_insensitive_str)
            elif lines:
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


class ResultSelection:
    """Custom selection implementation.

    This selection supports three modes:
    - row selection
    - column selection
    - cell selection
    Those modes are mutual exclusive.
    """

    MODE_ROW = 1
    MODE_COLUMN = 2
    MODE_CELL = 3

    class Type(Enum):
        Nothing = 1  # "None" looks strange here :)
        Single = 2
        Multiple = 3
        Rows = 4
        Columns = 5

    def __init__(self, treeview):
        self.treeview = treeview
        self.mode = None
        self._selected_rows = set()
        self._selected_columns = set()
        self._selected_cells = set()

    def set_mode(self, mode):
        if mode != self.mode:
            self.reset_selection()
            self.mode = mode

    def reset_selection(self):
        self._selected_rows = set()
        self._selected_columns = set()
        self._selected_cells = set()

    def is_selected(self, row, colnum):
        if self.mode == self.MODE_ROW:
            return row in self._selected_rows
        elif self.mode == self.MODE_COLUMN:
            return colnum in self._selected_columns
        elif self.mode == self.MODE_CELL:
            return (row, colnum) in self._selected_cells
        else:
            return False

    def select_row(self, path, additive):
        self.set_mode(self.MODE_ROW)
        row = path.get_indices()[0]
        if row in self._selected_rows:
            self._selected_rows.remove(row)
        else:
            if not additive:
                self.reset_selection()
            self._selected_rows.add(row)

    def _get_colnum(self, column):
        for idx, col in enumerate(self.treeview.get_columns()):
            if col == column:
                return idx

    def select_cell(self, path, column, additive):
        self.set_mode(self.MODE_CELL)
        row = path.get_indices()[0]
        colnum = self._get_colnum(column)
        if colnum is None:
            return
        entry = (row, colnum)
        if entry in self._selected_cells:
            self._selected_cells.remove(entry)
        else:
            if not additive:
                self.reset_selection()
            self._selected_cells.add(entry)

    def select_column(self, column):
        self.set_mode(self.MODE_COLUMN)
        colnum = self._get_colnum(column)
        if colnum is None:
            return
        if colnum in self._selected_columns:
            self._selected_columns.remove(colnum)
        else:
            self._selected_columns.add(colnum)

    def get_active_selection_type(self):
        if self._selected_columns:
            return ResultSelection.Type.Columns
        elif self._selected_rows:
            return ResultSelection.Type.Rows
        elif len(self._selected_cells) == 1:
            return ResultSelection.Type.Single
        elif self._selected_cells:
            return ResultSelection.Type.Multiple
        else:
            return ResultSelection.Type.Nothing

    def get_export_data(self):
        data = []
        model = self.treeview.get_model()
        if self.mode == ResultSelection.MODE_CELL:
            row = []
            last_row = None
            selected = list(self._selected_cells)
            selected.sort()
            unique_cols = set()
            selected_rows = defaultdict(list)
            for entry in selected:
                selected_rows[entry[0]].append(entry)
                unique_cols.add(entry[1])
            rows = list(selected_rows)
            rows.sort()
            unique_cols = list(unique_cols)
            unique_cols.sort()
            headers = []
            for colnum in unique_cols:
                column = self.treeview.get_column(colnum)
                headers.append(column.get_title().replace('__', '_'))
            data.append(headers)
            for rownum in rows:
                row = []
                for colnum in unique_cols:
                    if (rownum, colnum) in selected:
                        row.append(model.data[rownum][colnum - 1])
                    else:
                        row.append(None)
                if row:
                    data.append(row)
        elif self.mode == ResultSelection.MODE_COLUMN:
            selected_cols = list(self._selected_columns)
            selected_cols.sort()
            headers = []
            for colnum in selected_cols:
                column = self.treeview.get_column(colnum)
                headers.append(column.get_title().replace('__', '_'))
            data.append(headers)
            for item in model.data:
                row = []
                for colnum in selected_cols:
                    row.append(item[colnum - 1])
                if row:
                    data.append(row)
        elif self.mode == ResultSelection.MODE_ROW:
            headers = []
            for i in range(len(model.data[0])):
                column = self.treeview.get_column(i + 1)
                headers.append(column.get_title().replace('__', '_'))
            data.append(headers)
            for rownum in self._selected_rows:
                data.append(model.data[rownum])
        return data


class DataViewer(Gtk.Dialog):
    """Dialog to display a value"""

    def __init__(self, parent, data):
        """
        The constructor of this class takes 1 argument:

        :Parameter:
            data
                A Python value to display
        """
        Gtk.Dialog.__init__(self, 'Cell Content', parent,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CLOSE, Gtk.ResponseType.OK))
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.vbox.pack_start(sw, True, True, True)
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.get_buffer().set_text(str(data))
        sw.add(tv)
        sw.show_all()
        self.resize(650, 550)
