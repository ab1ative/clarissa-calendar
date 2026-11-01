"""Build the Clarissa Calendar's data from the sources.

    python3 build/build.py              run every step
    python3 build/build.py 8            run from step 8 to the end
    python3 build/build.py 8 8          run step 8 only

Steps (each is a script in build/, documented at its top):
   1 extract      text and word positions from the ProQuest PDFs (pdftotext)
   2 reflow       rebuild paragraphs from the line geometry
   3 parse        split into letters: headings, datelines, footnotes, editor's summaries
   4 align        pair 1748 and 1751 letters; Penguin numbers
   5 index        the letter index and the two text files for the app
   6 paragraphs   settle paragraph breaks the geometry left open
   7 sources      read the UPenn 1751 transcription and the Penguin epub
   8 supplement   restore passages the ProQuest transcriptions dropped
   9 dating       place letters on the story calendar
  10 annotate     places of writing, deceptive letters, marked days
  11 enclosures   enclosed letters and where they sit
  12 links        page references -> links to letters
  13 compare      word-by-word comparison; how much each letter was revised

Steps 5 onward rewrite the files in site/ from scratch, so start at step 5 or earlier after
changing anything that feeds the texts.
"""
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['s01_extract', 's02_reflow', 's03_parse', 's04_align', 's05_index', 's06_paragraphs', 's07_sources',
         's08_supplement', 's09_dating', 's10_annotate', 's11_enclosures', 's12_links', 's13_compare']


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    last = int(sys.argv[2]) if len(sys.argv) > 2 else len(STEPS)
    sys.path.insert(0, HERE)
    for n in range(first, last + 1):
        name = STEPS[n - 1]
        t = time.time()
        print(f'{n:2} {name[4:]}')
        runpy.run_path(os.path.join(HERE, name + '.py'), run_name='__main__')
        print(f'   ({time.time() - t:.0f}s)')


if __name__ == '__main__':
    main()
