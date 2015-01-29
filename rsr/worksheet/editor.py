from gi.repository import GtkSource, Pango

import sqlparse

from rsr import paths


class Editor(GtkSource.View):

    def __init__(self):
        super(Editor, self).__init__()
        self.buffer = GtkSource.Buffer()

        sm = GtkSource.StyleSchemeManager()
        sm.append_search_path(paths.theme_dir)
        self.buffer.set_style_scheme(sm.get_scheme('monokai-extended'))

        lang_manager = GtkSource.LanguageManager()
        self.buffer.set_language(lang_manager.get_language('sql'))
        self.set_buffer(self.buffer)
        # TODO: Move to configuration
        font_desc = Pango.FontDescription.from_string('Ubuntu Mono 16')
        self.modify_font(font_desc)

        self.set_show_line_numbers(True)
        self.set_highlight_current_line(True)
        # attrs = GtkSource.MarkAttributes()
        # attrs.set_icon_name('document-new-symbolic')
        # self.set_mark_attributes('statement', attrs, 10)
        # self.set_show_line_marks(True)

        self.buffer.connect('changed', self.on_buffer_changed)

    def on_buffer_changed(self, buf):
        sql = self.get_text()

        # Build custom filter stack. sqlparse.split() removes whitespace ATM.
        stack = sqlparse.engine.FilterStack()
        stack.split_statements = True
        statements = [str(stmt) for stmt in stack.run(sql, None)]

        start, end = buf.get_bounds()
        buf.remove_source_marks(start, end, 'stmt_start')
        buf.remove_source_marks(start, end, 'stmt_end')

        offset = 0
        for statement in statements:
            # Remove leading and trailing whitespaces and recalculate offset.
            lstripped = statement.lstrip()
            offset += len(statement) - len(lstripped)
            statement = lstripped.rstrip()
            iter_ = buf.get_iter_at_offset(offset)
            buf.create_source_mark(None, 'stmt_start', iter_)
            offset += len(statement)
            iter_ = buf.get_iter_at_offset(offset)
            buf.create_source_mark(None, 'stmt_end', iter_)

    def get_text(self):
        buf = self.get_buffer()
        return buf.get_text(*buf.get_bounds(), include_hidden_chars=False)

    def set_text(self, text):
        self.get_buffer().set_text(text)

    def get_statement_at_cursor(self):
        mark = self.buffer.get_insert()
        iter_start = self.buffer.get_iter_at_mark(mark)
        marks = self.buffer.get_source_marks_at_iter(iter_start, 'stmt_start')
        if not marks:
            self.buffer.backward_iter_to_source_mark(iter_start, 'stmt_start')
        iter_end = iter_start.copy()
        self.buffer.forward_iter_to_source_mark(iter_end, 'stmt_end')
        stmt = self.buffer.get_text(
            iter_start, iter_end, include_hidden_chars=False)
        stmt = stmt.strip()
        if not stmt:
            return None
        return stmt
