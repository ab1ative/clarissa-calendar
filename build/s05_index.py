"""Step 5. Build the app's letter index and its two text files.

Outputs
  site/index.json   one row per letter, in reading order (the 1751 sequence):
      L        Penguin number (1751 sequence number), or None for Morden's 1748 letter
      a, b     index of the letter in t1.json (1748) and t3.json (1751), or None
      how      pairing kind from step 4; "new" becomes "gap" (Penguin skips the number)
               or "newflag" (Penguin prints a 1748 summary the transcription lacks: L160)
      host     for Morden's letter: the Penguin number of the 1751 letter enclosing it
      v1, n1   1748 volume and letter number;  v3, n3  the same for 1751
      w        heading (writer, to recipient)
      dt1, dt3 the dateline as printed in each edition ("" if none)
      note1    remark on a misnumbered 1748 heading, or on an editor's summary
      sib      for a split letter: the other Penguin numbers carved from the same 1748 letter
      g        writer group for the calendar's shapes: clarissa, lovelace, howe, belford,
               family, other
    Later steps add: cal, loc, dec (step 9-10), enc/encd (11), ad/dr (13), rv/rg (10).
  site/t1.json, site/t3.json   per letter: [heading, dateline, text, notes]
"""
import re
from common import work, site, load, save

GAPS = {43, 66, 67, 122, 208, 249, 468, 469}      # numbers Penguin's table says it skips

# Writer group, for letters whose heading names only the recipient, or names the writer oddly.
GROUP_FIX = {289: 'lovelace', 290: 'lovelace', 518: 'clarissa', 96: 'other', 139: 'other', 102: 'clarissa',
             147: 'family', 291: 'other', 485: 'family', 488: 'clarissa', 489: 'clarissa', 490: 'clarissa',
             491: 'clarissa', 492: 'clarissa', None: 'family'}          # None: Morden's 1748 letter

def group(heading):
    w = (heading or '').lower().replace('bedford', 'belford')
    writer = re.split(r',? to |\. in |; in |, in ', w)[0]
    if 'translation' in w or 'la tour' in w:
        return 'other'
    for g, names in (('clarissa', ['clarissa', 'cl. harlowe']), ('lovelace', ['lovelace']),
                     ('howe', ['miss howe', 'anna howe']), ('belford', ['belford']),
                     ('family', ['harlowe', 'hervey', 'mrs. howe', 'hickman', 'norton', 'morden', 'lord m', 'lady',
                                 'montague'])):
        if any(x in writer for x in names):
            return g
    return 'other'

def numbering_note(a):
    """Plain-language version of the parser's note on a misnumbered heading."""
    if not a['note']:
        return None
    if a.get('summary'):
        return a['note']
    if a['note'].startswith('The 1748 printing skips'):
        return (f"The 1748 printing numbers this letter {a['num']}: it skips straight from Letter {a['num'] - 2} "
                f"to Letter {a['num']}, so no 1748 letter is numbered {a['num'] - 1}. No letter is missing.")
    return f"The 1748 printing misnumbers this letter (it reads {a['printed']}); it is Letter {a['num']} of Volume {a['vol']}."

def recover_headings(letters):
    """Headings the parser missed: lift a leading "X, To Y." line (and a dateline) out of the text."""
    for L in letters:
        if L['addr']:
            continue
        lines = L['text'].split('\n')
        if lines and re.search(r', To ', lines[0]) and len(lines[0]) < 120:
            L['addr'] = lines.pop(0)
            if lines and re.match(r'^(Sun|Mon|Tue|Wed|Thu|Fri|Sat)[a-z]*\.?[ ,]', lines[0]) and len(lines[0]) < 60:
                L['date'] = lines.pop(0)
            L['text'] = '\n'.join(lines)

def run():
    d = load(work('letters.json')); A, B = d['1'], d['3']
    pairs = load(work('align.json'))
    recover_headings(A + B)
    by_a = {}
    for p in pairs:
        if p['a'] is not None and p['L']:
            by_a.setdefault(p['a'], []).append(p['L'])
    rows = []
    for p in pairs:
        a = A[p['a']] if p['a'] is not None else None
        b = B[p['b']] if p['b'] is not None else None
        how = p['how']
        if how == 'new':
            how = 'gap' if p['L'] in GAPS else 'newflag'
        w = (b or a)['addr'] or (a or b)['addr']
        rows.append({'L': p['L'], 'a': p['a'], 'b': p['b'], 'how': how, 'host': p.get('host'),
                     'v1': a['vol'] if a else None, 'n1': a['num'] if a else None,
                     'v3': b['vol'] if b else None, 'n3': b['num'] if b else None,
                     'w': w, 'dt1': a['date'] if a else '', 'dt3': b['date'] if b else '',
                     'note1': numbering_note(a) if a else None,
                     'sib': [x for x in by_a.get(p['a'], []) if x != p['L']] if a else [],
                     'g': GROUP_FIX.get(p['L'], group(w))})
    # Morden's 1748 letter goes right after the 1751 letter that encloses it
    enc = [r for r in rows if r['how'] == 'enclosed']
    rows = [r for r in rows if r['how'] != 'enclosed']
    for e in enc:
        rows.insert(next(i for i, r in enumerate(rows) if r['L'] == e['host']) + 1, e)
    save(rows, site('index.json'))
    save([[x['addr'], x['date'], x['text'], x['notes']] for x in A], site('t1.json'))
    save([[x['addr'], x['date'], x['text'], x['notes']] for x in B], site('t3.json'))
    print(f'  {len(rows)} rows')

if __name__ == '__main__':
    run()
