from gi.repository import GtkSource, Pango

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

    def get_text(self):
        buf = self.get_buffer()
        return buf.get_text(*buf.get_bounds(), include_hidden_chars=False)

    def set_text(self, text):
        self.get_buffer().set_text(text)
