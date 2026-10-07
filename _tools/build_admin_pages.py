#!/usr/bin/env python3
"""Build the users, media and taxonomy (البيانات الوصفية) pages of CMS-final.

The HTML comes from CMS-improvements (checked against production on 2026-10-07).
Each page gets the CMS-final sidebar (from edit__post_type-article.html) with its
own menu item marked current, a few English labels in Arabic, and the links fixed
the same way as build_content_pages.py. The design and the hidden sections
(Rank Math, WPML language settings, profile options) are in custom.css.

البيانات الوصفية: one list page per taxonomy (WordPress has a copy per content type) and
one edit page per taxonomy. شجرة التصنيفات and المجموعات keep their hand-tuned
list pages and only get an edit page here; التصنيفات الفقهية is not built (it is
a parent inside شجرة التصنيفات).

ترتيب البيانات الوصفية (zad-icmss-taxonomy-order): one page per tab, built on the
المجموعات list page as a shell, with the plugin's markup (tabs, #tto_sortable list,
.save-order button). Omar's decisions (2026-10-07): no taxonomy radio table, no
«<type> — التصنيفات» heading, no plugin promo; the save button also sits above the
list; the page opens on شجرة التصنيفات. Drag and drop is in proto.js.

Run after build_content_pages.py:  python3 _tools/build_admin_pages.py
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_content_pages import (FINAL, RENAMES, add_class, classes, fix_links, remove_class, sidebar_template,  # noqa: E402
                                 soup, write)
import copy  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

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


# ترتيب البيانات الوصفية: (taxonomy, tab label, terms or the list page to read them from)
ORDER = 'admin__page-zad-icmss-taxonomy-order'
ORDER_TABS = [
    ('topic', 'شجرة التصنيفات', [
        ('التصنيفات الموضوعية', ['آداب الإسلام', 'آداب وأخلاق', 'الآداب والأخلاق والرقائق']),
        ('التصنيفات الفقهية', ['أصول الفقه', 'الفقه وأصوله', 'حقوق وواجبات']),
        ('التصنيفات العقدية', ['دورة العقيدة الواسطية', 'عقائد ونبوات']),
        ('الفنون', ['التفسير', 'الحديث', 'النحو'])]),
    ('article-type', 'المجموعات', 'edit-tags__post_type-article__taxonomy-article-type.html'),
    ('index', 'فهارس', 'edit-tags__post_type-audio-book-lesson__taxonomy-index.html'),
    ('course-index', 'فهارس الدورات', 'edit-tags__post_type-book-lesson__taxonomy-course-index.html'),
    ('book-index', 'فهارس الكتب', 'edit-tags__post_type-book__taxonomy-book-index.html'),
]


def order_name(tax):
    # the menu link (no taxonomy) opens the first tab
    return ORDER + ('.html' if tax == ORDER_TABS[0][0] else '__taxonomy-%s.html' % tax)


def order_terms(terms):
    """[(name, children)] from the tab's own list, or from a taxonomy list page."""
    if isinstance(terms, list):
        return terms
    page = soup(os.path.join(FINAL, terms))
    # sample terms with no Arabic letters (test junk like «cxvxv») are left out
    return [(t, []) for t in (a.get_text(strip=True) for a in page.select('#the-list .row-title'))
            if re.search('[\u0621-\u064A]', t)]


def build_order(shell, template):
    built = []
    n = [0]

    def items(page, terms):
        ul = page.new_tag('ul')
        for name, kids in terms:
            n[0] += 1
            li = page.new_tag('li', id='item_%d' % n[0], attrs={'class': 'term_type_li'})
            div = page.new_tag('div', attrs={'class': 'item'})
            span = page.new_tag('span')
            span.string = name
            div.append(span)
            li.append(div)
            if kids:
                sub = items(page, [(k, []) for k in kids])
                sub['class'] = 'children sortable'
                li.append(sub)
            ul.append(li)
        return ul

    for tax, label, terms in ORDER_TABS:
        page = soup(os.path.join(FINAL, shell))
        menu = copy.copy(template)
        mark(menu, ORDER + '.html')
        page.find(id='adminmenumain').replace_with(menu)
        page.title.string = 'ترتيب البيانات الوصفية › موقع مشكاة — ووردبريس'
        cls = [c for c in page.body['class'] if not c.startswith(('edit-tags', 'post-type-', 'taxonomy-', 'ac-wp-'))]
        page.body['class'] = cls[:cls.index('auto-fold')] + ['admin_page_zad-icmss-taxonomy-order'] + \
            cls[cls.index('auto-fold'):] + ['taxonomy-' + tax]
        body = page.find(id='wpbody-content')
        body.clear()
        tabs = ''.join('<li>%s<a class="%s" href="%s">%s</a></li>' % (
            ' | ' if i else '', 'current' if t == tax else '', order_name(t), lab)
            for i, (t, lab, _) in enumerate(ORDER_TABS))
        save = '<p class="submit"><a class="save-order button-primary" href="javascript:;">حفظ الترتيب</a></p>'
        body.append(BeautifulSoup(
            '<div class="wrap"><ul class="subsubsub">%s</ul><div class="clear"></div></div>'
            '<div class="wrap"><h2>ترتيب البيانات الوصفية</h2><div id="ajax-response"></div><div class="clear"></div>'
            '<form id="to_form" method="get"><div class="tto-top actions">%s</div>'
            '<div id="order-terms"><div id="post-body"><ul class="sortable" id="tto_sortable"></ul>'
            '<div class="clear"></div></div><div class="alignleft actions">%s</div></div></form></div>'
            '<div class="clear"></div>' % (tabs, save, save), 'html.parser'))
        ul = items(page, order_terms(terms))
        page.find(id='tto_sortable').extend(list(ul.children))
        name = order_name(tax)
        write(os.path.join(FINAL, name), page)
        built.append(name)
    return built


def mark(menu, target):
    """Open the menu item that links to `target` and mark that submenu entry current.
    القراء and المجموعات are marked by proto.js (it moves them under البيانات الوصفية)."""
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
    page = soup(src, RENAMES)
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

    built += build_order(LIST_OF['article-type'], template)

    existing = {os.path.basename(p) for p in glob.glob(os.path.join(FINAL, '*.html'))}
    changed = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(FINAL, '*.html'))) if fix_links(p, existing)]
    print('built %d pages; links fixed in %d pages' % (len(built), len(changed)))


if __name__ == '__main__':
    sys.exit(main())
