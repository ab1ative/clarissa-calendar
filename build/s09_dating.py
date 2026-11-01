"""Step 9. Place every letter on the story calendar.

Adds to each row of site/index.json:  cal = [month, day, kind]
  kind "d"  Richardson gives the month and day (from the dateline or heading, else the
            letter's opening lines); shown as a filled shape
  kind "w"  he gives only a weekday ("Thursday Night."): the date is that weekday on or just
            after the letter before it (or just before, if that would overshoot the next dated
            letter); shown half-filled
  kind "i"  no date at all: placed on the day of the letter before it; shown as an outline

Datelines are read from the 1748 text first (as Ross does), then from 1751; see use_1751 for
the exceptions.

The year is never stated. The weekdays Richardson does give fit a common year that begins on a
Sunday (see common.JAN1_WEEKDAY).
"""
import re
from common import site, work, load, save, day_of_year, month_day, weekday as weekday_of

MON = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
MO = r'(Jan|Feb|Mar(?!y)|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.?'   # Mar(?!y): "Mary 29" is a 1748 misprint, not March
MD_RE = re.compile(r'\b' + MO + r'\s*(\d{1,2})\b', re.I)          # "April 13"
DM_RE = re.compile(r'\b(\d{1,2})\.?\s+' + MO, re.I)                  # "5 Sept."
WD_RE = re.compile(r'\b(Sunday|Sun\.|Monday|Mon\.|Tuesday|Tues?\.|Wednesday|Wedn?\.|Thursday|Thurs?\.|Friday|Frid?\.'
                   r'|Saturday|Sat\.)', re.I)
WD = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def full_date(s):
    """(day_of_year, stated weekday or None) from a dateline, or None."""
    if not s:
        return None
    a, b = MD_RE.search(s), DM_RE.search(s)
    if a and b and b.start() < a.start():      # "5 Sept. 9 in the Morn." is 5 Sept.
        a = None
    if a: m, d, at = MON[a.group(1)[:3].lower()], int(a.group(2)), a.start()
    elif b: m, d, at = MON[b.group(2)[:3].lower()], int(b.group(1)), b.start()
    else: return None
    if not 1 <= d <= MONTH_DAYS[m - 1]:
        return None
    w = WD_RE.search(s[:at + 20])
    return day_of_year(m, d), WD[w.group(1)[:3].lower()] if w else None

def weekday_only(s):
    w = WD_RE.search(s or '')
    return WD[w.group(1)[:3].lower()] if w else None

# The 1748 dateline is preferred, as in Ross's edition of the 1748 text, except:
MISPRINTS = {132, 146, 191}     # L132, L191: 1748 prints "April 10" and "May 10" for the 19th; L146: "April 23" for Saturday the 22nd

def use_1751(r):
    """Read the 1751 dateline first: for misprints, and for letters 1751 split out of a longer
    1748 letter (the 1748 dateline belongs to the whole of it)."""
    return r['L'] in MISPRINTS or r['how'] == 'part' or bool(r.get('sib'))

def run():
    letters = load(work('letters.json')); A, B = letters['1'], letters['3']
    rows = load(site('index.json'))
    stated = []                     # per row: (day or None, weekday or None)
    for r in rows:
        x1 = A[r['a']] if r['a'] is not None else None
        x3 = B[r['b']] if r['b'] is not None else None
        first, second = (x3, x1) if use_1751(r) else (x1, x3)
        eds = [x for x in (first, second) if x]
        # "In answer to hers of Thursday, Aug. 17." (L431 in 1748) dates the letter answered, not this one
        heads = [h for x in eds for h in (x['date'], x['addr']) if not h.lower().startswith('in answer to')]
        g = next((full_date(c) for c in heads + [x['text'][:200] for x in eds] if full_date(c)), None)
        wd = g[1] if g else next((weekday_only(x['date']) for x in eds if weekday_only(x['date']) is not None), None)
        stated.append((g[0] if g else None, wd))
    last, counts = None, {}
    for k, (r, (day, wd)) in enumerate(zip(rows, stated)):
        r.pop('cal', None)
        if day is not None:
            n, kind = day, 'd'
        elif last is None:
            continue
        elif wd is not None:
            nxt = next((x[0] for x in stated[k + 1:] if x[0] is not None), None)
            n = last + (wd - weekday_of(last)) % 7                     # this weekday, on or after
            if nxt is not None and nxt >= last and n > nxt and n - 7 >= last - 6:
                n -= 7                                                 # overshoots the next dated letter
            kind = 'w'
        else:
            n, kind = last, 'i'
        r['cal'] = [*month_day(n), kind]
        last = n
        counts[kind] = counts.get(kind, 0) + 1
    save(rows, site('index.json'))
    print('  dated:', counts.get('d', 0), ' weekday only:', counts.get('w', 0), ' undated:', counts.get('i', 0))

if __name__ == '__main__':
    run()
