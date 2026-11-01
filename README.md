# Clarissa Calendar

A reading tool for Samuel Richardson's *Clarissa*. It has two views:

- **Calendar.** Every letter is placed on its day in the story, drawn as a shape for its writer. Clicking a day opens the letter in a pop-up.
- **Letters.** The first edition (1748) and the third edition (1751) are shown side by side, with every change in wording marked. Each letter also carries its Penguin (Angus Ross) number.

Other features:

- Richardson's footnotes appear on hover. His page references are turned into links to the letters they mean.
- Enclosed letters are set off from the letter that contains them.
- A search covers every text, note and heading.
- A "Most revised" list ranks the letters Richardson expanded most for 1751.

The app is one static page, `site/index.html`, plus the JSON files next to it. It needs no server code. Any static host will do, including GitHub Pages, or `python3 -m http.server` run inside `site/`.

## Folder layout

```
site/           the app: index.html and its data files (built by build/)
build/          the scripts that make the data, run in order by build/build.py
  common.py     shared conventions: paths, the text markers, word keys, the calendar
  data/         small derived facts kept between builds (Penguin's enclosure numbering)
sources/        the inputs you supply (not committed: see "Sources and rights")
work/           intermediate files written by the build (not committed; safe to delete)
```

## Sources and rights

| File in `sources/` | What it is | Used for |
|---|---|---|
| `proquest_1748.pdf` | ProQuest Literature Online export, *Clarissa* 1st ed. (1747–48) | the 1748 text and notes |
| `proquest_1751.pdf` | ProQuest Literature Online export, *Clarissa* 3rd ed. (1751) | the 1751 text and notes |
| `upenn_1751.json` | pages of *Clarissa: The Complete 3rd Edition*, clarissa.english.upenn.edu | passages ProQuest's 1751 text lacks |
| `penguin_ross.epub` | Angus Ross's Penguin edition (1985), your own copy | checking the 1748 text; enclosure numbering |

**Check the rights before publishing the site.**

- The ProQuest transcriptions come from a licensed database, and its terms most likely do not allow republishing them.
- The UPenn site is free to read but states no terms of reuse.
- None of Ross's text is reproduced. The build reads his edition only to compare against, and keeps nothing from it beyond letter and enclosure numbers.

`upenn_1751.json` maps `"volume.letter"` to each page's HTML. The site has no download, so the pages were collected in a browser on the site itself:

```js
// run in the browser console on any clarissa.english.upenn.edu/3rd-edition/ page
const out = {};
for (let v = 1; v <= 8; v++) {
  const idx = new DOMParser().parseFromString(await (await fetch(`/3rd-edition/${v}/`)).text(), 'text/html');
  for (const a of idx.querySelectorAll('a')) {
    const n = a.getAttribute('href');
    if (/^\d+$/.test(n)) out[`${v}.${n}`] = (await (await fetch(`/3rd-edition/${v}/${n}/`)).text());
  }
}
// then save JSON.stringify(out) as sources/upenn_1751.json
```

## Building

You need Python 3.10 or later and `pdftotext` from poppler-utils. Then run:

```
python3 build/build.py          # all steps, about 3 minutes
python3 build/build.py 8        # from step 8 on
python3 build/build.py 8 8      # step 8 only
```

Every step is a short script with a full description at its top. In brief:

| Step | Script | Does |
|---|---|---|
| 1 | `s01_extract.py` | extracts text and word positions from the PDFs (pdftotext) |
| 2 | `s02_reflow.py` | rebuilds paragraphs from the line geometry: a line ends a paragraph when the next line's first word would have fitted on it |
| 3 | `s03_parse.py` | splits the text into letters (headings, datelines, footnotes) and separates Richardson's 1748 editor's summaries |
| 4 | `s04_align.py` | pairs each 1748 letter with its 1751 letter and assigns Penguin numbers; checks the pairing against Penguin's list of skipped numbers |
| 5 | `s05_index.py` | writes the letter index and the two text files |
| 6 | `s06_paragraphs.py` | settles uncertain paragraph breaks by looking at the other edition |
| 7 | `s07_sources.py` | reads the UPenn pages and the Penguin epub |
| 8 | `s08_supplement.py` | restores the postscripts, editorial passages and blank pages that ProQuest dropped |
| 9 | `s09_dating.py` | places every letter on the story calendar |
| 10 | `s10_annotate.py` | adds places of writing, deceptive letters and the marked days |
| 11 | `s11_enclosures.py` | finds the enclosed letters and their paragraphs |
| 12 | `s12_links.py` | turns page references in notes and text into links to letters |
| 13 | `s13_compare.py` | makes the word-by-word comparison and counts how much each letter was revised |

