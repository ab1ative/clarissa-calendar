"""Step 10. Places of writing, deceptive letters, and the calendar's marked days.

Adds to each row of site/index.json:
  loc = [place, "stated" | "inferred", explanation?]
        "stated": named in the letter's dateline or heading ("M. Hall, Sat. Night").
        "inferred": from where the writer is in the story at that date (PHASES below; each
        stretch is pinned to letters that state it, noted in the comments), or for minor
        writers from who they are (OTHERS).
  dec = [label, explanation] for letters that are forged, sent under a false name, carry an
        intercepted or impostor's letter, etc. Each explanation cites the text.

Writes site/places.json:
  clarissa: [[first_day, last_day + 1, short name, full name], ...]  where Clarissa is, by day
            of the year (the names shown over the calendar's weeks)
  events:   [{m, d, label, L, kind}]  days outlined on the calendar; kind "event" (black) or
            "revision" (green: a letter much revised for 1751, named by the editor)
"""
import re
from common import site, load, save, day_of_year

# ---- places named in datelines -> display name
STATED = [
    (r"Harlowe[- ]Place", 'Harlowe Place'), (r"St\. Alban'?s", 'St Albans'),
    (r"At Mrs\. Sinclair's", "Mrs. Sinclair's, London"), (r"Hamstead", 'Hampstead'),
    (r"Cocoa[- ]tree", 'the Cocoa Tree, London'), (r"\bLondon\b", 'London'), (r"M[.,]? Hall", 'M. Hall, Berkshire'),
    (r"Edgware", 'Edgware'), (r"Watford", 'Watford'), (r"Uxbridge", 'Uxbridge'), (r"Kensington", 'Kensington'),
    (r"Yarmouth, Isle of Wight", 'Yarmouth, Isle of Wight'), (r"Florence", 'Florence'), (r"Paris", 'Paris'),
    (r"Munich", 'Munich'), (r"Lintz", 'Linz'), (r"Trent", 'Trent'), (r"Enfield", 'Enfield'),
]


def stated_place(t):
    """Place named in the dateline, heading or first lines of a letter's text, or None."""
    for c in [t[1] or '', t[0] or ''] + t[2].split('\n')[:2]:
        head = re.split(r'(?:,|\.)\s*(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', c)[0]
        if len(head) > 45 or head == c and len(c) > 45:
            continue
        for pat, name in STATED:
            if re.search(pat, head):
                return name
    return None

# ---- where the main correspondents are (story calendar; inclusive ranges of (month, day))
PHASES = {
    'clarissa': [
        ((1, 1), (4, 9), 'Harlowe Place'),                    # L2, L6, L7 dated there
        ((4, 10), (4, 11), 'St Albans'),                       # L92, L97 dated there
        ((4, 12), (4, 25), "Mrs. Sorlings's farm"),            # L98 onwards; L149 "setting out for London"
        ((4, 26), (6, 8), "Mrs. Sinclair's, London"),          # L155 "I am in London, and in my new lodgings"
        ((6, 9), (6, 12), "Mrs. Moore's, Hampstead"),       # flight after the fire; L233
        ((6, 13), (6, 27), "Mrs. Sinclair's, London"),         # brought back on 12 June (L256)
        ((6, 28), (7, 15), "Mr. Smith's, Covent Garden"),      # L295 directs to King-street
        ((7, 16), (7, 18), "Rowland's, High Holborn (under arrest)"),   # L333-339
        ((7, 19), (9, 7), "Mr. Smith's, Covent Garden"),       # L340
        ((9, 8), (12, 31), "Mr. Smith's, Covent Garden (written before her death, delivered after)"),
    ],
    'lovelace': [
        ((3, 1), (4, 9), 'near Harlowe Place (the White Hart inn)'),   # L34
        ((4, 10), (4, 11), 'St Albans'),
        ((4, 12), (4, 25), "near Mrs. Sorlings's farm"),
        ((4, 26), (6, 8), "Mrs. Sinclair's, London"),          # L154 "our arrival"
        ((6, 9), (6, 12), 'Hampstead'),                     # L233 dated Hamstead
        ((6, 13), (6, 23), "Mrs. Sinclair's, London"),
        ((6, 24), (8, 20), 'M. Hall, Berkshire'),               # L282 to L346 dated M. Hall
        ((8, 21), (8, 31), 'London'),                          # L416 dated London
        ((9, 1), (9, 10), 'Uxbridge'),                       # L453, L463, L497
        ((9, 11), (10, 6), 'M. Hall, Berkshire'),               # L511
        ((10, 7), (12, 31), 'travelling on the Continent'),    # Paris, Munich, Linz, Trent
    ],
    'howe': [
        ((1, 1), (8, 6), "Mrs. Howe's house"),
        ((8, 7), (8, 24), 'Yarmouth, Isle of Wight'),           # L404, L434
        ((8, 25), (12, 31), "Mrs. Howe's house"),                # L455: mother ill at home
    ],
    'belford': [
        ((1, 1), (4, 25), 'London'),
        ((4, 26), (5, 10), "Edgware, at his dying uncle's"),  # L154 "thou wert at Edgware"; L169, L172
        ((5, 11), (12, 31), 'London'),
    ],
}
# other writers: (pattern on the writer's name, place, region)
OTHERS = [
    (r'Lord M\b|Lady Betty|Lady Sarah|Montague', 'M. Hall, Berkshire'),
    (r'Mrs\. Howe', "Mrs. Howe's house"),
    (r'Hickman', "near the Howes'"),
    (r'Harlowe|Hervey|Leman|Norton|Lewen|Hodges|Betty Barnes|Joseph', 'Harlowe Place (neighbourhood)'),
    (r'Mowbray|Tourville', 'London'),
    (r'Brand|Dr\. H\.', 'London'),
    (r'De la Tour', 'Trent'),
]

