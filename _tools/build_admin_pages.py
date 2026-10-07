#!/usr/bin/env python3
"""Build the users, media and taxonomy (التصنيفات) pages of CMS-final.

The HTML comes from CMS-improvements (checked against production on 2026-10-07).
Each page gets the CMS-final sidebar (from edit__post_type-article.html) with its
own menu item marked current, a few English labels in Arabic, and the links fixed
the same way as build_content_pages.py. The design and the hidden sections
(Rank Math, WPML language settings, profile options) are in custom.css.

التصنيفات: one list page per taxonomy (WordPress has a copy per content type) and
one edit page per taxonomy. شجرة التصنيفات and المجموعات keep their hand-tuned
list pages and only get an edit page here; التصنيفات الفقهية is not built (it is
a parent inside شجرة التصنيفات).

Run after build_content_pages.py:  python3 _tools/build_admin_pages.py
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_content_pages import (FINAL, add_class, classes, fix_links, remove_class, sidebar_template,  # noqa: E402
                                 soup, write)
import copy  # noqa: E402

# (source page in CMS-improvements, page the sidebar marks current)
PAGES = [
    ('users.html', 'users.html'),
    ('user-new.html', 'user-new.html'),
    ('profile.html', 'profile.html'),
    ('upload.html', 'upload.html'),
    ('media-new.html', 'media-new.html'),
    ('admin__page-wpml-media.html', 'admin__page-wpml-media.html'),
]
# taxonomy: (list page, edit page); None = the list page is hand-tuned, not built here
TAXONOMIES = {
    'public-tag': ('edit-tags__post_type-article__taxonomy-public-tag.html',
                   'term__post_type-article__tag_ID-226__taxonomy-public-tag.html'),
    'keyword': ('edit-tags__post_type-article__taxonomy-keyword.html',
                'term__post_type-article__tag_ID-16__taxonomy-keyword.html'),
    'index': ('edit-tags__post_type-audio-book-lesson__taxonomy-index.html',
              'term__post_type-audio-book-lesson__tag_ID-228__taxonomy-index.html'),
    'course-index': ('edit-tags__post_type-book-lesson__taxonomy-course-index.html',
                     'term__post_type-book-lesson__tag_ID-92__taxonomy-course-index.html'),
    'reciter': ('edit-tags__post_type-audio-book-lesson__taxonomy-reciter.html',
                'term__post_type-audio-book-lesson__tag_ID-212__taxonomy-reciter.html'),
    'book-index': ('edit-tags__post_type-book__taxonomy-book-index.html',
                   'term__post_type-book__tag_ID-116__taxonomy-book-index.html'),
    'topic': (None, 'term__post_type-article__tag_ID-38__taxonomy-topic.html'),
    'article-type': (None, 'term__post_type-article__tag_ID-12__taxonomy-article-type.html'),
}
LIST_OF = {'topic': 'edit-tags__post_type-article__taxonomy-topic.html',
           'article-type': 'edit-tags__post_type-article__taxonomy-article-type.html'}

# English text left in the source pages
ARABIC = {
    'Send the new user an email about their account': 'أرسل إلى العضو الجديد رسالة بريد إلكتروني بشأن حسابه',
}
# ترجمة الوسائط date filter: «كل التواريخ in أي لغة to أي لغة»
FILTER_WORDS = {'in': 'من', 'to': 'إلى'}


def mark(menu, target):
    """Open the menu item that links to `target` and mark that submenu entry current.
    القراء and المجموعات are marked by proto.js (it moves them under التصنيفات)."""
    a = next((x for x in menu.select('.wp-submenu a')
              if target in (x.get('href'), x.get('data-orig-href'))), None)
    if a is None or 'reciter' in target:
        return
    li = a.find_parent('li', class_='menu-top') or a.find_parent('li', id=True)
    top = li.find('a', recursive=False)
    for el in (li, top):
        remove_class(el, 'wp-not-current-submenu')
        add_class(el, 'wp-has-current-submenu', 'wp-menu-open')
    if top.has_attr('data-ariahaspopup'):
        del top['data-ariahaspopup']
    sub = a.find_parent('li')
    add_class(sub, 'current')
    add_class(a, 'current')
    a['aria-current'] = 'page'


def build(src, name, current, template):
    page = soup(src)
    menu = copy.copy(template)
    mark(menu, current)
    page.find(id='adminmenumain').replace_with(menu)
    for t in page.find_all(string=True):
        s = t.strip()
        if s in ARABIC:
            t.replace_with(t.replace(s, ARABIC[s]))
        elif name == 'admin__page-wpml-media.html' and s in FILTER_WORDS and t.parent.name == 'form':
            t.replace_with(t.replace(s, FILTER_WORDS[s]))
    # media icons saved without a file (all audio files in the sample)
    for img in page.select('img.is-non-image[src=""]'):
        img['src'] = 'assets/846b298392-audio.svg'
    write(os.path.join(FINAL, name), page)
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--improvements', default=os.path.join(os.path.dirname(FINAL), 'CMS-improvements'))
    args = ap.parse_args()
    template = sidebar_template()
    built = []
    for src, current in PAGES:
        built.append(build(os.path.join(args.improvements, src), src, current, template))
    for tax, (lst, term) in TAXONOMIES.items():
        listed = lst or LIST_OF[tax]
        if lst:
            built.append(build(os.path.join(args.improvements, lst), lst, listed, template))
        built.append(build(os.path.join(args.improvements, term), term, listed, template))

    existing = {os.path.basename(p) for p in glob.glob(os.path.join(FINAL, '*.html'))}
    changed = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(FINAL, '*.html'))) if fix_links(p, existing)]
    print('built %d pages; links fixed in %d pages' % (len(built), len(changed)))


if __name__ == '__main__':
    sys.exit(main())
