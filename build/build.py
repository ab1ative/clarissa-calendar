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