The UPenn and Penguin sources are optional. Without them, steps 7 and 8 skip the supplementing. Step 11 then takes the enclosure list from `build/data/` but cannot place the enclosures in the text.

## Data files (in `site/`)

- **`index.json`** has one row per letter, in the 1751 order. Each row gives:
  - the Penguin number (`L`)
  - the position in each text file (`a` for 1748, `b` for 1751)
  - how the two editions relate (`how`: `match`, `rewritten`, `part`, `enclosed`, `gap`, `summary` and so on)
  - volume and letter numbers in each edition (`v1`, `n1`, `v3`, `n3`)
  - the heading (`w`) and the datelines of each edition (`dt1`, `dt3`)
  - the calendar day (`cal`), the place (`loc`) and any deception flag (`dec`)
  - enclosures (`enc`, `encd`) and the words added and cut in 1751 (`ad`, `dr`)

  Each field is documented in the script that adds it.
- **`t1.json`** and **`t3.json`** hold, per letter, `[heading, dateline, text, notes]`. The text is paragraphs separated by newlines. A few private-use characters mark footnote references, restored passages and links to letters; they are documented in `build/common.py`. Each note is `[serial, mark, text, references]`.
- **`diff.json`** holds the comparison of each pair of letters as opcodes over their word lists.
- **`enc.json`** gives the paragraph ranges of the enclosed letters.
- **`places.json`** gives where Clarissa is on each day, and the days outlined on the calendar.

## Editorial choices

The texts are edited, not merely transcribed. These are the choices made, and where to change each one.

- **Year.** Richardson never gives the year. His weekdays fit a common year that begins on a Sunday, and the calendar follows that year (`common.py`). Ross argues for 1732, which was a leap year. The note at the top of the calendar is the editor's own wording.
- **Dates.** The calendar follows the 1748 datelines, as Ross does, then the 1751 ones where 1748 gives none (`s09_dating.py`). The 1751 dateline is used instead for three 1748 misprints (L132, L146, L191, in `MISPRINTS`) and for letters split differently in 1751. Each heading shows the dateline of the edition on screen; side by side, a differing 1751 dateline is shown after the 1748 one.
  - A letter that gives only a weekday goes on that weekday, on or just after the letter before it.
  - An undated letter goes on the day of the letter before it.
  - Lovelace's death is marked on 18 December, the date of De la Tour's letter ("Dec. 18. N. S."), not the Old Style equivalent.
- **Restored passages** (`s08_supplement.py`).
  - **1751.** Passages missing from ProQuest's transcription are supplied from UPenn's transcription.
  - **1748.** Passages missing from ProQuest are supplied in the 1751 wording, but only where that wording agrees with Ross's text. About 420 words, in nine letters, could not be restored this way (L158, L165, L207, L257, L307, L363, L451, L467, L492). `work/supplement_report.json` lists them.
- **Footnotes.** All of Richardson's notes are kept. His page references are resolved to letters (`s12_links.py`).
- **Places** (`s10_annotate.py`).
  - **Stated:** the place is named in the letter's dateline or heading.
  - **Inferred:** the place comes from the writer's movements in the story, set out in `PHASES`, with the letters each stretch rests on noted in comments.
- **Deceptive letters** (`s10_annotate.py`, `DECEPTIONS`) are flagged only when the letter is forged, sent under a false name, or carries an intercepted or impostor's letter. Spying (Joseph Leman) and misleading wording (L421) were deliberately left out.
- **Marked days** (`s10_annotate.py`, `EVENTS` and `REVISIONS`):
  - Black outlines: the kidnapping, the fire, the arrest, Morden's return, Clarissa's death and Lovelace's death.
  - Green outline: the much-revised L140, named "Miss Betterton's Death".
  - 13 June is drawn in red (`SEL_RED` in `index.html`).
- **Writer groups** for the calendar's shapes are worked out from the headings. Letters whose heading names only the recipient are fixed by hand in `s05_index.py` (`GROUP_FIX`).
- **Enclosures** follow Penguin's numbering. The ten "Papers" in L261 are also treated as enclosures (`s11_enclosures.py`).
- **Not shown:** ProQuest's printed page numbers and its marginal dots, which mark paragraphs Richardson added in 1751.
