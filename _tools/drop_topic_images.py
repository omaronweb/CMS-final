#!/usr/bin/env python3
"""فروع التصنيفات (taxonomy «topic») has no images field (Omar, 2026-10-26).

Removes the ACF «الصور» repeater (topic_fields_images, whose rows hold the «صورة»
image field) from the topic add form and the topic term edit pages. It is the
only field of «حقول المواضيع», so its section goes with it. Other taxonomies'
image fields (فهارس الكتب) stay.

Run it after build_admin_pages.py. Running it twice changes nothing.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)
FIELD = 'topic_fields_images'


def element_end(s, i, tag):
    """End of the <tag> element opening at s[i] (nested ones counted)."""
    depth = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return i + t.end()
    raise ValueError('unbalanced <%s>' % tag)


def drop(s):
    # add form: the ACF fields box holds only this field
    m = re.search(r'<div class="acf-fields -clear" id="acf-term-fields">\s*<div class="acf-field [^"]*" [^>]*data-name="%s"' % FIELD, s)
    if m:
        s = s[:m.start()] + s[element_end(s, m.start(), 'div'):]
    # term edit page: «حقول المواضيع» and its table hold only this field
    m = re.search(r'<h2>حقول المواضيع</h2>\s*(<table class="form-table">)\s*<tbody>\s*<tr class="acf-field [^"]*" [^>]*data-name="%s"' % FIELD, s)
    if m:
        s = s[:m.start()] + s[element_end(s, m.start(1), 'table'):]
    return s


def main():
    pages = glob.glob(os.path.join(FINAL, 'edit-tags__*taxonomy-topic.html')) + \
        glob.glob(os.path.join(FINAL, 'term__*taxonomy-topic.html'))
    for path in sorted(pages):
        s = open(path, encoding='utf-8').read()
        t = drop(s)
        if t != s:
            open(path, 'w', encoding='utf-8').write(t)
            print('removed from', os.path.basename(path))


if __name__ == '__main__':
    main()
