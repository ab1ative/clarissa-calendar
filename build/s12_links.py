"""Step 12. Turn Richardson's page references into links to letters.

Richardson's footnotes cite pages of his own edition ("See Vol. iii. p. 130", "Letter ix. p. 50",
"the next Letter"), and a few of his editorial passages do the same in the text ("See p. 205.").
The page numbers mean nothing here, so each reference is resolved to a letter and a word in it.

1. Page map: where each printed page begins, found by matching the words that open the page
   (after its "[Page N]" marker in work/<ed>_para.txt) against the letter texts.
2. In-text references become \\uE007ed:letter:word\\uE008 (shown as a link "L123"). Page numbers
   in words supplied from the 1751 text (step 8) are 1751 pages, even inside a 1748 letter.
3. Footnote references: each note in t1/t3 becomes [serial, mark, text, refs] with
   refs = [[start, end, letter, word], ...] character spans of the note text.
"""
import re
from common import work, site, load, save, tokens, key, from_roman, page_link

def page_starts(ed, letters):
    """{(vol, page): (letter, word)} for every printed page that can be located."""
    vols, out = [], {}
    for line in open(work(f'{ed}_para.txt'), encoding='utf-8').read().split('\n'):
        if line.strip() == 'NOTES': break
        m = re.match(r'^\s*Vol\. (\d+)\s*$', line)
        if m: vols.append((int(m.group(1)), [])); continue
        if vols: vols[-1][1].append(line)
    anchors = {}
    for vol, ls in vols:
        text = ' \n '.join(ls)
        for m in re.finditer(r'\[Page (\d+)\]', text):
            rest = re.sub(r'\[Page [^\]]*\]|[\[(][a-h*][\])]\s?\d+|⁣', ' ', text[m.end():m.end() + 600])
            anchors.setdefault((vol, int(m.group(1))), [w for w in rest.split() if w != '\n'])
    T = load(site(f't{ed}.json'))
    keys = [[key(w) for w in tokens(x[2])] for x in T]
    byvol = {}
    for i, L in enumerate(letters): byvol.setdefault(L['vol'], []).append(i)
    for (vol, pg), words in anchors.items():
        found = None
        h = re.match(r'^·?LETTER\.?$', words[0]) and len(words) > 1 and re.match(r'^([IVXLC]+)\.?$', words[1])
        if h:                                                    # page opens with a letter heading
            found = next(((i, 0) for i in byvol.get(vol, []) if letters[i]['num'] == from_roman(h.group(1))
                          and not letters[i].get('summary')), None)
        for skip in ([] if found else (0, 1, 2, 3, 4, 6, 8)):    # allow for a word split across the page
            want = [k for k in (key(w) for w in words[skip:skip + 14]) if k][:6]
            if len(want) < 4: continue
            for i in byvol.get(vol, []):
                K = keys[i]
                j = next((j for j in range(len(K) - len(want) + 1) if K[j:j + len(want)] == want), None)
                if j is not None: found = (i, j); break
            if found: break
        if found: out[(vol, pg)] = found
    return out

def at_page(pages, vol, pg):
    for d in (0, -1, 1):                                         # tolerate a page that opens on a heading
        if (vol, pg + d) in pages:
            i, j = pages[(vol, pg + d)]
            return [i, j] if d == 0 else [i, 0 if d == 1 else j]
    return None

TEXT_REF = re.compile(r'(?P<pre>[]*)(?P<vol>Vol\.\s*[ivxIVX]+\.?\s*)?[Pp]\.\s?[]*(?P<n>\d+)'
                      r'(?:\s*[]*(?:-|,|to)\s*[]*\d+)*(?P<dot>\.?)')
