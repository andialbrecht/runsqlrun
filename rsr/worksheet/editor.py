import uuid

import cairo
from gi.repository import Gtk, GtkSource, Pango, GObject, Gdk, GLib

import sqlparse

from rsr.worksheet.completion import SqlKeywordProvider, DbObjectProvider


class BaseEditor(GtkSource.View):
    """Basic, language-agnostic editor."""

    def __init__(self, app, language=None):
        super(BaseEditor, self).__init__()
        self.buffer = GtkSource.Buffer()
        self.set_buffer(self.buffer)
        self._config = app.config

        # Disable blinking cursor
        settings = self.get_settings()
        settings.set_property('gtk-cursor-blink', False)
        self.set_auto_indent(True)
        self.set_highlight_current_line(True)

        if language is not None:
            lang_manager = GtkSource.LanguageManager()
            self.buffer.set_language(lang_manager.get_language(language))

        self._setup_style_scheme()
        self._setup_font()
        self._setup_tab_width()
        self._setup_line_numbers()

    def _setup_style_scheme(self):
        sm = GtkSource.StyleSchemeManager()

        def set_theme(*args):
            self.buffer.set_style_scheme(
                sm.get_scheme(self._config.ui_style_scheme))
        set_theme()
        self._config.connect('notify::ui-style-scheme', set_theme)

    def _setup_font(self):
        def set_font(*args):
            font_desc = Pango.FontDescription.from_string(
                self._config.get_fontname())
            self.modify_font(font_desc)
        set_font()
        self._config.connect('notify::font-use-system-font', set_font)
        self._config.connect('notify::font-fontname', set_font)

    def _setup_tab_width(self):
        def set_tabwidth(*args):
            self.set_tab_width(self._config.editor_tab_width)
        set_tabwidth()
        self._config.connect('notify::editor-tab-width', set_tabwidth)

    def _setup_line_numbers(self):
        def set_lino(*args):
            self.set_show_line_numbers(self._config.editor_show_line_numbers)
        set_lino()
        self._config.connect('notify::editor-show-line-numbers', set_lino)


class Editor(BaseEditor):

    __gsignals__ = {
        'parsed-statement-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'statements-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, worksheet):
        super(Editor, self).__init__(worksheet.app, 'sql')
        self.worksheet = worksheet
        self._parse_timeout = None
        self._parsed = None
        self._statements = []

        renderer = StatementGutter(self.buffer)
        gutter = self.get_gutter(Gtk.TextWindowType.LEFT)
        gutter.insert(renderer, 1)
        # Redraw statement highlight when cursor moves to correctly
        # highlight the current statement. Without explicity redrawing
        # the whole area only the current line is redrawn which will not
        # remove the highight from the previous statement.
        self.buffer.connect(
            'notify::cursor-position', lambda *a: renderer.queue_draw())

        # Completions
        self._setup_completions()

        self.buffer.connect('changed', self.on_buffer_changed_delayed)

    def _setup_completions(self):
        completion = self.get_completion()
        completion.add_provider(DbObjectProvider(self))
        completion.add_provider(SqlKeywordProvider())

    def on_buffer_changed_delayed(self, buf):
        if self._parse_timeout is not None:
            GLib.source_remove(self._parse_timeout)
        self._parse_timeout = GLib.timeout_add(
            200, self.on_buffer_changed, buf)

    def on_buffer_changed(self, buf):
        sql = self.get_text()

        # Build custom filter stack. sqlparse.split() removes whitespace ATM.
        stack = sqlparse.engine.FilterStack()
        stack.split_statements = True
        statements = [str(stmt) for stmt in stack.run(sql, None)]
        stmt_data = []

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
            parsed = sqlparse.parse(statement)
            # Handle current statement
            if offset_start <= cur_pos <= offset_end:
                # parsed = sqlparse.parse(statement)
                if parsed:
                    self._parsed = parsed[0]
                else:
                    self._parsed = None
                self.emit('parsed-statement-changed')
            stmt_data.append({
                'statement': statement,
                'start': offset_start,
                'end': offset_end,
                'parsed': parsed
            })
            # Update offset
            offset += len(statement)
        self._statements = stmt_data
        self.emit('statements-changed')
        self._parse_timeout = None

    def get_statements(self):
        return self._statements

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
        """Returns statement under cursor or selected part of buffer."""
        if self.buffer.get_has_selection():
            iter_start, iter_end = self.buffer.get_selection_bounds()
        else:
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
        formatted = sqlparse.format(
            stmt, reindent=True, keyword_case='upper',
            wrap_after=80, indent_width=1, indent_tabs=True)
        self.buffer.begin_user_action()
        self.buffer.delete(iter_start, iter_end)
        self.buffer.insert(iter_start, formatted)
        self.buffer.end_user_action()

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

    def close(self):
        self.worksheet.win.docview.close_current_editor()

    def insert_uuid(self):
        self.buffer.insert_at_cursor(str(uuid.uuid4()))

    def get_parsed_statement(self):
        return self._parsed


class StatementGutter(GtkSource.GutterRenderer):

    def __init__(self, buf):
        super(StatementGutter, self).__init__()
        self.set_size(10)
        self.buffer = buf

    def _in_statement(self, start):
        cur = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        stmt_start = start.copy()
        marks = self.buffer.get_source_marks_at_iter(stmt_start, 'stmt_start')
        if not marks:
            self.buffer.backward_iter_to_source_mark(stmt_start, 'stmt_start')
        stmt_end = stmt_start.copy()
        self.buffer.forward_iter_to_source_mark(stmt_end, 'stmt_end')
        return (start.in_range(stmt_start, stmt_end),
                stmt_start.get_line() <= cur.get_line() <= stmt_end.get_line())

    def do_draw(self, cr, background_area, cell_area, start, end, state):
        in_statement, is_current = self._in_statement(start)
        if not in_statement:
            return
        style = self.buffer.get_style_scheme()
        ref_style = style.get_style('line-numbers')
        if ref_style is not None:
            ok, col_default = Gdk.Color.parse(
                ref_style.get_property('foreground'))
        else:
            ok, col_default = Gdk.Color.parse('#1565C0')
        ok, col_highlight = Gdk.Color.parse('#1565C0')
        cr.move_to(cell_area.x, cell_area.y)
        cr.line_to(cell_area.x, cell_area.y + cell_area.height)
        cr.set_line_width(10)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        if is_current:
            cr.set_source_rgb(*col_highlight.to_floats())
        else:
            cr.set_source_rgb(*col_default.to_floats())
        cr.stroke()
