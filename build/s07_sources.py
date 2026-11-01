"""Step 7. Read the two outside texts used to fill gaps in the ProQuest transcriptions.

UPenn: "Clarissa: The Complete 3rd Edition" (clarissa.english.upenn.edu), saved as
  sources/upenn_1751.json = {"vol.letter": page HTML}. The site has no download; the pages were
  collected in a browser with a short script (see README). Two letters are absent (1751 Vol. 1,
  Letter 42 and Vol. 6, Letters 38-39 are not served) - the build copes.
  -> work/upenn.json {"vol.seq": {vol, seq, num, addr, paras: [[[word, italic], ...], ...]}}
     Page markers are dropped, paragraphs split by a page break are rejoined, and footnote
     marks ("(a)") are removed.

Penguin: Angus Ross's edition (1985), sources/penguin_ross.epub (the user's own copy; never
  published). Used only to check the 1748 text: which passages ProQuest dropped, and where
  Penguin numbers enclosed letters (L22.1 ...).
  -> work/penguin.json [{n, sub, h, paras}] in book order (n = letter number, sub = enclosure
     number, 0 for the letter itself).
"""
import html
import json
import os
import re
import zipfile
from html.parser import HTMLParser
from common import src, work, save, from_roman


class _Paras(HTMLParser):
    """Collect <p> paragraphs as [(text, italic)], skipping header/footer divs and <sup>."""
    def __init__(self):
        super().__init__(); self.paras, self.cur, self.em, self.skip, self.sup = [], None, 0, 0, 0
    def handle_starttag(self, t, a):
        if t == 'div' and (dict(a).get('class') in ('header', 'footer') or self.skip): self.skip += 1
        if t == 'p': self.cur = []
        if t in ('em', 'i'): self.em += 1
        if t == 'sup': self.sup += 1
        if t == 'br' and self.cur is not None: self.cur.append(('\n', False))
    def handle_endtag(self, t):
        if t == 'div' and self.skip: self.skip -= 1
        if t == 'p' and self.cur is not None: self.paras.append(self.cur); self.cur = None
        if t in ('em', 'i'): self.em = max(0, self.em - 1)
        if t == 'sup': self.sup -= 1
    def handle_data(self, d):
        if not self.skip and self.cur is not None and not self.sup:
            self.cur.append((d.replace('\xa0', ' '), self.em > 0))


def words(segs):
    """[(word, italic)] from text segments; a segment not starting with a space continues the word."""
    toks = []
    for text, it in segs:
        for part in re.split(r'(\s+)', text):
            if not part: continue
            if part.isspace(): toks.append(None); continue
            if toks and toks[-1] is not None: toks[-1] = (toks[-1][0] + part, toks[-1][1] and it)
            else: toks.append((part, it))
    toks = [t for t in toks if t and not re.fullmatch(r'\(\s*[a-z*]\s*\)\.?', t[0])]     # footnote marks
    toks = [(re.sub(r'^\(\s*[a-z*]\s*\)', '', w), it) for w, it in toks]
    out = []
    for w, it in toks:                      # a full stop left behind by a removed mark joins its word
        if w == '.' and out: out[-1] = (out[-1][0] + '.', out[-1][1])
        elif w: out.append((w, it))
    return out


def read_upenn():
    pages = json.load(open(src('upenn_1751.json'), encoding='utf-8'))
    out = {}
    for k, page in pages.items():
        p = _Paras(); p.feed(page)
        paras, join_next = [], False
        for segs in p.paras:
            toks = words(segs)
            txt = ' '.join(w for w, _ in toks).strip()
            if not txt: continue
            if re.fullmatch(r'\[Page [^\]]*\]', txt): join_next = True; continue
            if join_next and paras: paras[-1] += toks
            else: paras.append(toks)
            join_next = False
        head = next((i for i, t in enumerate(paras)
                     if re.match(r'^[·\s]*(LETTER|CHAP)\b|^[IVXLC]+\.$', ' '.join(w for w, _ in t))), None)
        num = None
        if head is not None:
            m = re.match(r'^[·\s]*(?:LETTER\.?\s+|CHAP\.\s+)?([IVXLC]+)', ' '.join(w for w, _ in paras[head]))
            num = from_roman(m.group(1)) if m else None
        v, n = map(int, k.split('.'))
        out[k] = {'vol': v, 'seq': n, 'num': num,
                  'addr': ' '.join(w for w, _ in paras[head + 1]) if head is not None and head + 1 < len(paras) else '',
                  'paras': [[[w, int(i)] for w, i in t] for t in (paras[head + 2:] if head is not None else paras)]}
    return out


def read_penguin():
    z = zipfile.ZipFile(src('penguin_ross.epub'))
    opf_name = next(n for n in z.namelist() if n.endswith('.opf'))
    opf, base = z.read(opf_name).decode('utf-8'), os.path.dirname(opf_name)
    items = {m.group(1): m.group(2) for m in re.finditer(r'<item [^>]*id="([^"]+)"[^>]*href="([^"]+)"', opf)}
    items.update({m.group(2): m.group(1) for m in re.finditer(r'<item [^>]*href="([^"]+)"[^>]*id="([^"]+)"', opf)})
    spine = [os.path.join(base, items[i]) for i in re.findall(r'<itemref idref="([^"]+)"', opf)]
    book = re.sub(r'<a id="page_\d+"\s*/>', '', ''.join(z.read(f).decode('utf-8') for f in spine))
    txt = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', h))).strip()
    parts = re.split(r'(<h2[^>]*>.*?</h2>)', book, flags=re.S)
    out = []
    for i in range(1, len(parts), 2):
        h = txt(parts[i])
        m = re.match(r'\[?Letters? \[?(\d+)(?:\.(\d+))?', h)
        paras = [t for t in (txt(p) for p in re.findall(r'<p[^>]*>(.*?)</p>', parts[i + 1], re.S)) if t]
        out.append({'n': int(m.group(1)) if m else None, 'sub': int(m.group(2)) if m and m.group(2) else 0,
                    'h': h, 'paras': paras})
    return out


def run():
    if os.path.exists(src('upenn_1751.json')):
        u = read_upenn(); save(u, work('upenn.json')); print(f'  UPenn: {len(u)} letters')
    else:
        print('  UPenn transcription not found; the 1751 text will not be supplemented')
    if os.path.exists(src('penguin_ross.epub')):
        p = read_penguin(); save(p, work('penguin.json'))
        print(f'  Penguin: {sum(1 for x in p if x["n"] and not x["sub"])} letters, {sum(1 for x in p if x["sub"])} enclosures')
    else:
        print('  Penguin epub not found; the 1748 text will not be supplemented and enclosures come from the cache')

if __name__ == '__main__':
    run()