NOTE_REF = re.compile(
    r"(?=\S)(?P<let>Letters?,?\s*(?:N[o°S]\.?\s*)?(?P<ln>[ivxlcIVXLC]+)\b\.?)?"
    r"(?:,?\s*(?:of|in)\s+(?:this|the same)\s+Vol(?:ume|\.)?\.?)?"
    r"(?:,?\s*(?P<volp>(?:(?:of|in)\s+)?Vol(?:ume)?\.?\s*(?P<vol>[ivxlIVXL]+)\b\.?))?"
    r"(?:,?\s*(?:Letters?,?\s*(?:N[o°S]\.?\s*)?(?P<ln2>[ivxlcIVXLC]+)\b\.?))?"
    r"(?:,?\s*(?P<pg>[Pp]\.\s*(?P<p>\d+)))?")
RELATIVE = re.compile(r"(?:the\s+)?(?P<w>next|following|preceding|foregoing|last)\s+Letter|Letter\s+(?P<w2>preceding|following)", re.I)

def run():
    letters = load(work('letters.json'))
    rows = load(site('index.json'))
    vol3_of = {r['a']: r['v3'] for r in rows if r['a'] is not None and r['v3']}
    pages = {ed: page_starts(ed, letters[ed]) for ed in '13'}
    for ed in '13':
        T = load(site(f't{ed}.json'))
        L = letters[ed]
        byvol = {}
        for i, x in enumerate(L): byvol.setdefault(x['vol'], []).append(i)
        def letter_no(vol, n):
            return next(([i, 0] for i in byvol.get(vol, []) if L[i]['num'] == n and not L[i].get('summary')), None)
        linked = total = 0
        for li, x in enumerate(T):
            here = L[li]['vol']
            # in-text references
            def sub(m):
                nonlocal linked
                supplied = '' in m.group('pre') or '' in m.group('pre')
                e = '3' if ed == '3' or supplied else '1'
                vol = from_roman(re.sub(r'[^ivxIVX]', '', m.group('vol'))) if m.group('vol') else \
                    (vol3_of.get(li) if ed == '1' and supplied else here)
                tgt = at_page(pages[e], vol, int(m.group('n'))) if vol else None
                if not tgt: return m.group(0)
                linked += 1
                return m.group('pre') + page_link(e, *tgt) + m.group('dot')
            x[2] = TEXT_REF.sub(sub, x[2])
            # footnote references
            notes = []
            for serial, mark, text, *_ in x[3]:
                refs, vol = [], here
                for m in NOTE_REF.finditer(text):
                    if m.end() == m.start() or not (m.group('ln') or m.group('ln2') or m.group('p')): continue
                    total += 1
                    ln = m.group('ln') or m.group('ln2')
                    if m.group('vol'): vol = from_roman(m.group('vol'))     # "and Letter liv." keeps the volume
                    tgt = at_page(pages[ed], vol, int(m.group('p'))) if m.group('p') else None
                    if ln:
                        lt = letter_no(vol, from_roman(ln))
                        if lt and not (tgt and tgt[0] == lt[0]): tgt = lt   # a page counts only inside that letter
                    if tgt:
                        g = m.group(0); s = m.start() + len(g) - len(g.lstrip(' ,;'))
                        tail = re.match(r'(?:,\s*\d+|\s+to\s+\d+|,?\s*&\s*seq\.?)*', text[m.end():])
                        refs.append([s, m.end() + (tail.end() if tail else 0)] + tgt); linked += 1
                for m in RELATIVE.finditer(text):
                    if any(a <= m.start() < b for a, b, *_ in refs): continue
                    j = li + 1 if (m.group('w') or m.group('w2')).lower() in ('next', 'following') else li - 1
                    if 0 <= j < len(T): refs.append([m.start(), m.end(), j, 0]); linked += 1; total += 1
                notes.append([serial, mark, text, sorted(refs)])
            x[3] = notes
        save(T, site(f't{ed}.json'))
        print(f'  {ed}: {len(pages[ed])} printed pages located; {linked} references linked ({total} in notes)')

if __name__ == '__main__':
    run()
