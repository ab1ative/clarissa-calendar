"""Step 4. Pair each 1748 letter with its 1751 letter, and number them as Penguin does.

Both editions print the letters in the same order, so the pairing is a sequence alignment
(banded Needleman-Wunsch) scored by shared wording: the share of a letter's 4-word sequences
found in the other letter. Letters left unpaired are then explained:

  match      same letter in both editions
  rewritten  same place in the sequence and same writer, but largely rewritten (or a 1748
             heading-only item, "stub")
  part       a 1751 letter carved out of a longer 1748 letter (L435-436, L505-508)
  enclosed   a 1748 letter that 1751 prints inside another letter (Morden's, in L173)
  new        a 1751 letter with no 1748 counterpart
  summary    a 1751 letter that 1748 replaced with an editor's summary;
  summary1748  a 1748 summary that 1751 dropped without replacing

Penguin (Ross) numbers follow the 1751 sequence, L1-L537. Letters that exist only in 1751 have no
Penguin text, so Penguin skips their numbers; as a check, Penguin's own list of skipped numbers
must match the letters found to be new here.

Output: work/align.json, rows {a, b, how, L, host, sim} (a, b = indices into letters.json).
"""
import re
from common import work, load, save

d = load(work('letters.json'))
A, B = d['1'], d['3']

def norm(t):
    """Lower-case words, with the 1751 edition's commonest word substitutions undone."""
    t = t.lower()
    t = re.sub(r'\[page[^\]]*\]', ' ', t)
    t = t.replace('mamma', 'mother').replace('papa', 'father')
    return re.findall(r"[a-z]+", t)

def shingles(words, k=4):
    return {' '.join(words[i:i + k]) for i in range(len(words) - k + 1)}

def prep(L):
    """4-word sequences of the whole letter, its opening and its close."""
    w = norm(L['text'])
    return {'all': shingles(w), 'head': shingles(w[:250]), 'tail': shingles(w[-150:]), 'n': len(w)}

PA, PB = [prep(x) for x in A], [prep(x) for x in B]

def contain(x, y):  # share of x's shingles found in y
    return len(x & y) / max(1, len(x))

def sim(i, j):
    """How likely 1748 letter i and 1751 letter j are the same letter: how much of either one's
    opening (or, discounted, its close) appears in the other."""
    a, b = PA[i], PB[j]
    s = max(contain(a['head'], b['all']), contain(b['head'], a['all']))
    s = max(s, 0.6 * max(contain(a['tail'], b['all']), contain(b['tail'], a['all'])))
    return s

# Banded Needleman-Wunsch (letters stay in order; band keeps it fast)
n, m, BAND, TH = len(A), len(B), 40, 0.3
NEG = -1e9
score = [[NEG] * (m + 1) for _ in range(n + 1)]
back = [[None] * (m + 1) for _ in range(n + 1)]
score[0][0] = 0
for i in range(n + 1):
    for j in range(max(0, i - BAND), min(m, i + BAND) + 1):
        if i == 0 and j == 0: continue
        best, arg = NEG, None
        if i and j:
            s = sim(i - 1, j - 1)
            if s >= TH and score[i - 1][j - 1] + s > best:
                best, arg = score[i - 1][j - 1] + s, 'M'
        if i and score[i - 1][j] > best: best, arg = score[i - 1][j], 'A'
        if j and score[i][j - 1] > best: best, arg = score[i][j - 1], 'B'
        score[i][j], back[i][j] = best, arg

pairs, i, j = [], n, m
while i or j:
    a = back[i][j]
    if a == 'M': pairs.append((i - 1, j - 1)); i -= 1; j -= 1
    elif a == 'A': pairs.append((i - 1, None)); i -= 1
    else: pairs.append((None, j - 1)); j -= 1
pairs.reverse()


def addrkey(L):
    return re.sub(r'[^a-z]', '', L['addr'].lower().split(' to ')[0].replace('cl.', 'clarissa'))[:12]

pairs = [list(p) + [None] for p in pairs]          # [a, b, how]
for p in pairs:
    if p[0] is not None and p[1] is not None: p[2] = 'match'

