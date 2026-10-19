#!/usr/bin/env python3
"""Build the users, media and taxonomy (التصنيفات) pages of CMS-final.

The HTML comes from CMS-improvements (checked against production on 2026-10-07).
Each page gets the CMS-final sidebar (from edit__post_type-article.html) with its
own menu item marked current, a few English labels in Arabic, and the links fixed
the same way as build_content_pages.py. The design and the hidden sections
(Rank Math, WPML language settings, profile options) are in custom.css.

التصنيفات: one list page per taxonomy (WordPress has a copy per content type) and
one edit page per taxonomy. فروع التصنيفات keeps its hand-tuned list page and
only gets an edit page here; التصنيفات الفقهية is not built (it is
a parent inside فروع التصنيفات).

ترتيب التصنيفات (zad-icmss-taxonomy-order): one page per tab, built on the
فروع التصنيفات list page as a shell, with the plugin's markup (tabs, #tto_sortable list,
.save-order button). Omar's decisions (2026-10-07): no taxonomy radio table, no
«<type> — التصنيفات» heading, no plugin promo; the save button also sits above the
list; the page opens on فروع التصنيفات. Drag and drop is in proto.js.

Run after build_content_pages.py:  python3 _tools/build_admin_pages.py
"""
import argparse
import glob
import json
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
    'reciter': ('edit-tags__post_type-audio-book-lesson__taxonomy-reciter.html',
                'term__post_type-audio-book-lesson__tag_ID-212__taxonomy-reciter.html'),
    'book-index': ('edit-tags__post_type-book__taxonomy-book-index.html',
                   'term__post_type-book__tag_ID-116__taxonomy-book-index.html'),
    'topic': (None, 'term__post_type-article__tag_ID-38__taxonomy-topic.html'),
}
LIST_OF = {'topic': 'edit-tags__post_type-article__taxonomy-topic.html'}
# الكلمات المفتاحية، المجموعات، فهارس الدورات and فهارس were deleted (Omar, 2026-10-15/18): no pages

# English text left in the source pages
ARABIC = {
    'Send the new user an email about their account': 'أرسل إلى العضو الجديد رسالة بريد إلكتروني بشأن حسابه',
}
# ترجمة الوسائط date filter: «كل التواريخ in أي لغة to أي لغة»
FILTER_WORDS = {'in': 'من', 'to': 'إلى'}


