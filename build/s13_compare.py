"""Step 13. Word-by-word comparison of the two editions, and how much each letter was revised.

For every paired letter, the two full texts are compared as sequences of word keys (common.key:
case, punctuation and old spellings ignored). Paragraph breaks are not compared, so a break that
one transcription has and the other lacks can never look like a revision; the page lays the
paragraphs out afterwards.

Writes site/diff.json = {"a:b": [[tag, i1, i2, j1, j2], ...]}: opcodes over the token lists of
1748 letter a and 1751 letter b (common.tokens), with tags
  e  equal        r  replaced        d  only in 1748        i  only in 1751
  s  differs only in spelling, word division or punctuation (shown unmarked)

Adds to site/index.json: ad, dr = words 1751 adds to / drops from the letter (the "Most revised"
list). L173 does not count Morden's letter, which 1751 moved into it.
"""
import re
from difflib import SequenceMatcher
from common import site, load, save, tokens, key

MOVED_IN = {173}

def lev(a, b):
    if abs(len(a) - len(b)) > 2: return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def spelling_only(A, B):
    """True when two runs of keys differ only in spelling, hyphenation, word division or punctuation."""
    a, b = [k for k in A if k], [k for k in B if k]
    if ''.join(a) == ''.join(b):                     # any thing / any-thing / anything
        return True
    return len(a) == len(b) and bool(a) and all(
        x == y or (min(len(x), len(y)) >= 6 and lev(x, y) <= 1) or (min(len(x), len(y)) >= 8 and lev(x, y) <= 2)
        for x, y in zip(a, b))

WORD = re.compile(r'\w')

def run():
    T1, T3, rows = load(site('t1.json')), load(site('t3.json')), load(site('index.json'))
    out = {}
    for r in rows:
        r.pop('ad', None); r.pop('dr', None)
        if r['how'] in ('summary', 'summary1748', 'gap', 'newflag') or r['a'] is None:
            continue
        b = r['b'] if r['b'] is not None else (r['host'] - 1 if r.get('host') else None)
        if b is None:
            continue
        ta, tb = tokens(T1[r['a']][2]), tokens(T3[b][2])
        ka, kb = [key(w) for w in ta], [key(w) for w in tb]
        ops = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, ka, kb, autojunk=False).get_opcodes():
            t = 's' if tag != 'equal' and spelling_only(ka[i1:i2], kb[j1:j2]) else tag[0]
            ops.append([t, i1, i2, j1, j2])
        out[f"{r['a']}:{b}"] = ops
        if r['b'] is None:
            continue
        added = [sum(1 for w in tb[j1:j2] if WORD.search(w)) for t, i1, i2, j1, j2 in ops if t in 'ri']
        if r['L'] in MOVED_IN and added:
            added.remove(max(added))
        r['ad'] = sum(added)
        r['dr'] = sum(sum(1 for w in ta[i1:i2] if WORD.search(w)) for t, i1, i2, j1, j2 in ops if t in 'rd')
    save(out, site('diff.json'))
    save(rows, site('index.json'))
    top = sorted(((r['ad'], r['L']) for r in rows if r.get('ad')), reverse=True)[:5]
    print(f'  {len(out)} letters compared; most added: ' + ', '.join(f'L{L} (+{n})' for n, L in top))

if __name__ == '__main__':
    run()