# Letters by minor writers: (pattern on the writer's name, place)
OTHERS = [
    (r'Lord M\b|Lady Betty|Lady Sarah|Montague', 'M. Hall, Berkshire'),
    (r'Mrs\. Howe', "Mrs. Howe's house"),
    (r'Hickman', "near the Howes'"),
    (r'Harlowe|Hervey|Leman|Norton|Lewen|Hodges|Betty Barnes|Joseph', 'Harlowe Place (neighbourhood)'),
    (r'Mowbray|Tourville|Brand|Dr\. H\.', 'London'),
    (r'De la Tour', 'Trent'),
]
# Dateline deliberately false
FALSE_DATELINE = {304: ("Mr. Smith's, Covent Garden",
                        'Dated "Enfield" to hide where she was; she was in hiding at Mr. Smith\'s, Covent Garden.')}
# Letters the tables above would place wrongly
PLACE_FIX = {231: "Mrs. Sinclair's, London",           # 2 a.m. on the night of the fire, before Clarissa's flight
             96: 'Harlowe Place (neighbourhood)', 139: 'Harlowe Place (neighbourhood)',   # Joseph Leman
             291: 'London',                               # Patrick McDonald
             None: 'Florence'}                            # Morden's 1748 letter, dated Florence

def place(r, t):
    L = r['L']
    if L in FALSE_DATELINE:
        return [FALSE_DATELINE[L][0], 'inferred', FALSE_DATELINE[L][1]]
    s = stated_place(t) if t else None
    if s:
        return [s, 'stated']
    if L in PLACE_FIX:
        return [PLACE_FIX[L], 'inferred']
    md = tuple(r['cal'][:2]) if r.get('cal') else None
    if r['g'] in PHASES:
        p = next((name for lo, hi, name in PHASES[r['g']] if md and lo <= md <= hi), None)
    else:
        writer = re.split(r',? [Tt]o |\. In |\. in |; In ', r['w'] or '')[0]
        p = next((name for pat, name in OTHERS if re.search(pat, writer)), None)
        if re.match(r'(Col(onel|\.)) ?Morden', writer) and md:
            p = 'Harlowe Place (neighbourhood)' if md >= (8, 25) else None
    return [p, 'inferred'] if p else None

# ---- deceptions: forged letters, false names, intercepted or impostors' letters ...
DECEPTIONS = {
    155: ('alias', 'Sets up the false name "Miss Lætitia Beaumont" for Anna\'s letters, collected at Wilson\'s in Pall Mall. The cover address was Lovelace\'s suggestion.'),
    229: ('intercepted', "Lovelace copies Anna's real letter of 7 June, which he has intercepted, marking the passages he means to avenge."),
    230: ('alias', 'In hiding at Hampstead, Clarissa asks Anna to write to her as "Mrs. Harriot Lucas".'),
    231: ('decoy', 'Contains a decoy note Clarissa wrote to Anna "only for a feint", to send Lovelace\'s servant Will out of the way before her escape. Will kept it back for Lovelace.'),
    233: ('impostor', 'Includes a letter signed by "Captain Antony Tomlinson", the impostor Lovelace hired to pose as a friend of Clarissa\'s uncle.'),
    238: ('intercepted', 'Lovelace has intercepted Anna\'s note to Clarissa, addressed to her alias "Mrs. Harriot Lucas".'),
    239: ('forgery', "Contains Lovelace's forgery of Anna's letter of 7 June, cut and added to by him and passed to Clarissa as genuine. Anna exposes it in L316."),
    256: ('impostor', 'Contains a note from "Lady Betty", one of the two women Lovelace hired to impersonate his aunt and cousin.'),
    272: ('impostor', 'Includes a letter from the impostor "Captain Tomlinson".'),
    282: ('false name', 'Superscribed "To Mrs. Lovelace", keeping up the pretence that they are married.'),
    283: ('false name', 'Superscribed "To Mrs. Lovelace", keeping up the pretence that they are married.'),
    284: ('false name', 'Superscribed "To Mrs. Lovelace", keeping up the pretence that they are married.'),
    288: ('false name', 'Superscribed "To Mrs. Lovelace", keeping up the pretence that they are married.'),
    289: ('impostor', 'To Patrick McDonald, the man posing as "Captain Tomlinson", under his real name.'),
    290: ('staged', 'A sham letter to "Captain Tomlinson", written to be shown to Clarissa "as in confidence".'),
    295: ('alias', 'Clarissa, in hiding, asks to be written to as "Mrs. Rachel Clark" at Mr. Smith\'s.'),
    298: ('alias', 'Clarissa asks to be written to as "Rachel Clark".'),
    304: ('false dateline', 'Dated "Enfield" and signed only "Your Friend", so as not to reveal where she is hiding.'),
    310: ('alias', 'Superscribed "For Mrs. Rachel Clark", Clarissa\'s assumed name at Mr. Smith\'s.'),
}
LABEL = {'alias': 'False name', 'intercepted': 'Intercepted', 'impostor': 'Impostor', 'forgery': 'Forgery',
         'false name': 'False name', 'staged': 'Staged', 'decoy': 'Decoy', 'false dateline': 'False dateline'}

