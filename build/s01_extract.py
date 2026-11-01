"""Step 1. Extract text from the two ProQuest PDF exports with pdftotext (poppler-utils).

For each edition two extractions are made:
  work/<ed>.txt         `pdftotext -layout`: line by line. Used for the NOTES section at the end,
                        where each footnote starts its own line.
  work/<ed>_bbox.html   `pdftotext -bbox-layout`: every line and word with its coordinates.
                        Used by step 2 to rebuild paragraphs, which -layout output loses.
"""
import subprocess
from common import src, work

PDFS = {'1': 'proquest_1748.pdf', '3': 'proquest_1751.pdf'}

def run():
    for ed, pdf in PDFS.items():
        subprocess.run(['pdftotext', '-q', '-layout', src(pdf), work(f'{ed}.txt')], check=True)
        subprocess.run(['pdftotext', '-q', '-bbox-layout', src(pdf), work(f'{ed}_bbox.html')], check=True)
        print(f'  {pdf}: extracted')

if __name__ == '__main__':
    run()
