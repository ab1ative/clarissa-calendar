"""Step 8. Restore passages the ProQuest transcriptions leave out.

ProQuest's transcriptions of both editions drop most postscripts and most of Richardson's
italic editorial passages ("Mr. Lovelace, in continuation of his last Letter, gives an account..."),
and a few pages of the 1748 export are blank. These are oversights of the transcription: the
printed editions have them (Ross prints them from a 1748 copy, UPenn from the 1751 text).

1751: every passage of 12+ words in the UPenn transcription that ProQuest's 1751 lacks is
      inserted where it belongs, unless it repeats one of the letter's own footnotes (UPenn
      prints some footnotes in the text).
1748: every passage of 12+ words in Ross's Penguin text that ProQuest's 1748 lacks is inserted
      in the 1751 wording, original spelling, but only where that wording agrees with Ross's
      (spelling-blind similarity >= 0.85). The rest is listed in work/supplement_report.json.

Inserted words are prefixed \\uE002 (1751) or \\uE004 (1748), plus \\uE006 for italic passages,
so they can be traced; the page shows them as ordinary text.
"""
import os
from difflib import SequenceMatcher
from common import site, work, load, save, key, shingles, containment, SUPPLIED_UPENN, SUPPLIED_1748, ITALIC

MIN = 12            # shortest passage (in words) treated as missing
AGREE = 0.85        # 1751 wording must match Ross this closely to stand in for the 1748 text
SKIP_1748 = {537}   # Penguin's L537 runs on into the Conclusion
SKIP_SUB = {(173, 1)}   # Morden's letter: printed separately in 1748, so not missing from L173


def flat(text):
    """[[word, starts_paragraph]] of a text."""
    return [[w, i == 0] for p in text.split('\n') for i, w in enumerate(p.split())]

def unflat(toks):
    paras = []
    for w, start in toks:
        if start or not paras: paras.append([w])
        else: paras[-1].append(w)
    return '\n'.join(' '.join(p) for p in paras)

def missing_runs(ref_keys, our_keys):
    """(i1, i2, j) for each run ref[i1:i2] of MIN+ words absent from ours; j = where it belongs in ours."""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, ref_keys, our_keys, autojunk=False).get_opcodes():
        if tag in ('delete', 'replace') and i2 - i1 >= MIN and (tag == 'delete' or j2 - j1 <= 2):
            yield i1, i2, j1

def splice(ours, inserts):
    """Insert runs of [[word, starts_paragraph]] into ours; inserts = {position: [(run, ends_paragraph)]}."""
    out = []
    for j in range(len(ours) + 1):
        for run, ends in inserts.get(j, []):
            out += run
            if ends and j < len(ours): ours[j][1] = True
        if j < len(ours): out.append(ours[j])
    return out

def marked(span, prefix):
    italic = sum(1 for t in span if t[2]) >= 0.8 * len(span)
    return [[prefix + (ITALIC if italic else '') + w, start] for w, start, _ in span]


def upenn_index(T3, U):
    """1751 letter index -> UPenn letter key, by shared wording within the same volume."""
    usets = {k: shingles([key(w) for p in x['paras'] for w, _ in p]) for k, x in U.items()}
    letters = load(work('letters.json'))['3']
    out = {}
    for bi, b in enumerate(letters):
        mine = shingles([key(w) for w in T3[bi][2].split()])
        cands = [k for k in U if U[k]['vol'] == b['vol']]
        best = max(cands, key=lambda k: containment(mine, usets[k]))
        if containment(mine, usets[best]) > 0.5:
            out[bi] = best
    return out