# ---- days outlined on the calendar
EVENTS = [((4, 10), 'Lovelace kidnaps Clarissa', 97),
          ((6, 8), "Fire at Mrs. Sinclair's", 225),
          ((7, 16), "Clarissa arrested and held at Rowland's", 334),
          ((8, 14), 'Colonel Morden arrives in England from the Continent', 408),
          ((9, 7), 'Clarissa dies', 481),
          ((12, 18), 'Lovelace dies', 537)]
REVISIONS = {140: "Miss Betterton's Death"}     # much-revised letters marked in green, with the editor's name

# Short names for Clarissa's places, shown over the calendar's weeks
SHORT = {"Mrs. Sorlings's farm": "Sorlings's farm", "near Mrs. Sorlings's farm": "Sorlings's farm",
         "Mrs. Sinclair's, London": "Sinclair's, London", "Mrs. Moore's, Hampstead": 'Hampstead',
         "Mr. Smith's, Covent Garden": "Smith's, Covent Garden", "Rowland's, High Holborn (under arrest)": 'Arrested',
         'near Harlowe Place (the White Hart inn)': 'near Harlowe Place', "Edgware, at his dying uncle's": 'Edgware',
         'travelling on the Continent': 'Continent', 'M. Hall, Berkshire': 'M. Hall', "Mrs. Howe's house": "Mrs. Howe's",
         'Yarmouth, Isle of Wight': 'Isle of Wight'}


def run():
    rows = load(site('index.json')); T1 = load(site('t1.json')); T3 = load(site('t3.json'))
    for r in rows:
        t = T3[r['b']] if r['b'] is not None else (T1[r['a']] if r['a'] is not None else None)
        r['loc'] = place(r, t)
        r.pop('dec', None)
        if r['L'] in DECEPTIONS:
            kind, why = DECEPTIONS[r['L']]
            r['dec'] = [LABEL[kind], why]
    save(rows, site('index.json'))

    clarissa = []
    for lo, hi, name in PHASES['clarissa']:
        if lo > (9, 7): continue
        hi = min(hi, (9, 7))                                    # she dies on 7 September
        short = SHORT.get(name, name)
        if clarissa and clarissa[-1][2] == short and clarissa[-1][1] == day_of_year(*lo):
            clarissa[-1][1] = day_of_year(*hi) + 1              # merge neighbouring stretches
        else:
            clarissa.append([day_of_year(*lo), day_of_year(*hi) + 1, short, name])
    events = [{'m': m, 'd': d, 'label': label, 'L': L, 'kind': 'event'} for (m, d), label, L in EVENTS]
    taken = {(e['m'], e['d']) for e in events}
    for r in rows:
        if r['L'] in REVISIONS and r.get('cal') and tuple(r['cal'][:2]) not in taken:
            events.append({'m': r['cal'][0], 'd': r['cal'][1], 'label': REVISIONS[r['L']], 'L': r['L'], 'kind': 'revision'})
    save({'clarissa': clarissa, 'events': events}, site('places.json'))
    print(f"  places: {sum(1 for r in rows if r['loc'] and r['loc'][1] == 'stated')} stated, "
          f"{sum(1 for r in rows if r['loc'] and r['loc'][1] == 'inferred')} inferred, {sum(1 for r in rows if not r['loc'])} unknown;"
          f" {sum(1 for r in rows if r.get('dec'))} deceptive letters; {len(events)} marked days")

if __name__ == '__main__':
    run()
