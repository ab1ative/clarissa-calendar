# Clarissa Calendar

A tool for Samuel Richardson's *Clarissa* to help both students and researchers compare multiple versions of the text, as well as visualize the whole of the text on a calendar.

- **Calendar.** Each letter's author has a corresponding shape that is drawn on the day it was written. You can hide the letters from any one individual by clicking their button in the top bar. Clicking on a day will open the first of the letters from that day and provide several buttons linking to the other letters for that day. 
- **Letters.** Each letter has been a 1748 and 1751 printing, as well as a comparative view. The first edition and the third edition are shown side by side, with marked changes in wording.

In addition:

- This tool features a search function of the entire text in both editions.
- A "Most revised" list ranks the letters Richardson modified most for 1751.
- Richardson's footnotes appear on hover.

The app is one static page, `site/index.html`, plus the JSON files next to it.

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

This tool uses texts for each edition drawn directly from ProQuest. These have some OCR issues that might be present in the final tool. I also compare against Angus Ross' edition, but I don't reproduce any of the Penguin text.

## How it works

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

I used Claude. Claude extracted the text from the two PDFs using Python 3.10 and `pdftotext` from poppler-utils. Claude then had to rebuild the text from broken OCR lines into actual paragraphs and split it into letters, for each edition. This is why I used artificial intelligence: It's an absoluately absurd amnount of text. Claude then had to pair the letters and number them sequentially, put them on a calendar, and mark changes. These steps were all done with Python scripts, and those scripts can be viewed in the data folder, though currently they do nothing.

## Files (in `site/`)

The actual texts live in two .json files, t1.json for 1748 and t3.json for 1751, which Claude created using the Python scripts in the data folder.

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

In creating this tool, I realized I was making an edition, given all the editorial choices I was making, particularly given the need to assign each letter a date. Here are some of those choices:

- **Year.** The year is the standard "Common Year Starting on a Sunday." https://en.wikipedia.org/wiki/Common_year_starting_on_Sunday

- **Dates.** The calendar follows the 1748 datelines, then the 1751 ones where 1748 gives none. The 1751 dateline is used instead for three 1748 misprints (L132, L146, L191) and for letters split differently in 1751. Each heading shows the dateline of the edition on screen; side by side, a differing 1751 dateline is shown after the 1748 one.
  - A letter that gives only a weekday goes on the next nearest the letter before it.
  - An undated letter goes on the day of the letter before it.

- **Restored passages** (`s08_supplement.py`).
  - **1751.** Passages missing from ProQuest's transcription are supplied from UPenn's transcription.
  - **1748.** Passages missing from ProQuest are supplied in the 1751 wording, but only where that wording agrees with Ross's text. About 420 words, in nine letters, could not be restored this way (L158, L165, L207, L257, L307, L363, L451, L467, L492).

- **Footnotes.** All of Richardson's notes are kept. His page references are resolved to letters (`s12_links.py`).

- **Places** (`s10_annotate.py`).
  - **Stated:** the place is named in the letter's dateline or heading.
  - **Inferred:** the place comes from the writer's movements in the story, set out in phases, with the letters each stretch rests on noted in comments.

- **Deceptive letters** (`s10_annotate.py`) are flagged only when the letter is forged, sent under a false name, or carries an intercepted or impostor letter.

- **Marked days**:
  - Black outlines, pointing to some of the text's most important moments: the kidnapping, the fire, the arrest, Morden's return, Clarissa's death, and Lovelace's death.
  - Green outline: one of the most revised letter's, which I think is most revealing about Richardson's purposes in making these revisions: L140, named "Miss Betterton's Death".
  - 13 June, the day of the assault, is drawn in red.