# 1) Within each unmatched stretch, pair letters in order when the writer agrees
#    (heavily rewritten letters, and the 1748 heading-only stub).
k = 0
while k < len(pairs):
    if pairs[k][2] is None:
        e = k
        while e < len(pairs) and pairs[e][2] is None: e += 1
        ones = [p for p in pairs[k:e] if p[1] is None]
        threes = [p for p in pairs[k:e] if p[0] is None]
        for o in ones:
            for t in threes:
                if t[0] is None and addrkey(A[o[0]]) == addrkey(B[t[1]]):
                    t[0], t[2] = o[0], 'rewritten' if PA[o[0]]['n'] > 20 else 'stub'
                    o[2] = 'merged'; break
        left1 = [p for p in ones if p[2] != 'merged']
        left3 = [p for p in threes if p[0] is None]
        if len(left1) == 1 and len(left3) == 1 and contain(PA[left1[0][0]]['all'], PB[left3[0][1]]['all']) > 0.05:
            left3[0][0], left3[0][2] = left1[0][0], 'rewritten'; left1[0][2] = 'merged'
        k = e
    else:
        k += 1
pairs = [p for p in pairs if p[2] != 'merged']

# 2) Moved letters: an unmatched 1st-ed letter whose text turns up elsewhere in the 3rd ed.
for o in [p for p in pairs if p[1] is None]:
    best = max(range(m), key=lambda j: contain(PA[o[0]]['all'], PB[j]['all']))
    if contain(PA[o[0]]['all'], PB[best]['all']) > 0.5:
        holder = next(p for p in pairs if p[1] == best)
        if holder[0] is None or holder[2] != 'match':
            holder[0], holder[2] = o[0], 'moved'; o[2] = 'merged'
        else:  # the 3rd ed folds this letter into another one as an enclosure
            o[2] = 'enclosed'; o.append(best)
pairs = [p for p in pairs if p[2] != 'merged']

# 3) 3rd-ed letters carved out of a 1st-ed letter (text largely contained in it)
for p in pairs:
    if p[0] is None:
        best = max(range(n), key=lambda i: contain(PB[p[1]]['all'], PA[i]['all']))
        c = contain(PB[p[1]]['all'], PA[best]['all'])
        if c > 0.5:
            p[0], p[2] = best, 'part'
        elif contain(PA[best]['all'], PB[p[1]]['all']) > 0.5 and len(PA[best]['all']) < 400:
            p[0], p[2] = best, 'part'
        else:
            p[2] = 'new'
for p in pairs:
    if p[1] is None and p[2] != 'enclosed': p[2] = 'only1'

# 1748 editor's summaries stand in for one or more consecutive 1751 letters by the same writer.
for p in pairs:
    if p[0] is not None and A[p[0]].get('summary') and p[1] is not None:
        p[2] = 'summary'
changed = True
while changed:
    changed = False
    for k, p in enumerate(pairs):
        if p[2] != 'new': continue
        for nb in (k - 1, k + 1):
            if 0 <= nb < len(pairs) and pairs[nb][2] == 'summary' and addrkey(A[pairs[nb][0]]) == addrkey(B[p[1]]):
                p[0], p[2] = pairs[nb][0], 'summary'; changed = True; break
# a summary left unpaired: attach it to the nearest following 1751-only letter by the same writer
for k, p in enumerate(pairs):
    if p[2] == 'only1' and A[p[0]].get('summary'):
        for q in pairs[k + 1:k + 6]:
            if q[2] == 'new' and addrkey(A[p[0]]) == addrkey(B[q[1]]):
                q[0], q[2] = p[0], 'summary'; p[2] = 'merged'; break
        else:
            p[2] = 'summary1748'   # 1748 summary that 1751 dropped without replacing
pairs = [p for p in pairs if p[2] != 'merged']

# Penguin numbers = 3rd-edition sequence. Penguin prints a letter only where it has 1748 text.
PENGUIN_GAPS = {43, 66, 67, 122, 208, 249, 468, 469}   # Penguin p.1512, via Petzold
rows = []
for p in pairs:
    a, b, how = p[:3]
    L = b + 1 if b is not None else None
    rows.append({'a': a, 'b': b, 'how': how, 'L': L, 'host': p[3] + 1 if len(p) > 3 else None,
                 'sim': round(sim(a, b), 3) if a is not None and b is not None else None})
new = sorted(r['L'] for r in rows if r['how'] == 'new')
part = [(r['L'], A[r['a']]['vol'], A[r['a']]['num']) for r in rows if r['how'] == 'part']
print('  counts', {h: sum(r['how'] == h for r in rows) for h in set(r['how'] for r in rows)})
print('  new in 1751:', new)
# L208 is a 1748 summary (paired); L160 is a summary in Penguin that the 1748 transcription lacks.
assert set(new) == (PENGUIN_GAPS - {208}) | {160}, 'pairing disagrees with Penguin\'s skipped numbers'
# order check: every 3rd-ed letter appears once
assert sorted(r['b'] for r in rows if r['b'] is not None) == list(range(m))
save(rows, work('align.json'))
