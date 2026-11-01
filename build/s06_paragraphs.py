"""Step 6. Settle the paragraph breaks that step 2 could not decide from the page geometry.

A "soft" mark (U+2063) sits on the word after a full-width line that ends a sentence. It
becomes a paragraph break only if the other edition starts a paragraph at the same word
(found by aligning the two texts word by word); otherwise the lines are joined.
Rewrites site/t1.json and site/t3.json.
"""
from difflib import SequenceMatcher
from common import site, load, save, key

SOFT = '⁣'

def toks(text):
    """[(word, starts_paragraph, soft)] in reading order."""
    return [(w, k == 0, w.startswith(SOFT)) for p in text.split('\n') for k, w in enumerate(p.split())]

def run():
    T = {1: load(site('t1.json')), 3: load(site('t3.json'))}
    breaks = {1: {}, 3: {}}           # edition -> letter -> token positions to break at
    for r in load(site('index.json')):
        a = r['a']; b = r['b'] if r['b'] is not None else (r['host'] - 1 if r.get('host') else None)
        if a is None or b is None or r['how'] in ('summary', 'summary1748'):
            continue
        A, B = toks(T[1][a][2]), toks(T[3][b][2])
        sm = SequenceMatcher(None, [key(w) for w, _, _ in A], [key(w) for w, _, _ in B], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                continue
            for x in range(i2 - i1):
                i, j = i1 + x, j1 + x
                if A[i][2] and B[j][1]: breaks[1].setdefault(a, set()).add(i)
                if B[j][2] and A[i][1]: breaks[3].setdefault(b, set()).add(j)
    for ed in (1, 3):
        made = joined = 0
        for i, x in enumerate(T[ed]):
            if SOFT not in x[2]:
                continue
            want, paras, cur = breaks[ed].get(i, set()), [], []
            for k, (w, start, soft) in enumerate(toks(x[2])):
                if cur and (start or (soft and k in want)):
                    paras.append(' '.join(cur)); cur = []
                made += soft and k in want; joined += soft and k not in want
                cur.append(w.replace(SOFT, ''))
            if cur:
                paras.append(' '.join(cur))
            x[2] = '\n'.join(paras)
        save(T[ed], site(f't{ed}.json'))
        print(f'  {ed}: {made} soft marks became paragraph breaks, {joined} joined')

if __name__ == '__main__':
    run()
