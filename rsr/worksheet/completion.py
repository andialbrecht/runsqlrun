import re

from gi.repository import GtkSource, GObject

import sqlparse

KEYWORDS = list(sqlparse.keywords.KEYWORDS_COMMON)
KEYWORDS.extend([
    'ASC',
    'BEGIN', 'BETWEEN',
    'CASCADE', 'COMMIT', 'COUNT',
    'DESC',
    'EXISTS',
    'HAVING',
    'INTO', 'IS',
    'LIMIT',
    'NOT', 'NULL',
    'SUM',
    'UNION', 'USING',
])
KEYWORDS = set(KEYWORDS)


def matches(word1, word2):
    if word1 is None:
        return None
    regex = r'.*?'.join(r'({})'.format(re.escape(y)) for y in word1)
    return re.search(regex, word2, re.U | re.I)


class ProviderMixin:

    def _get_word(self, context):
        activation = context.get_activation()
        requested = activation != GtkSource.CompletionActivation.USER_REQUESTED
        end_iter = context.get_iter()
        start_iter = end_iter.copy()
        while not start_iter.starts_line():
            start_iter.backward_char()
            char = start_iter.get_char()
            if not (char.isalnum() or char in '_.'):
                start_iter.forward_char()
                break
        word = end_iter.get_buffer().get_text(start_iter, end_iter, False)
        if not word and requested:
            return None
        return word


class ProposalMixin:

    def _get_match_offsets(self, match, word):
        rest = word
        offset = 0
        for group in self.match.groups():
            idx = rest.index(group)
            offset += idx
            yield offset
            rest = rest[idx:]

    def _highlight_match(self, match, word):
        pos = 0
        markup = ''
        for offset in self._get_match_offsets(match, word):
            markup += GObject.markup_escape_text(word[pos:offset])
            markup += '<span underline="single">'
            markup += GObject.markup_escape_text(word[offset])
            markup += '</span>'
            pos = offset + 1
        markup += GObject.markup_escape_text(word[pos:])
        return markup

    def _calc_score(self, match, word):
        return sum(self._get_match_offsets(match, word))
        # The shorter the better
        # The closer to beginning of word the better
        # The more it matches of a word the better
        start, end = self.match.span()
        score = end - start
        score = score * (start + 0.1)
        return score


class SqlKeywordProposal(GObject.GObject, GtkSource.CompletionProposal,
                         ProposalMixin):

    def __init__(self, keyword, match):
        super(SqlKeywordProposal, self).__init__()
        self.keyword = keyword
        self.match = match
        self.score = self._calc_score(match, keyword)

    def do_get_text(self):
        return self.keyword + ' '

    def do_get_markup(self):
        return self._highlight_match(self.match, self.keyword)

    def do_get_info(self):
        return 'Keyword'


class SqlKeywordProvider(GObject.GObject, GtkSource.CompletionProvider,
                         ProviderMixin):

    def __init__(self):
        super(SqlKeywordProvider, self).__init__()

    def do_get_name(self):
        return 'SQL keywords'

    def do_get_icon(self):
        return None

    def do_populate(self, context):
        word = self._get_word(context)
        proposals = []
        for keyword in KEYWORDS:
            match = matches(word, keyword)
            if match is not None:
                proposals.append(SqlKeywordProposal(keyword, match))
        proposals.sort(key=lambda x: x.score)
        context.add_proposals(self, proposals, True)

    def do_get_activation(self):
        return (GtkSource.CompletionActivation.INTERACTIVE |
                GtkSource.CompletionActivation.USER_REQUESTED)

    def do_match(self, context):
        return True


class DbObjectProposal(GObject.GObject, GtkSource.CompletionProposal,
                       ProposalMixin):

    def __init__(self, obj, match):
        super(DbObjectProposal, self).__init__()
        self.obj = obj
        self.match = match
        self.score = self._calc_score(match, self.obj.name)

    def do_get_text(self):
        return self.obj.name

    def do_get_markup(self):
        return self._highlight_match(self.match, self.obj.name)

    def do_get_info(self):
        return self.obj.get_type_name()


class DbObjectProvider(GObject.GObject, GtkSource.CompletionProvider,
                       ProviderMixin):

    def __init__(self, editor):
        super(DbObjectProvider, self).__init__()
        self.worksheet = editor.worksheet
        self._identifiers = {}
        editor.connect(
            'parsed-statement-changed', self.on_parsed_statement_changed)

    def do_get_name(self):
        return 'Database Objects'

    def do_get_icon(self):
        return None

    def do_get_activation(self):
        return (GtkSource.CompletionActivation.INTERACTIVE |
                GtkSource.CompletionActivation.USER_REQUESTED)

    def do_match(self, context):
        return self.worksheet.connection is not None

    def do_populate(self, context):
        word = self._get_word(context)
        proposals = []
        tables_in_query = []
        known_identifiers = set(map(str.lower, self._identifiers.values()))
        candidates = self.worksheet.connection.schema.get_objects(
            types=['table', 'view'])
        for obj in candidates:
            self._add_match(proposals, word, obj.name, obj)
            if obj.name.lower() in known_identifiers:
                tables_in_query.append(obj)
        # add alias completions (columns)
        if word is not None:
            if '.' in word:
                check_word = word.split('.', 1)[-1]
            else:
                check_word = word
            for col in self._get_column_candidates(word, tables_in_query):
                self._add_match(proposals, check_word, col.name, col)
        proposals.sort(key=lambda x: (x.score, x.get_text()))
        context.add_proposals(self, proposals, True)

    def _add_match(self, proposals, word, completion, obj):
        """Adds a proposal for obj if word matches completion."""
        match = matches(word, completion)
        if match is not None:
            proposals.append(DbObjectProposal(obj, match))

    def _get_column_candidates(self, word, tables_in_query):
        """Returns a list of columns.

        This function takes into account that word is None (-> empty list)
        and that word contains an alias for a table.
        """
        if word is None:
            return []
        if '.' in word:
            alias, rest = word.split('.', 1)
            real_name = self._identifiers.get(alias, None)
            if real_name is None:
                return []

            # A predicate function is still needed. A single table could
            # be referenced more that once with different aliases.
            def predicate(t):
                return t.name.lower() == real_name.lower()
        else:
            def predicate(t):
                return True
        columns = []
        for table in filter(predicate, tables_in_query):
            columns.extend(table.columns)
        return columns

    def on_parsed_statement_changed(self, editor):
        parsed = editor.get_parsed_statement()
        if parsed is None:
            self._identifiers = {}
            return
        identifiers = {}
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.Identifier) \
               and token.get_real_name() is not None:
                identifiers[token.get_name()] = token.get_real_name()
                if token.get_alias() is not None:
                    identifiers[token.get_alias()] = token.get_real_name()
        self._identifiers = identifiers