def supplement_1751(T3, U, umap, report):
    for bi, k in umap.items():
        ref = [(w, i == 0, bool(it)) for p in U[k]['paras'] for i, (w, it) in enumerate(p)]
        rk = [key(w) for w, _, _ in ref]
        ours = flat(T3[bi][2])
        own = shingles([key(w) for w in (T3[bi][0] + ' ' + T3[bi][1] + ' ' + ' '.join(n[2] for n in T3[bi][3])).split()], 3)
        inserts = {}
        for i1, i2, j in missing_runs(rk, [key(w) for w, _ in ours]):
            if containment(shingles(rk[i1:i2], 3), own) >= 0.5:  # repeats the heading or a footnote
                continue
            inserts.setdefault(j, []).append((marked(ref[i1:i2], SUPPLIED_UPENN), i2 >= len(ref) or ref[i2][1]))
            report.setdefault('1751', {}).setdefault(bi, []).append(i2 - i1)
        if inserts:
            T3[bi][2] = unflat(splice(ours, inserts))


def supplement_1748(T1, U, umap, rows, P, report):
    pen = {}
    for p in P:
        if p['n'] and (p['n'], p['sub']) not in SKIP_SUB:
            pen.setdefault(p['n'], []).append(p)
    for r in rows:
        L, a, b = r['L'], r['a'], r['b']
        if not L or L not in pen or a is None or r['how'] == 'part' or L in SKIP_1748:
            continue
        ref = [(w, i == 0, False) for p in pen[L] for para in p['paras'] for i, w in enumerate(para.split())]
        uk = umap.get(b)
        u = [(w, i == 0, bool(it)) for p in U[uk]['paras'] for i, (w, it) in enumerate(p)] if uk else []
        uks = [key(w) for w, _, _ in u]
        ours = flat(T1[a][2])
        inserts = {}
        for i1, i2, j in missing_runs([key(w) for w, _, _ in ref], [key(w) for w, _ in ours]):
            pk = [x for x in (key(w) for w, _, _ in ref[i1:i2]) if x]
            words = ' '.join(w for w, _, _ in ref[i1:i1 + 12])
            blocks = [bl for bl in SequenceMatcher(None, pk, uks, autojunk=False).get_matching_blocks() if bl.size >= 3] if uks else []
            if not blocks:
                report.setdefault('1748 unaccounted', {}).setdefault(L, []).append([words, len(pk)]); continue
            u1, u2 = blocks[0].b, blocks[-1].b + blocks[-1].size
            ratio = SequenceMatcher(None, pk, [x for x in uks[u1:u2] if x], autojunk=False).ratio()
            if ratio < AGREE:
                report.setdefault('1748 unaccounted', {}).setdefault(L, []).append([words, len(pk), round(ratio, 2)]); continue
            run = marked(u[u1:u2], SUPPLIED_1748)
            run[0][1] = run[0][1] or ref[i1][1]
            inserts.setdefault(j, []).append((run, i2 >= len(ref) or ref[i2][1]))
            report.setdefault('1748', {}).setdefault(L, []).append(u2 - u1)
        if inserts:
            T1[a][2] = unflat(splice(ours, inserts))


def run():
    T1, T3, rows = load(site('t1.json')), load(site('t3.json')), load(site('index.json'))
    if not os.path.exists(work('upenn.json')):
        print('  no UPenn text: skipped'); return
    U = load(work('upenn.json'))
    umap = upenn_index(T3, U)
    report = {}
    supplement_1751(T3, U, umap, report)
    if os.path.exists(work('penguin.json')):
        supplement_1748(T1, U, umap, rows, load(work('penguin.json')), report)
    save(T1, site('t1.json')); save(T3, site('t3.json')); save(report, work('supplement_report.json'), pretty=True)
    n = lambda k: (len(report.get(k, {})), sum(sum(v) if isinstance(v[0], int) else sum(x[1] for x in v) for v in report.get(k, {}).values()))
    print(f'  1751 from UPenn: {len(umap)} letters matched; supplied {n("1751")[1]} words in {n("1751")[0]} letters')
    print(f'  1748: supplied {n("1748")[1]} words in {n("1748")[0]} letters; '
          f'{n("1748 unaccounted")[1]} words in {n("1748 unaccounted")[0]} letters unaccounted for')

if __name__ == '__main__':
    run()
