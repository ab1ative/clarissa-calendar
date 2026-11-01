"""Step 11. Enclosed letters: which letters contain them, and where each one sits.

An enclosure is a letter sent inside another letter, or copied into it. Penguin numbers them
with decimals (L22.1, L22.2 ...); that numbering is taken as the list.

Adds to site/index.json:
  enc   ["22.1", "22.2"] on a letter that contains enclosures
  encd  1 on a letter that was itself sent as an enclosure but printed with its own number
        (heading "Inclosed in the preceding", e.g. L102), and on Morden's 1748 letter

Writes site/enc.json = {"1": {letter: [[first_para, last_para], ...]}, "3": {...}}: the
paragraphs of each enclosure inside its host letter, in each edition, so the page can set them
off. Each enclosure is found by matching Penguin's text of it against ours; it runs from its
address line ("To Miss Clarissa Harlowe.") to its signature. Clarissa's torn papers in L261
("PAPER I." to "PAPER X.") are enclosures too and are marked by their headings.

Penguin's L187.1-4 is Richardson's summary of four of Lovelace's letters, not enclosures: left out.

Without the Penguin epub, the enclosure list comes from build/data/penguin_enclosures.json (saved
on the last build that had it) and the paragraph ranges cannot be recomputed.
"""
import os
import re
from difflib import SequenceMatcher
from common import ROOT, site, work, load, save, tokens, key

LIST = os.path.join(ROOT, 'build', 'data', 'penguin_enclosures.json')
NOT_ENCLOSURES = {187}
PAPERS = 261


def signature_cut(paras):
    """Penguin runs the host letter's continuation into the enclosure's entry: stop at the
    enclosure's signature (a short paragraph in capitals, Penguin's small caps)."""
    out = []
    for p in paras:
        out.append(p)
        letters = [c for c in p if c.isalpha()]
        if len(out) > 1 and 0 < len(p.split()) <= 6 and letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
            break
    return out


def locate(sub_paras, paras):
    """[first, last] paragraph of our text that holds the enclosure, or None."""
    flat = [(pi, k) for pi, p in enumerate(paras) for k in map(key, tokens(p)) if k]
    ours = [k for _, k in flat]
    want = [k for k in (key(w) for p in sub_paras for w in p.split()) if k]
    if len(want) < 5:
        return None
    blocks = [b for b in SequenceMatcher(None, want, ours, autojunk=False).get_matching_blocks() if b.size >= 4]
    if not blocks or sum(b.size for b in blocks) / len(want) < 0.5:
        return None
    p0, p1 = flat[blocks[0].b][0], flat[blocks[-1].b + blocks[-1].size - 1][0]
    if p0 > 1 and len(paras[p0 - 1].split()) <= 14:              # take in the address line
        p0 -= 1
    while p1 + 1 < len(paras) and len(paras[p1 + 1].split()) <= 4 and not re.match(r'[·\s]*To ', paras[p1 + 1]):
        p1 += 1                                                  # and the subscription and signature
    return [p0, p1]


def papers(paras):
    """L261: each "PAPER N." up to the next one, stopping where Lovelace resumes."""
    heads = [i for i, p in enumerate(paras) if re.fullmatch(r'[-]*PAPER [IVX]+\.', p.strip())]
    resume = re.compile(r'^[-]*(Plague on it|After all, Belford)')
    spans = []
    for n, h in enumerate(heads):
        end = (heads[n + 1] if n + 1 < len(heads) else len(paras)) - 1
        end = next((j - 1 for j in range(h + 1, end + 1) if resume.match(paras[j])), end)
        spans.append([h, end])
    return spans


def merge(spans):
    out = []
    for a, b in sorted(spans):
        if out and a < out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            if out and a == out[-1][1]: a += 1
            out.append([a, b])
    return out


def run():
    rows = load(site('index.json'))
    T = {'1': load(site('t1.json')), '3': load(site('t3.json'))}
    have_penguin = os.path.exists(work('penguin.json'))
    subs = {}
    if have_penguin:
        for p in load(work('penguin.json')):
            if p['n'] and p['sub'] and p['n'] not in NOT_ENCLOSURES:
                subs.setdefault(p['n'], []).append(p)
        save({str(n): [f"{p['n']}.{p['sub']}" for p in ps] for n, ps in subs.items()}, LIST)
    numbers = load(LIST)
    spans = {'1': {}, '3': {}}
    for r in rows:
        r.pop('enc', None); r.pop('encd', None)
        if r['L'] and str(r['L']) in numbers and r['how'] != 'gap':
            r['enc'] = numbers[str(r['L'])]
        if r['how'] == 'enclosed' or re.search(r'\b[IE]nclos', r['w'] or ''):
            r['encd'] = 1
        for ed, idx in (('1', r['a']), ('3', r['b'])):
            if idx is None:
                continue
            paras = T[ed][idx][2].split('\n')
            found = [s for s in (locate(signature_cut(p['paras']), paras) for p in subs.get(r['L'], [])) if s]
            if r['L'] == PAPERS:
                found += papers(paras)
            if found:
                spans[ed][idx] = merge(found)
    save(rows, site('index.json'))
    if have_penguin:
        save(spans, site('enc.json'))
    print(f"  {sum(1 for r in rows if r.get('enc'))} letters contain enclosures; "
          f"{sum(len(v) for v in spans['1'].values())} enclosures placed in 1748, {sum(len(v) for v in spans['3'].values())} in 1751")

if __name__ == '__main__':
    run()
