import cairo
from gi.repository import Gtk, GtkSource, Pango, GObject, Gio

import sqlparse

from rsr import paths
from rsr.worksheet.completion import SqlKeywordProvider, DbObjectProvider


class Editor(GtkSource.View):

    __gsignals__ = {
        'parsed-statement-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, worksheet):
        super(Editor, self).__init__()
        self.buffer = GtkSource.Buffer()
        self.worksheet = worksheet
        self._parsed = None

        # Disable blinking cursor
        settings = self.get_settings()
        settings.set_property('gtk-cursor-blink', False)

        sm = GtkSource.StyleSchemeManager()
        sm.append_search_path(paths.theme_dir)
        self.buffer.set_style_scheme(sm.get_scheme('monokai-extended'))

        lang_manager = GtkSource.LanguageManager()
        self.buffer.set_language(lang_manager.get_language('sql'))
        self.set_buffer(self.buffer)
        self._setup_font()

        self.set_show_line_numbers(True)
        self.set_highlight_current_line(True)
        # attrs = GtkSource.MarkAttributes()
        # attrs.set_icon_name('document-new-symbolic')
        # self.set_mark_attributes('statement', attrs, 10)
        # self.set_show_line_marks(True)

        renderer = StatementGutter(self.buffer)
        gutter = self.get_gutter(Gtk.TextWindowType.LEFT)
        gutter.insert(renderer, 1)

        # Completions
        self._setup_completions()

        self.buffer.connect('changed', self.on_buffer_changed)

    def _setup_font(self):
        # TODO: Move to configuration
        schema = 'org.gnome.desktop.interface'
        if schema in Gio.Settings.list_schemas():
            settings = Gio.Settings(schema)
            font_name = settings.get_string('monospace-font-name')
        else:
            font_name = 'Monospace 13'
        font_desc = Pango.FontDescription.from_string(font_name)
        self.modify_font(font_desc)

    def _setup_completions(self):
        completion = self.get_completion()
        completion.add_provider(DbObjectProvider(self))
        completion.add_provider(SqlKeywordProvider())

    def on_buffer_changed(self, buf):
        sql = self.get_text()

        # Build custom filter stack. sqlparse.split() removes whitespace ATM.
        stack = sqlparse.engine.FilterStack()
        stack.split_statements = True
        statements = [str(stmt) for stmt in stack.run(sql, None)]

        start, end = buf.get_bounds()
        buf.remove_source_marks(start, end, 'stmt_start')
        buf.remove_source_marks(start, end, 'stmt_end')

        cur_pos = buf.get_iter_at_mark(buf.get_insert()).get_offset()

        # Mark statements (aka the statement splitter)
        offset = 0
        for statement in statements:
            # Calculate offsets of stripped statement
            offset_start = offset + (len(statement) - len(statement.lstrip()))
            offset_end = offset_start + len(statement.strip())
            # Create source marks
            iter_ = buf.get_iter_at_offset(offset_start)
            buf.create_source_mark(None, 'stmt_start', iter_)
            iter_ = buf.get_iter_at_offset(offset_end)
            buf.create_source_mark(None, 'stmt_end', iter_)
            # Handle current statement
            if offset_start <= cur_pos <= offset_end:
                parsed = sqlparse.parse(statement)
                if parsed:
                    self._parsed = parsed[0]
                else:
                    self._parsed = None
                self.emit('parsed-statement-changed')
            # Update offset
            offset += len(statement)

    def get_cursor_position(self):
        mark = self.buffer.get_insert()
        iter_ = self.buffer.get_iter_at_mark(mark)
        return iter_.get_offset()

    def set_cursor_position(self, offset):
        if offset is None:
            return
        iter_ = self.buffer.get_iter_at_offset(offset)
        self.buffer.place_cursor(iter_)

    def get_text(self):
        buf = self.get_buffer()
        return buf.get_text(*buf.get_bounds(), include_hidden_chars=False)

    def set_text(self, text):
        self.get_buffer().set_text(text)

    def get_statement_iters_at_cursor(self):
        mark = self.buffer.get_insert()
        iter_start = self.buffer.get_iter_at_mark(mark)
        marks = self.buffer.get_source_marks_at_iter(iter_start, 'stmt_start')
        if not marks:
            self.buffer.backward_iter_to_source_mark(iter_start, 'stmt_start')
        iter_end = iter_start.copy()
        self.buffer.forward_iter_to_source_mark(iter_end, 'stmt_end')
        return iter_start, iter_end

    def get_statement_at_cursor(self):
        iter_start, iter_end = self.get_statement_iters_at_cursor()
        stmt = self.buffer.get_text(
            iter_start, iter_end, include_hidden_chars=False)
        stmt = stmt.strip()
        if not stmt:
            return None
        return stmt

    def format_statement(self):
        iter_start, iter_end = self.get_statement_iters_at_cursor()
        stmt = self.buffer.get_text(
            iter_start, iter_end, include_hidden_chars=False)
        formatted = sqlparse.format(stmt, reindent=True, keyword_case='upper')
        self.buffer.delete(iter_start, iter_end)
        self.buffer.insert(iter_start, formatted)

    def jump_next(self):
        mark = self.buffer.get_insert()
        iter_ = self.buffer.get_iter_at_mark(mark)
        self.buffer.forward_iter_to_source_mark(iter_, 'stmt_start')
        self.buffer.place_cursor(iter_)

    def jump_prev(self):
        mark = self.buffer.get_insert()
        iter_ = self.buffer.get_iter_at_mark(mark)
        sourcemarks = self.buffer.get_source_marks_at_iter(iter_)
        self.buffer.backward_iter_to_source_mark(iter_, 'stmt_start')
        if not sourcemarks:
            # If there are any source marks the cursor was already
            # placed at the beginning of a statement. In that case
            # backward_iter_to_source_mark moved the iter to the previous
            # statement already. Otherwise the first call moved the iter
            # to the beginning of the current statement.
            self.buffer.backward_iter_to_source_mark(iter_, 'stmt_start')
        self.buffer.place_cursor(iter_)

    def get_parsed_statement(self):
        return self._parsed


class StatementGutter(GtkSource.GutterRenderer):

    def __init__(self, buf):
        super(StatementGutter, self).__init__()
        self.set_size(10)
        self.buffer = buf

    def _in_statement(self, start):
        stmt_start = start.copy()
        marks = self.buffer.get_source_marks_at_iter(stmt_start, 'stmt_start')
        if not marks:
            self.buffer.backward_iter_to_source_mark(stmt_start, 'stmt_start')
        stmt_end = stmt_start.copy()
        self.buffer.forward_iter_to_source_mark(stmt_end, 'stmt_end')
        return start.in_range(stmt_start, stmt_end)

    def do_draw(self, cr, background_area, cell_area, start, end, state):
        in_statement = self._in_statement(start)
        if not in_statement:
            return
        cr.move_to(cell_area.x, cell_area.y)
        cr.line_to(cell_area.x, cell_area.y + cell_area.height)
        cr.set_line_width(10)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        # cr.set_source_rgba(*tuple(self.color))
        cr.stroke()