# ترتيب التصنيفات: (taxonomy, tab label, terms or the list page to read them from)
ORDER = 'admin__page-zad-icmss-taxonomy-order'
ORDER_TABS = [
    ('topic', 'فروع التصنيفات', [
        ('الموضوعية', ['آداب الإسلام', 'آداب وأخلاق', 'الآداب والأخلاق والرقائق']),
        ('الفقهية', ['أصول الفقه', 'الفقه وأصوله', 'حقوق وواجبات']),
        ('العقدية', ['دورة العقيدة الواسطية', 'عقائد ونبوات']),
        ('الفنون', ['التفسير', 'الحديث', 'النحو'])]),
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
        page.title.string = 'ترتيب التصنيفات › موقع مشكاة — ووردبريس'
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
            '<div class="wrap"><h2>ترتيب التصنيفات</h2><div id="ajax-response"></div><div class="clear"></div>'
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


# قوائم المحتويات (Omar, 2026-10-15): a taxonomy under التصنيفات whose
# terms each point at one item: pick the content type, then the item of that type.
# Built on the فهارس الكتب pages as shells; the item list is filled by proto.js
# from the JSON in the page (titles from the list pages).
TOC_LIST, TOC_EDIT = 'edit-tags__taxonomy-toc.html', 'term__tag_ID-301__taxonomy-toc.html'
TOC_SAMPLES = [  # (name, content type, item)
    ('فهرس كتاب حصن المسلم', 'audio-book-series', 'كتاب حصن المسلم من أذكار الكتاب والسنة'),
    ('قائمة محتويات شرح اقتضاء الصراط المستقيم', 'book-series', 'شرح كتاب اقتضاء الصراط المستقيم'),
    ('فهرس شرح الأربعين النووية', 'scientific-series', 'سلسلة شرح الأربعون النووية'),
    ('فهرس وصايا سورة الإسراء', 'interpret-series', 'وقفات مع وصايا سورة الإسراء'),
]


def toc_types():
    """{type: {'label', 'posts'}} for every content type with items, from its list page."""
    from build_content_pages import INDEX_NAMES
    out = {}
    for f in sorted(glob.glob(os.path.join(FINAL, 'edit__post_type-*.html'))):
        ptype = os.path.basename(f)[len('edit__post_type-'):-len('.html')]
        page = soup(f)
        posts = [a.get_text(strip=True) for a in page.select('#the-list .row-title')]
        posts = [t for t in posts if t and t != '(بدون عنوان)']
        h = page.select_one('h1.wp-heading-inline')
        if posts and h:
            out[ptype] = {'label': INDEX_NAMES.get(ptype, h.get_text(strip=True)), 'posts': posts}
    return out


def toc_selects(page, types, selected=None):
    """The «نوع المحتوى» and «المادة» selects (proto.js fills the second)."""
    order = sorted(types, key=lambda t: types[t]['label'])
    sel_type, sel_post = selected or ('', '')
    type_sel = page.new_tag('select', id='toc-content-type', attrs={'name': 'toc_content_type', 'class': 'cms-toc-type',
                                                                     'aria-required': 'true'})
    o = page.new_tag('option', value='')
    o.string = '— اختر نوع المحتوى —'
    type_sel.append(o)
    for t in order:
        o = page.new_tag('option', value=t)
        o.string = types[t]['label']
        if t == sel_type:
            o['selected'] = 'selected'
        type_sel.append(o)
    post_sel = page.new_tag('select', id='toc-post', attrs={'name': 'toc_post', 'class': 'cms-toc-post',
                                                         'aria-required': 'true', 'data-selected': sel_post})
    o = page.new_tag('option', value='')
    o.string = '— اختر نوع المحتوى أولًا —'
    post_sel.append(o)
    return type_sel, post_sel


def toc_data(page, types):
    tag = page.new_tag('script', id='cms-toc-posts', type='application/json')
    tag.string = json.dumps({t: v['posts'] for t, v in types.items()}, ensure_ascii=False)
    return tag


# «العنصر الأب» (Omar, 2026-10-19): after «المادة», the entry this one sits under, from the
# entries of the same المادة (proto.js fills it). Sample entries for the sample materials.
TOC_CHAPTERS = ['الباب الأول', 'الباب الثاني', 'الباب الثالث']
PARENT_HELP = 'العنصر الذي يندرج تحته هذا العنصر في قائمة محتويات المادة المختارة.'


def toc_parent_select(page, exclude=None):
    sel = page.new_tag('select', id='toc-parent', attrs={'name': 'toc_parent', 'class': 'cms-toc-parent'})
    o = page.new_tag('option', value='')
    o.string = 'بدون'
    sel.append(o)
    entries = {}
    for name, _, post in TOC_SAMPLES:
        entries.setdefault(post, [])
        if name != exclude:
            entries[post].append(name)
        entries[post] += [c for c in TOC_CHAPTERS if c not in entries[post]]
    data = page.new_tag('script', id='cms-toc-parents', type='application/json')
    data.string = json.dumps(entries, ensure_ascii=False)
    return sel, data


def toc_texts(page):
    for t in page.select_one('#wpbody-content').find_all(string=True):
        v = str(t)
        for a, b in (('أضف فهرس الكتب جديد', 'أضف فهرسًا أو قائمة محتويات'), ('تحديث فهرس الكتب', 'تحديث'),
                     ('تحرير فهرس الكتب', 'تحرير الفهرس أو قائمة المحتويات'), ('ترجمة فهرس الكتب', 'ترجمة الفهرس'),
                     ('فهارس الكتب', 'قوائم المحتويات')):
            v = v.replace(a, b)
        if v != str(t):
            t.replace_with(v)
    for inp in page.select('#wpbody-content input[value]'):
        inp['value'] = inp['value'].replace('بحث فهارس الكتب', 'بحث').replace('أضف فهرس الكتب جديد', 'أضف')
    page.title.string = page.title.string.replace('تحرير فهرس الكتب', 'تحرير الفهرس أو قائمة المحتويات') \
        .replace('فهارس الكتب', 'قوائم المحتويات')
    cls = [c for c in page.body['class'] if c not in ('post-type-book', 'taxonomy-book-index', 'ac-wp-taxonomy_book-index')]
    page.body['class'] = cls + ['taxonomy-toc']


def field_desc(page, text):
    d = page.new_tag('p', attrs={'class': 'description'})
    d.string = text
    return d


TYPE_HELP = 'نوع المحتوى الذي ينتمي إليه الفهرس.'
POST_HELP = 'المادة التي يعرض الفهرس محتوياتها، من نوع المحتوى المختار.'


def core_styles(page):
    """The book-index list capture lost WordPress's core admin stylesheet; put it back."""
    if page.find('link', href=lambda h: h and 'd214292bb0-load-styles' in h):
        return
    part = page.find('link', href=lambda h: h and 'c5e412a223-load-styles' in h)
    if part:
        part.insert_before(page.new_tag('link', href='assets/d214292bb0-load-styles.php.css',
                                        media='all', rel='stylesheet'))


def topic_look(page, shell):
    """Give a page the stylesheets of a فروع التصنيفات page (`shell`), so قوائم المحتويات and
    شجرات التصنيف look the same (Omar, 2026-10-19). The book-index captures carry other
    plugins' CSS and miss some of the core and theme CSS."""
    src = soup(os.path.join(FINAL, shell))
    is_css = lambda t: t.name == 'style' or (t.name == 'link' and 'stylesheet' in (t.get('rel') or []))
    for t in page.head.find_all(is_css) + page.body.find_all(is_css):
        t.decompose()
    title = page.head.title
    for t in src.head.find_all(is_css):
        page.head.append(copy.copy(t))
    first = page.body.contents[0] if page.body.contents else None
    for t in src.body.find_all(is_css):
        if first is not None:
            first.insert_before(copy.copy(t))
        else:
            page.body.append(copy.copy(t))
    assert title is not None


def build_toc(template):
    types = toc_types()
    # list page
    page = soup(os.path.join(FINAL, TAXONOMIES['book-index'][0]))
    page.find(id='adminmenumain').replace_with(copy.copy(template))
    toc_texts(page)
    form = page.select_one('#addtag')
    for sel in ('.term-parent-wrap', '#acf-term-fields', '#acf-form-data'):
        for x in form.select(sel):
            x.decompose()
    type_sel, post_sel = toc_selects(page, types)
    parent_sel, parent_data = toc_parent_select(page)
    after = form.select_one('.term-name-wrap')
    for cls, label, sel, helptext in (('term-toc-parent-wrap', 'العنصر الأب', parent_sel, PARENT_HELP),
                                      ('term-post-wrap', 'المادة', post_sel, POST_HELP),
                                      ('term-content-type-wrap', 'نوع المحتوى', type_sel, TYPE_HELP)):
        req = '' if cls == 'term-toc-parent-wrap' else 'form-required '
        div = page.new_tag('div', attrs={'class': 'form-field ' + req + cls})
        lab = page.new_tag('label', attrs={'for': sel['id']})
        lab.string = label
        div.extend([lab, sel, field_desc(page, helptext)])
        after.insert_after(div)
    # columns: الاسم، نوع المحتوى، المادة، الاسم اللطيف (no count)
    for row in page.select('table.wp-list-table thead tr, table.wp-list-table tfoot tr'):
        desc = row.find(['th'], class_='column-description')
        slug = row.find(['th'], class_='column-slug')
        posts = row.find(['th'], class_='column-posts')
        new_post = copy.copy(desc)
        for th, label, key in ((desc, 'نوع المحتوى', 'content-type'), (new_post, 'المادة', 'post')):
            th['class'] = [c.replace('column-description', 'column-' + key) for c in th['class']]
            if th.get('id'):
                th['id'] = key
            th['abbr'] = label
            th.select_one('a > span').string = label
        desc.insert_after(new_post)
        if posts:
            posts.decompose()
    tmpl = page.select_one('#the-list tr')
    body = tmpl.parent
    for i, (name, ptype, post) in enumerate(TOC_SAMPLES):
        tr = copy.copy(tmpl)
        tid = 301 + i
        tr['id'], tr['data-id'] = 'tag-%d' % tid, str(tid)
        for a in tr.select('a.row-title, .row-actions .edit a'):
            a['href'] = TOC_EDIT
        tr.select_one('a.row-title').string = name
        tr.select_one('.row-title')['aria-label'] = '“%s” (تحرير)' % name
        for d in tr.select('#inline_116 .name'):
            d.string = name
        tr.select_one('.check-column input')['value'] = str(tid)
        tr.select_one('.check-column input')['id'] = 'cb-select-%d' % tid
        sr = tr.select_one('.check-column .screen-reader-text')
        if sr:
            sr.string = 'تحديد ' + name
        desc = tr.select_one('td.column-description')
        desc['class'] = ['content-type', 'column-content-type']
        desc['data-colname'] = 'نوع المحتوى'
        desc.clear()
        desc.string = types[ptype]['label']
        td = page.new_tag('td', attrs={'class': 'post column-post', 'data-colname': 'المادة'})
        td.string = post
        desc.insert_after(td)
        slug = tr.select_one('td.column-slug')
        slug.string = str(632 + i)
        tr.select_one('td.column-posts').decompose()
        body.append(tr)
    tmpl.decompose()
    for n in page.select('.displaying-num'):
        n.string = '%d عناصر' % len(TOC_SAMPLES)
    form.insert(0, toc_data(page, types))  # before proto.js runs
    form.insert(1, parent_data)
    topic_look(page, LIST_OF['topic'])
    write(os.path.join(FINAL, TOC_LIST), page)
    # the shell itself (فهارس الكتب) has the same gap
    shell = soup(os.path.join(FINAL, TAXONOMIES['book-index'][0]))
    core_styles(shell)
    write(os.path.join(FINAL, TAXONOMIES['book-index'][0]), shell)

    # edit page (the first sample)
    name, ptype, post = TOC_SAMPLES[0]
    page = soup(os.path.join(FINAL, TAXONOMIES['book-index'][1]))
    page.find(id='adminmenumain').replace_with(copy.copy(template))
    toc_texts(page)
    form = page.select_one('#edittag')
    for x in form.select('tr.term-parent-wrap, tr.acf-field'):
        x.decompose()
    for h in form.find_all('h2'):  # the empty book-index ACF group heading
        if 'حقول' in h.get_text():
            t = h.find_next_sibling('table')
            if t and not t.get_text(strip=True):
                t.decompose()
            h.decompose()
    form.select_one('#name')['value'] = name
    form.select_one('#slug')['value'] = '632'
    type_sel, post_sel = toc_selects(page, types, (ptype, post))
    parent_sel, parent_data = toc_parent_select(page, exclude=name)
    after = form.select_one('tr.term-name-wrap')
    for cls, label, sel, helptext in (('term-toc-parent-wrap', 'العنصر الأب', parent_sel, PARENT_HELP),
                                      ('term-post-wrap', 'المادة', post_sel, POST_HELP),
                                      ('term-content-type-wrap', 'نوع المحتوى', type_sel, TYPE_HELP)):
        req = '' if cls == 'term-toc-parent-wrap' else 'form-required '
        tr = page.new_tag('tr', attrs={'class': 'form-field ' + req + cls})
        th = page.new_tag('th', scope='row')
        lab = page.new_tag('label', attrs={'for': sel['id']})
        lab.string = label
        th.append(lab)
        td = page.new_tag('td')
        td.extend([sel, field_desc(page, helptext)])
        tr.extend([th, td])
        after.insert_after(tr)
    form.insert(0, toc_data(page, types))
    form.insert(1, parent_data)
    topic_look(page, TAXONOMIES['topic'][1])
    write(os.path.join(FINAL, TOC_EDIT), page)
    return [TOC_LIST, TOC_EDIT]


# شجرات التصنيف (Omar, 2026-10-18): the trees of فروع التصنيفات. Each tree is only a
# name; the trees are the top level of the فروع التصنيفات box on the add/edit pages,
# shown as headings without a checkbox (proto.js). الموضوعية is always on (it is
# selected and disabled in the Aalaam wizard), so it has no «حذف».
TREES_LIST, TREES_EDIT = 'edit-tags__taxonomy-tree.html', 'term__tag_ID-402__taxonomy-tree.html'
TREES = ['الموضوعية', 'الفقهية', 'العقدية', 'الفنون']


def tree_texts(page):
    for t in page.select_one('#wpbody-content').find_all(string=True):
        v = str(t)
        for a, b in (('أضف فهرسًا أو قائمة محتويات', 'أضف شجرة تصنيف'),
                     ('تحرير الفهرس أو قائمة المحتويات', 'تحرير شجرة التصنيف'), ('ترجمة الفهرس', 'ترجمة الشجرة'),
                     ('قوائم المحتويات', 'شجرات التصنيف'), ('4 عناصر', '%d عناصر' % len(TREES))):
            v = v.replace(a, b)
        if v != str(t):
            t.replace_with(v)
    page.title.string = page.title.string.replace('تحرير الفهرس أو قائمة المحتويات', 'تحرير شجرة التصنيف') \
        .replace('قوائم المحتويات', 'شجرات التصنيف')
    page.body['class'] = [c for c in page.body['class'] if c != 'taxonomy-toc'] + ['taxonomy-tree']
    for x in page.select('#cms-toc-posts, .term-content-type-wrap, .term-post-wrap, .term-slug-wrap, '
                         '.term-description-wrap, .term-toc-parent-wrap, #cms-toc-parents, .column-content-type, .column-post, .column-slug'):
        x.decompose()


def build_trees(template):
    page = soup(os.path.join(FINAL, TOC_LIST))
    tree_texts(page)
    rows = page.select('#the-list tr')
    tmpl = copy.copy(rows[0])
    for r in rows:
        r.decompose()
    body = page.select_one('#the-list')
    for i, name in enumerate(TREES):
        tr = copy.copy(tmpl)
        tid = 401 + i
        tr['id'], tr['data-id'] = 'tag-%d' % tid, str(tid)
        for a in tr.select('a.row-title, .row-actions .edit a'):
            a['href'] = TREES_EDIT
        tr.select_one('a.row-title').string = name
        tr.select_one('a.row-title')['aria-label'] = '“%s” (تحرير)' % name
        for d in tr.select('.hidden .name'):
            d.string = name
        cb = tr.select_one('.check-column input')
        cb['value'], cb['id'] = str(tid), 'cb-select-%d' % tid
        sr = tr.select_one('.check-column .screen-reader-text')
        if sr:
            sr.string = 'تحديد ' + name
        if i == 0:  # always on: no delete
            for x in tr.select('.row-actions .delete'):
                x.decompose()
            cb['disabled'] = ''
        body.append(tr)
    write(os.path.join(FINAL, TREES_LIST), page)

    page = soup(os.path.join(FINAL, TOC_EDIT))
    tree_texts(page)
    page.select_one('#name')['value'] = TREES[1]
    write(os.path.join(FINAL, TREES_EDIT), page)
    return [TREES_LIST, TREES_EDIT]


def add_tree_field(name):
    """فروع التصنيفات add/edit form: «شجرة التصنيف» select (the trees of شجرات التصنيف)
    before «التصنيف الأب» (Omar, 2026-10-19)."""
    path = os.path.join(FINAL, name)
    page = soup(path)
    if page.select_one('.term-tree-wrap'):
        return
    wrap = page.select_one('.term-parent-wrap')
    opts = ''.join('<option value="%d"%s>%s</option>' % (401 + i, ' selected=""' if i == 0 else '', t)
                   for i, t in enumerate(TREES))
    sel = '<select class="postform" id="tree" name="tree">%s</select>' % opts
    if wrap.name == 'tr':
        html = ('<tr class="form-field term-tree-wrap"><th scope="row"><label for="tree">شجرة التصنيف</label></th>'
                '<td>%s</td></tr>' % sel)
    else:
        html = '<div class="form-field term-tree-wrap"><label for="tree">شجرة التصنيف</label>%s</div>' % sel
    wrap.insert_before(BeautifulSoup(html, 'html.parser'))
    write(path, page)


def add_tree_column(name):
    """فروع التصنيفات list: «شجرة التصنيف» column after الاسم (Omar, 2026-10-19). proto.js nests
    the first 12 rows (its demo levels), so a child shows its top-level row's tree."""
    path = os.path.join(FINAL, name)
    page = soup(path)
    if page.select_one('.column-tree'):
        return
    for th in page.select('table.wp-list-table :is(thead, tfoot) .column-name'):
        th.insert_after(BeautifulSoup('<th class="manage-column column-tree" scope="col">شجرة التصنيف</th>',
                                      'html.parser'))
    levels = [0, 1, 2, 1, 2, 3, 0, 1, 1, 1, 0, 0]  # proto.js «Demo hierarchy»
    roots = {0: 'الموضوعية', 6: 'الفقهية', 10: 'العقدية', 11: 'الفنون'}
    tree = TREES[0]
    for i, tr in enumerate(page.select('#the-list > tr')):
        if i < len(levels) and levels[i] == 0 or i >= len(levels):
            tree = roots.get(i, TREES[0])
        tr.select_one('td.column-name').insert_after(BeautifulSoup(
            '<td class="tree column-tree" data-colname="شجرة التصنيف">%s</td>' % tree, 'html.parser'))
    write(path, page)


def mark(menu, target):
    """Open the menu item that links to `target` and mark that submenu entry current.
    القراء is marked by proto.js (it moves it under الكتب الصوتية)."""
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

    built += build_order(LIST_OF['topic'], template)
    built += build_toc(template)
    built += build_trees(template)
    for name in (LIST_OF['topic'], TAXONOMIES['topic'][1]):
        add_tree_field(name)
    add_tree_column(LIST_OF['topic'])

    existing = {os.path.basename(p) for p in glob.glob(os.path.join(FINAL, '*.html'))}
    changed = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(FINAL, '*.html'))) if fix_links(p, existing)]
    print('built %d pages; links fixed in %d pages' % (len(built), len(changed)))


if __name__ == '__main__':
    sys.exit(main())
