from gi.repository import Gtk, GtkSource


class PreferencesDialog(Gtk.Dialog):

    def __init__(self, app):
        super(PreferencesDialog, self).__init__(
            'Preferences', app.win,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            use_header_bar=True)
        self.app = app
        self.config = app.config

        self.builder = Gtk.Builder()
        self.builder.add_from_resource('/org/runsqlrun/preferences.ui')
        content_area = self.get_content_area()
        notebook = self.builder.get_object('notebook')
        content_area.pack_start(notebook, True, True, 0)

        self._setup_dark_theme()
        self._setup_color_schemes()

        self._setup_font()
        self._setup_tab_width()
        self._setup_show_line_numbers()

        self.show_all()

    def _sp(self, key, value):
        self.config.set_property(key, value)

    def _setup_dark_theme(self):
        switch = self.builder.get_object('switch_dark_theme')
        switch.set_active(self.config.ui_dark_theme)
        switch.connect(
            'notify::active',
            lambda *a: self._sp('ui-dark-theme', switch.get_active()))

    def _setup_color_schemes(self):
        chooser = GtkSource.StyleSchemeChooserWidget()
        sw = self.builder.get_object('sw_color_schemes')
        sw.add(chooser)

        sm = GtkSource.StyleSchemeManager()
        chooser.set_style_scheme(
            sm.get_scheme(self.config.ui_style_scheme))
        chooser.connect(
            'notify::style-scheme',
            lambda *a: self._sp('ui-style-scheme',
                                chooser.get_style_scheme().get_id()))

    def _setup_font(self):
        use_system = self.builder.get_object('font_use_system_font')
        chooser_btn = self.builder.get_object('font_chooser_btn')
        use_system.connect(
            'notify::active',
            lambda *a: chooser_btn.set_sensitive(not use_system.get_active()))

        use_system.set_active(self.config.font_use_system_font)
        chooser_btn.set_font_name(self.config.font_fontname)

        use_system.connect(
            'notify::active',
            lambda *a: self._sp('font-use-system-font',
                                use_system.get_active()))
        chooser_btn.connect(
            'notify::font-name',
            lambda *a: self._sp('font-fontname', chooser_btn.get_font_name()))

    def _setup_tab_width(self):
        spin_btn = self.builder.get_object('editor_tab_width')
        spin_btn.set_range(1, 32)
        spin_btn.set_increments(1, 4)
        spin_btn.set_value(self.config.editor_tab_width)
        spin_btn.connect(
            'value-changed',
            lambda *a: self._sp('editor-tab-width', spin_btn.get_value()))

    def _setup_show_line_numbers(self):
        checkbox = self.builder.get_object('editor_show_line_numbers')
        checkbox.set_active(self.config.editor_show_line_numbers)
        checkbox.connect(
            'notify::active',
            lambda *a: self._sp('editor-show-line-numbers',
                                checkbox.get_active()))
