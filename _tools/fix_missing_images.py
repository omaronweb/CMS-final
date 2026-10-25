#!/usr/bin/env python3
"""Point images whose file is missing from assets/ to one that is there.

The pages were captured with thumbnails (mostly «-150x150») that were never
copied into assets/. Each missing file gets the same picture in another size
when assets/ has it, otherwise one of the site's own pictures (unused ones
first). One mapping for all pages, so a post shows the same image on its list
row and its edit page. Running it twice changes nothing.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)
IMG = re.compile(r'\.(jpe?g|png|webp)$', re.I)
REF = re.compile(r'((?:src|srcset)=")assets/([^" ]+)')


def base(name):
    """«1025654c30-name-150x150.jpg» → «name.jpg»"""
    name = re.sub(r'^[0-9a-f]{10}-', '', name)
    return re.sub(r'-\d+x\d+(?=\.)', '', name).lower()


def main():
    os.chdir(FINAL)
    assets = sorted(os.path.basename(p) for p in glob.glob('assets/*') if IMG.search(p))
    by_base = {}
    for a in assets:
        by_base.setdefault(base(a), []).append(a)
    pages = sorted(glob.glob('*.html'))
    missing = sorted({m.group(2) for p in pages for m in REF.finditer(open(p, encoding='utf-8').read())
                      if not os.path.exists('assets/' + m.group(2))})
    used = {m.group(2) for p in pages for m in REF.finditer(open(p, encoding='utf-8').read())}
    # pictures for the rest: content images (featured-image sizes), not icons or screenshots
    # (unused ones first, then the others in turn)
    content = [a for a in assets if re.search(r'-(300x167|150x150)\.', a)]
    pool = [a for a in content if a not in used] + [a for a in content if a in used]
    mapping = {}
    for i, m in enumerate(x for x in missing if not by_base.get(base(x))):
        mapping[m] = pool[i % len(pool)]
    for m in missing:
        same = by_base.get(base(m))
        if same:
            mapping[m] = sorted(same, key=lambda a: ('150x150' not in a, a))[0]
    for p in pages:
        s = open(p, encoding='utf-8').read()
        t = REF.sub(lambda m: m.group(1) + 'assets/' + mapping.get(m.group(2), m.group(2)), s)
        if t != s:
            open(p, 'w', encoding='utf-8').write(t)
    print('%d missing images, %d mapped' % (len(missing), len(mapping)))


if __name__ == '__main__':
    main()
