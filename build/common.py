"""Shared paths, text conventions and helpers for the Clarissa Calendar build.

Every build step imports from here, so the conventions below are defined exactly once.

Text conventions used in the letter texts (site/t1.json, site/t3.json)
-----------------------------------------------------------------------
A letter's text is a string of paragraphs separated by "\\n"; words are separated by spaces.
A few private-use characters carry information inside the text. The page strips or renders
them; the comparison ignores them (see key()).

  \\uE000 N \\uE001   reference to Richardson's footnote (or pointing hand) with ProQuest
                    serial N; the note itself is in the letter's notes list.
  \\uE002            prefix on a word supplied from the UPenn transcription of the 1751 text
                    (missing from ProQuest's 1751 transcription).
  \\uE004            prefix on a word supplied to the 1748 text in the 1751 wording, where
                    that wording agrees with Ross's Penguin text of the 1748 edition.
  \\uE006            prefix (after \\uE002/\\uE004) marking words Richardson set in italic
                    (his editorial passages). Kept in the data; the page does not style it.
  \\uE007 e:L:W \\uE008  an in-text page reference ("See p. 205.") resolved to letter L,
                    word W of edition e ("1" or "3"); the page shows it as a link "L123".
  "· " at the start of a paragraph: ProQuest's marginal dot (Richardson marked 3rd-edition
                    additions this way). Not displayed.

Edition codes: "1" = first edition (1748), "3" = third edition (1751).
"""
import json
import os
import re

# ---------------------------------------------------------------- paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, 'sources')   # inputs you supply (not committed): see README
WORK = os.path.join(ROOT, 'work')         # intermediate files, safe to delete
SITE = os.path.join(ROOT, 'site')         # the published app: index.html + data files
for _d in (WORK, SITE):
    os.makedirs(_d, exist_ok=True)

def src(name): return os.path.join(SOURCES, name)
def work(name): return os.path.join(WORK, name)
def site(name): return os.path.join(SITE, name)

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save(obj, path, pretty=False):
    with open(path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))

# ---------------------------------------------------------------- markers inside texts
NOTE_REF = re.compile('(\\d+)')
SUPPLIED_UPENN, SUPPLIED_1748, ITALIC = '', '', ''
MARKS = re.compile('[-]')
PAGE_LINK = re.compile('(\\d):(\\d+):(\\d+)')
HIDDEN = re.compile('\\d+|[^]*|[-]')   # never compared

def note_ref(n): return '%d' % n
def page_link(ed, letter, word): return '%s:%d:%d' % (ed, letter, word)

# ---------------------------------------------------------------- numbers
_ROMAN = ((100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I'))

def to_roman(n):
    out = ''
    for v, r in _ROMAN:
        while n >= v:
            out += r; n -= v
    return out

def from_roman(s):
    v = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    s = s.upper()
    return sum(-v[c] if i + 1 < len(s) and v[s[i + 1]] > v[c] else v[c] for i, c in enumerate(s))

# ---------------------------------------------------------------- the story calendar
# Richardson leaves the year unstated; his weekdays fit a common (non-leap) year beginning on a Sunday.
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
JAN1_WEEKDAY = 6            # Monday = 0 ... Sunday = 6

def day_of_year(m, d): return sum(MONTH_DAYS[:m - 1]) + d - 1

def month_day(n):
    m = 1
    while n >= MONTH_DAYS[m - 1]:
        n -= MONTH_DAYS[m - 1]; m += 1
    return m, n + 1

def weekday(n): return (JAN1_WEEKDAY + n) % 7

# ---------------------------------------------------------------- words
def tokens(text):
    """Words of a letter in reading order. Must match tokens() in site/index.html exactly:
    the word positions stored in diff.json, enc.json and the cross-references index into it."""
    out = []
    for p in text.split('\n'):
        if p.startswith('· '):
            p = p[2:]
        out += p.split()
    return out

# Spellings the 1751 edition modernised. A change of spelling is not a revision.
SPELL = {'tho': 'though', 'altho': 'although', 'thro': 'through', 'shew': 'show', 'shewn': 'shown', 'shewed': 'showed',
         'shewing': 'showing', 'shews': 'shows', 'chuse': 'choose', 'chuses': 'chooses', 'chusing': 'choosing',
         'compleat': 'complete', 'compleatly': 'completely', 'surprize': 'surprise', 'surprized': 'surprised',
         'surprizing': 'surprising', 'cloaths': 'clothes', 'antient': 'ancient', 'staid': 'stayed', 'gaol': 'jail',
         'connexion': 'connection', 'knowlege': 'knowledge', 'acknowlege': 'acknowledge', 'acknowleged': 'acknowledged',
         'dropt': 'dropped', 'stopt': 'stopped', 'stept': 'stepped', 'mixt': 'mixed', 'past': 'passed', 'chace': 'chase',
         'expence': 'expense', 'defence': 'defense', 'offence': 'offense', 'pretence': 'pretense', 'ake': 'ache',
         'aking': 'aching', 'phrensy': 'frenzy', 'stile': 'style', 'teaze': 'tease', 'teazing': 'teasing', 'gayety': 'gaiety',
         'cyder': 'cider', 'sallad': 'salad', 'waggon': 'wagon', 'controul': 'control', 'inclose': 'enclose',
         'inclosed': 'enclosed', 'cypher': 'cipher', 'pacquet': 'packet', 'chearful': 'cheerful', 'chearfully': 'cheerfully',
         'tryal': 'trial', 'tryals': 'trials', 'fansy': 'fancy', 'fansied': 'fancied', 'remembred': 'remembered'}
PREFIX = [('inq', 'enq'), ('intir', 'entir'), ('incourag', 'encourag'), ('indear', 'endear'), ('ingag', 'engag'),
          ('intreat', 'entreat'), ('inforc', 'enforc'), ('injoin', 'enjoin'), ('intrust', 'entrust'), ('intitl', 'entitl'),
          ('inclos', 'enclos'), ('indors', 'endors'), ('inquir', 'enquir'), ('incr', 'encr'), ('intang', 'entang'),
          ('ingross', 'engross'), ('incroach', 'encroach'), ('imploy', 'employ'), ('ingrat', 'ungrat')]

def key(w):
    """Comparison key for a word: lower case, no punctuation or hidden markers, old spellings
    mapped to modern ones. Two words with the same key count as the same word.
    Punctuation-only tokens get the empty key."""
    w = HIDDEN.sub('', w).lower().replace('’', "'")
    w = re.sub(r"(?<=[a-z])y'd$", 'ied', w)          # cry'd -> cried
    w = re.sub(r"(?<=[a-z])'d$", 'ed', w)            # help'd -> helped
    w = re.sub(r'[\W_]', '', w)
    w = SPELL.get(w, w)
    for a, b in PREFIX:                               # inquire -> enquire, intreat -> entreat ...
        if w.startswith(a):
            w = b + w[len(a):]; break
    if w.endswith('ick') and len(w) > 5:              # publick -> public
        w = w[:-1]
    if w.endswith(('our', 'ours', 'oured', 'ouring')) and len(w) > 5:
        w = w.replace('our', 'or')                    # honour -> honor
    return w

def shingles(keys, n=4):
    """Set of n-word sequences, used to measure how much of one text appears in another."""
    keys = [k for k in keys if k]
    return {tuple(keys[i:i + n]) for i in range(len(keys) - n + 1)}

def containment(a, b):
    """Share of shingle set a that is also in b."""
    return len(a & b) / max(1, len(a))
