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
    regex = r'.*?'.join(re.escape(y) for y in word1)
    return re.search(regex, word2, re.U | re.I)


class SqlKeywordProposal(GObject.GObject, GtkSource.CompletionProposal):

    def __init__(self, keyword, match):
        super(SqlKeywordProposal, self).__init__()
        self.keyword = keyword
        self.match = match
        self.score = self._calc_score()

    def _calc_score(self):
        # The shorter the better
        # The closer to beginning of word the better
        # The more it matches of a word the better
        start, end = self.match.span()
        score = end - start
        score = score * (start + 0.1)
        return score

    def do_get_text(self):
        return self.keyword + ' '

    def do_get_markup(self):
        start, end = self.match.span()
        markup = GObject.markup_escape_text(self.keyword[:start])
        markup += '<span underline="single">'
        markup += GObject.markup_escape_text(self.keyword[start:end])
        markup += '</span>'
        markup += GObject.markup_escape_text(self.keyword[end:])
        return markup

    def do_get_info(self):
        return 'Keyword'


class SqlKeywordProvider(GObject.GObject, GtkSource.CompletionProvider):

    def __init__(self):
        super(SqlKeywordProvider, self).__init__()

    def do_get_name(self):
        return 'SQL keywords'

    def do_get_icon(self):
        return None

    def do_populate(self, context):
        end_iter = context.get_iter()
        start_iter = end_iter.copy()
        start_iter.backward_word_starts(1)
        buff = end_iter.get_buffer()
        word = buff.get_text(start_iter, end_iter, False)
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
