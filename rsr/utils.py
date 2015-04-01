import re


def regex_fuzzy_match(word1, word2):
    if word1 is None:
        return None
    regex = r'.*?'.join(r'({})'.format(re.escape(y)) for y in word1)
    return re.search(regex, word2, re.U | re.I)
