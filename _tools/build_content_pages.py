#!/usr/bin/env python3
"""Build the list, add and edit pages of every content type in CMS-final.

The HTML comes from CMS-improvements (one list page, one add page and one edit
page per post type). Each page gets what the article pages already have in
CMS-final:

- the CMS-final sidebar, taken from edit__post_type-article.html, with the
  page's own menu item marked current;
- list pages: the columns Omar picked (list-pages-columns.html), other columns
  hidden (still in Screen Options), ordered checkbox, image, title, content,
  excerpt, others, then «حالة النشر» and «آخر تعديل» last;
- add / edit pages: the article rules from improvements.html (fields in the
  live order, «الصور» and required fields outside «حقول إضافية», removed boxes
  and fields, Arabic labels borrowed from the live CMS in cms-testing, «+ أضف»
  links, open excerpt box with the excerpt guide link, Arabic SEO title).

Afterwards every page in CMS-final gets its links fixed: links to pages that
exist are live, links to pages that don't are `proto-dead` (they show a toast).

Run from anywhere:  python3 _tools/build_content_pages.py
Expects CMS-improvements and cms-testing checked out next to CMS-final
(override with --improvements / --testing).
"""
import argparse
import copy
import glob
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)

# Post types built by this script. article keeps its hand-tuned pages, and
# public-config is the single «الإعدادات العامة» page (post__action-edit__post-702.html).
SKIP = {'article', 'public-config'}

# Lesson types that proto.js folds into their series' menu item.
SERIES_OF = {
    'book-lesson': 'book-series',
    'scientific-lesson': 'scientific-series',
    'radio-program-lesson': 'radio-program-series',
    'tv-program-lesson': 'tv-program-series',
    'book-page': 'book',
    'book-browser-lesson': 'book-browser-series',
    'audio-book-lesson': 'audio-book-series',
}

# Post types that CMS-improvements doesn't have, built from a look-alike type's
# pages: {new type: (source type, fake post id for its edit page, text replacements)}.
# audio-book-series has the same fields as book-browser-series on the live CMS
# (حالة السلسلة، الصور، تاريخ الإلقاء) and no شجرة التصنيفات box.
AR = r'(?<![\u0621-\u064A])%s(?![\u0621-\u064A])'  # whole words (Arabic letters, not \u00AB\u060C\u00BB)
DERIVED = {
    'audio-book-series': ('book-browser-series', ('5620', '95620'), [
        ('book-browser-series', 'audio-book-series'),
        ('book_browser_series', 'audio_book_series'),
        (AR % 'حقول سلاسل متصفح الكتب', 'حقول سلاسل الكتب الصوتية'),
        (AR % 'لغة هذا متصفح الكتاب', 'لغة هذا الكتاب الصوتي'),
        (AR % 'متصفح متصفح كتاب', 'كتاب'),
        (AR % 'متصفح كتاب', 'كتاب'),
        (AR % 'سلسلة متصفح كتب', 'سلسلة كتب صوتية'),
        (AR % 'متصفح الكتب', 'الكتب الصوتية'),
        (AR % 'متصفح الكتاب', 'الكتاب الصوتي'),
    ], ['topicdiv']),
}

# Names changed on the pages themselves (Omar, 2026-10-07): التفسير → الدورات
RENAMES = [
    (AR % 'حقول سلاسل التفسير', 'حقول الدورات'),
    (AR % 'دروس التفسير', 'دروس الدورات'),
    (AR % 'درس التفسير', 'درس الدورة'),
    (AR % 'أضف درس تفسير', 'أضف درس دورة'),
    # the generic term (menu item, ترتيب page, field labels); names like شجرة التصنيفات
    # and التصنيفات الفقهية stay, and so does the quoted plugin heading «الدروس — التصنيفات»
    (r'(?<![\u0621-\u064A])(?<!شجرة )(?<!— )التصنيفات(?![\u0621-\u064A])(?! (?:الموضوعية|الفقهية|العقدية))',
     'البيانات الوصفية'),
]
RENAME_PAGES = {'interpret-series': [(AR % 'دورات', 'الدورات')], 'interpret-lesson': []}

# Side boxes (and the content editor) the live CMS doesn't show for a type
DROP_BOXES = {'fatwa': ['tagsdiv-keyword', 'postdivrich']}  # postdivrich: no المحتوى editor on the live fatwa page

LATIN = re.compile(r'[A-Za-z]{3,}')

# ACF fields: canonical order inside a content type's field group (suffix after
# «<type>_fields_»). Unlisted fields keep their source order after these.
ORDER = ['question', 'answer', 'images', 'cover_images', 'status', 'youtube_id', 'audios', 'videos',
         'video_url', 'pdfs', 'release_date', 'transcript', 'clips', 'view_count', 'words']
# Only required fields stay outside «حقول إضافية» (Omar, 2026-10-07)
OUTSIDE = set()
# Removed like on the article pages (حقول المحرر)
DROP = {'editor_draft', 'workflow_stage'}

YOUTUBE_PLACEHOLDER = 'https://www.youtube.com/watch?v=...'
VIDEO_URL_DESC = 'رابط مباشر لملف الفيديو ينتهي بامتداده، مثل: https://www.example.com/video.mp4'
EXCERPT_DOC = 'docs/excerpt.html'
SEO_TITLE = 'تحسين الوصول لمحركات البحث (SEO)'


def soup(path, subs=()):
    with open(path, encoding='utf-8') as f:
        src = f.read()
    for a, b in subs:
        src = re.sub(a, b, src)
    return BeautifulSoup(src, 'html.parser')


def write(path, s):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(s))


def classes(el):
    return el.get('class') or []


def add_class(el, *names):
    c = classes(el)
    for n in names:
        if n not in c:
            c.append(n)
    el['class'] = c


def remove_class(el, *names):
    c = [x for x in classes(el) if x not in names]
    if c:
        el['class'] = c
    elif el.has_attr('class'):
        del el['class']


# ── Sidebar ─────────────────────────────────────────────────────────────────

def sidebar_template():
    s = soup(os.path.join(FINAL, 'edit__post_type-article.html'))
    menu = s.find(id='adminmenumain')
    # clear the article page's current state
    for li in menu.select('#adminmenu > li'):
        if 'wp-has-current-submenu' in classes(li):
            for el in (li, li.find('a', recursive=False)):
                remove_class(el, 'wp-has-current-submenu', 'wp-menu-open')
                add_class(el, 'wp-not-current-submenu')
            li.find('a', recursive=False)['data-ariahaspopup'] = ''
    for el in menu.select('.wp-submenu .current'):
        remove_class(el, 'current')
    for a in menu.select('[aria-current]'):
        del a['aria-current']
    return menu


def mark_current(menu, ptype, sub_index):
    """Open the post type's menu item; sub_index 0 = «الكل», 1 = «أضف»."""
    def open_item(li):
        a = li.find('a', recursive=False)
        for el in (li, a):
            remove_class(el, 'wp-not-current-submenu')
            add_class(el, 'wp-has-current-submenu', 'wp-menu-open')
        if a.has_attr('data-ariahaspopup'):
            del a['data-ariahaspopup']

    li = menu.find(id='menu-posts-' + ptype)
    if li is None:
        return
    open_item(li)
    # proto.js folds lesson items into their series' item
    if ptype in SERIES_OF and menu.find(id='menu-posts-' + SERIES_OF[ptype]) is not None:
        open_item(menu.find(id='menu-posts-' + SERIES_OF[ptype]))
    subs = [x for x in li.select('.wp-submenu > li') if 'wp-submenu-head' not in classes(x)]
    if sub_index < len(subs):
        sub = subs[sub_index]
        add_class(sub, 'current')
        a = sub.find('a')
        add_class(a, 'current')
        a['aria-current'] = 'page'


def put_sidebar(page, template, ptype, sub_index):
    menu = copy.copy(template)
    mark_current(menu, ptype, sub_index)
    page.find(id='adminmenumain').replace_with(menu)


# ── List pages ──────────────────────────────────────────────────────────────

def column_key(cell):
    if 'check-column' in classes(cell):
        return 'cb'
    for c in classes(cell):
        if c.startswith('column-'):
            return c[7:]
    return None


def header_text(th):
    t = th.get_text(' ', strip=True)
    return re.sub(r'\s*Sort (ascending|descending)\.?', '', t).strip()


def apply_columns(page, keep):
    table = page.select_one('table.wp-list-table')
    head = table.select_one('thead tr')
    cols = []  # (key, label, hidden)
    for cell in head.find_all(['th', 'td'], recursive=False):
        cols.append((column_key(cell), header_text(cell), 'hidden' in classes(cell)))

    # which columns stay visible: one per picked label (the visible one if the
    # label appears twice)
    visible = set()
    for label in keep:
        same = [c for c in cols if c[1] == label]
        if not same:
            continue
        pick = next((c for c in same if not c[2]), same[0])
        visible.add(pick[0])
    visible.add('cb')

    images = {'الصور', 'صور الغلاف'}
    def rank(i_col):
        i, (key, label, _) = i_col
        if key == 'cb':
            return (0, i)
        if label in images:
            return (1, i)
        if key == 'title':
            return (2, i)
        if label == 'المحتوى':
            return (3, i)
        if label == 'المقتطف':
            return (4, i)
        if label == 'حالة النشر':
            return (8, i)
        if key == 'lastmodified':
            return (9, i)
        return (5, i)
    order = [c[0] for _, c in sorted(enumerate(cols), key=rank)]

    # hide / show
    for key, _, _ in cols:
        if key in (None, 'cb'):
            continue
        for cell in table.select('.column-' + key):
            if key in visible:
                remove_class(cell, 'hidden')
            else:
                add_class(cell, 'hidden')
    for cb in page.select('#adv-settings .hide-column-tog'):
        if cb.get('value') in visible:
            cb['checked'] = ''
        elif cb.has_attr('checked'):
            del cb['checked']

    # reorder cells in every row that has exactly these columns
    for tr in table.select('thead tr, tfoot tr, #the-list > tr'):
        cells = tr.find_all(['th', 'td'], recursive=False)
        keys = [column_key(c) for c in cells]
        if sorted(k or '' for k in keys) != sorted(k or '' for k in order) or None in keys:
            continue
        by_key = dict(zip(keys, cells))
        # keep the whitespace between cells where it was
        for c in cells:
            c.extract()
        for k in order:
            tr.append(by_key[k])


# ── Add / edit pages ────────────────────────────────────────────────────────

def live_fields(testing):
    """data-name → live texts (label, description, placeholders, option texts) from cms-testing."""
    out = {}
    for f in sorted(glob.glob(os.path.join(testing, '*-new.html'))):
        s = soup(f)
        for fd in s.select('.acf-field[data-name]'):
            name = fd['data-name']
            if name in out:
                continue
            lab = fd.select_one('.acf-label label')
            desc = fd.select_one('.acf-label .description')
            out[name] = {
                'label': lab.get_text(' ', strip=True).replace(' *', '') if lab else '',
                'desc': desc.get_text() if desc else None,
                'placeholders': [i['placeholder'] for i in fd.select('.acf-input [placeholder]')],
                'options': {o.get('value', ''): o.get_text() for o in fd.select('option')},
            }
    return out


def own_fields(group):
    """Top-level fields of an ACF group (not the sub fields of repeaters)."""
    inside = group.select_one('.inside.acf-fields') or group.select_one('.acf-fields')
    return [f for f in inside.find_all('div', recursive=False) if 'acf-field' in classes(f)], inside


def translate_field(fd, live):
    lv = live.get(fd.get('data-name'))
    if not lv:
        return
    lab = fd.select_one('.acf-label label')
    if lab and LATIN.search(lab.get_text()) and lv['label'] and not LATIN.search(lv['label'].replace('Property ID', '')):
        req = lab.select_one('.acf-required')
        lab.clear()
        lab.append(lv['label'] + (' ' if req else ''))
        if req:
            lab.append(req)
    desc = fd.select_one('.acf-label .description')
    if desc and LATIN.search(desc.get_text().replace('ISBN', '').replace('RankMath', '').replace('Knowledge Graph', '')) and lv['desc']:
        desc.string = lv['desc']
    phs = fd.select('.acf-input [placeholder]')
    for i, el in enumerate(phs):
        if LATIN.search(el['placeholder']) and i < len(lv['placeholders']):
            el['placeholder'] = lv['placeholders'][i]
    for o in fd.select('option'):
        v = o.get('value', '')
        t = o.get_text()
        if LATIN.search(re.sub(r'[A-Z_]{3,}(-CODE)?|ISBN', '', t)):
            if v in lv['options']:
                o.string = lv['options'][v]
            elif v == '' and '' in lv['options']:
                o.string = lv['options']['']
    # the select2 box shows the selected option's text
    sel = fd.select_one('select')
    shown = fd.select_one('.select2-selection__rendered')
    if sel and shown:
        opt = sel.find('option', selected=True) or sel.find('option')
        if opt:
            shown['title'] = opt.get_text()
            inner = shown.select_one('.acf-selection') or shown
            inner.string = opt.get_text()


def accordion(prefix):
    name = prefix + 'additional_fields'
    key = 'field_' + name
    html = (
        f'<div class="acf-field acf-field-accordion acf-field-{name.replace("_", "-")}" data-name="{name}" '
        f'data-type="accordion" data-key="{key}">\n<div class="acf-label">\n'
        f'<label for="acf-{key}">حقول إضافية</label></div>\n<div class="acf-input">\n'
        '\t\t<div class="acf-fields" data-open="0" data-multi_expand="1" data-endpoint="0"></div>\n\t\t\t</div>\n</div>'
    )
    return BeautifulSoup(html, 'html.parser').div


def arrange_group(group, ptype, live):
    """Order a content type's own ACF group, add «حقول إضافية», apply the field rules."""
    fields, inside = own_fields(group)
    if not fields:
        return
    names = [f.get('data-name', '') for f in fields]
    # the group's prefix, e.g. «lesson_fields_» (interpret-series uses «interpretation_series_fields_»)
    prefix = os.path.commonprefix(names)
    if not prefix.endswith('_fields_'):
        prefix = prefix[:prefix.rfind('_fields_') + 8] if '_fields_' in prefix else ''
    if not prefix:
        return

    for f in fields:
        translate_field(f, live)
    kept = []
    for f in fields:
        if f['data-name'][len(prefix):] in DROP:
            f.extract()
        else:
            kept.append(f)

    def suffix(f):
        return f['data-name'][len(prefix):]

    def order_key(i_f):
        i, f = i_f
        sx = suffix(f)
        req = 'is-required' in classes(f)
        return (0 if req else 1, ORDER.index(sx) if sx in ORDER else len(ORDER), i)
    ordered = [f for _, f in sorted(enumerate(kept), key=order_key)]
    outside = [f for f in ordered if 'is-required' in classes(f) or suffix(f) in OUTSIDE]
    rest = [f for f in ordered if f not in outside]

    for f in kept:
        f.extract()
    # whatever is left in the container (whitespace) stays before the fields
    # all optional: the fields show directly, no «حقول إضافية»
    if not outside:
        outside, rest = rest, []
    seq = outside + ([accordion(prefix)] if rest else []) + rest
    for f in seq:
        inside.append(f)
        inside.append(NavigableString('\n'))

    for f in kept:
        sx = suffix(f)
        if sx == 'youtube_id':
            lab = f.select_one('.acf-label label')
            if lab:
                lab.string = 'رابط يوتيوب'
            inp = f.select_one('.acf-input input[type=text]')
            if inp:
                inp['placeholder'] = YOUTUBE_PLACEHOLDER
        elif sx == 'video_url':
            desc = f.select_one('.acf-label .description')
            if desc:
                desc.string = VIDEO_URL_DESC
        elif sx == 'transcript':
            ta = f.select_one('textarea')
            if ta:
                ta['rows'] = '3'


def form_rules(page, ptype, live, drop_boxes=()):
    # boxes removed on the article pages, and the type's own
    for box_id in ('fiqhi-topicdiv', 'acf-group_editor_fields') + tuple(drop_boxes):
        box = page.find(id=box_id)
        if box:
            box.decompose()
        lab = page.find('label', attrs={'for': box_id + '-hide'})
        if lab:
            lab.decompose()

    # «+ أضف» in the side boxes
    for a in page.select('.taxonomy-add-new'):
        a.string = '\n\t\t\t\t\t+ أضف\t\t\t\t'
    for b in page.select('input.category-add-submit'):
        b['value'] = 'أضف'

    # excerpt box open, «اعرف المزيد» opens the Arabic excerpt guide
    ex = page.find(id='postexcerpt')
    if ex:
        remove_class(ex, 'closed')
        for a in ex.select('a[data-orig-href*="excerpt"]'):
            remove_class(a, 'proto-dead')
            a['href'] = EXCERPT_DOC
            a['target'] = '_blank'

    # ACF boxes: the content type's own group arranged; a box is open when it
    # has a required field, closed otherwise (improvements.html, «صندوق الحقول»)
    for box in page.select('.postbox.acf-postbox'):
        if box.get('id') not in ('acf-group_views_fields', 'acf-group_series_shared_fields'):
            arrange_group(box, ptype, live)
        if box.select_one('.acf-field.is-required'):
            remove_class(box, 'closed')
        else:
            add_class(box, 'closed')

    # ACF editors: «Visual» tab in Arabic, like the main editor's «مرئي»
    for b in page.select('button.switch-tmce'):
        if b.get_text(strip=True) == 'Visual':
            b.string = 'مرئي'

    seo = page.find(id='rank_math_metabox')
    if seo and seo.h2:
        seo.h2.string = SEO_TITLE


def field_split(page):
    """Labels of the fields before and after «حقول إضافية» in the content type's own group."""
    outside, inside, seen = [], [], False
    for box in page.select('.postbox.acf-postbox'):
        if box.get('id') in ('acf-group_views_fields', 'acf-group_series_shared_fields'):
            continue
        for f in own_fields(box)[0]:
            if f.get('data-type') == 'accordion':
                seen = True
                continue
            lab = f.select_one('.acf-label label')
            text = lab.get_text(' ', strip=True).replace(' *', '') if lab else f.get('data-name')
            (inside if seen else outside).append(text)
    return outside, inside


# Content types whose Add page was compared with the live CMS copy (cms-testing)
LIVE_COPY = {'article': 'article-new', 'book': 'book-new', 'fatwa': 'fatwa-new', 'lesson': 'lesson-new',
             'podcast': 'podcast-new', 'scientific-series': 'scientific-series-new',
             'static-page': 'static-page-new', 'benefit': 'quote-new'}

# Names as the sidebar shows them (proto.js), where the page heading differs
INDEX_NAMES = {'interpret-series': 'الدورات', 'interpret-lesson': 'دروس الدورات',
               'audio-book-series': 'الكتب الصوتية', 'audio-book-lesson': 'دروس الكتب الصوتية',
               'book-browser-series': 'كتب المتصفح', 'book-browser-lesson': 'دروس المتصفح'}

INDEX_HEAD = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>أنواع المحتوى</title>
<style>
@font-face{font-family:"IBM Plex Sans Arabic";src:url(fonts/IBMPlexSansArabic-Regular.ttf) format("truetype");font-weight:400;font-display:swap}
@font-face{font-family:"IBM Plex Sans Arabic";src:url(fonts/IBMPlexSansArabic-SemiBold.ttf) format("truetype");font-weight:600;font-display:swap}
:root{--bg:#f1f5f9;--card:#fff;--ink:#1d2330;--muted:#5b6577;--line:#e3e6ec;--brand:#1a2744;--gold:#c49a2a;--chip:#eef1f6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#14171c;--card:#1c2027;--ink:#e6e9ef;--muted:#9aa3b2;--line:#2d333d;--brand:#9fb3d9;--gold:#d9b45a;--chip:#262c36}}
:root[data-theme="dark"]{--bg:#14171c;--card:#1c2027;--ink:#e6e9ef;--muted:#9aa3b2;--line:#2d333d;--brand:#9fb3d9;--gold:#d9b45a;--chip:#262c36}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "IBM Plex Sans Arabic",-apple-system,"Segoe UI",Tahoma,sans-serif}
main{max-width:1200px;margin:auto;padding:24px 16px 64px}
h1{font-size:26px;margin:12px 0 4px}
p{color:var(--muted);margin:0 0 12px}
a{color:var(--brand)}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%}
th,td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
thead th{font-weight:600;white-space:nowrap}
tbody tr:last-child>*{border-bottom:0}
tbody th{font-weight:600;white-space:nowrap}
tbody th code{display:block;font:12px monospace;color:var(--muted);direction:ltr;text-align:right}
td.links{white-space:nowrap}
td.links a+a{margin-inline-start:10px}
.f{font-size:13px;color:var(--muted)}
.f b{color:var(--ink);font-weight:600}
.live{font-size:12px;border-radius:999px;padding:0 8px;white-space:nowrap;background:var(--chip);color:var(--muted)}
.live.yes{color:var(--brand);font-weight:600}
</style>
</head>
<body>
<main>
<a href="index.html">→ العودة إلى النموذج</a>
<h1>أنواع المحتوى</h1>
<p>صفحة القائمة وصفحتا الإضافة والتحرير لكل نوع محتوى. بنية HTML من CMS-improvements، والتنسيق والقواعد نفسها المطبّقة على المقالات (انظر <a href="improvements.html">قائمة التحسينات</a>)، والأعمدة حسب <a href="list-pages-columns.html">أعمدة القوائم</a>.</p>
<div class="wrap"><table>
<thead><tr><th scope="col">نوع المحتوى</th><th scope="col">الصفحات</th><th scope="col">الحقول</th><th scope="col">مقارنة باللوحة الحالية</th></tr></thead>
<tbody>
'''


def write_index(rows):
    import html as h
    art = soup(os.path.join(FINAL, 'post-new__post_type-article.html'))
    outside, inside = field_split(art)
    rows = [{'type': 'article', 'name': 'المقالات', 'list': 'edit__post_type-article.html',
             'add': 'post-new__post_type-article.html', 'edit': 'post__action-edit__lang-ar__post-272.html',
             'outside': outside, 'inside': inside, 'rows': 8}] + rows
    for r in rows:
        r['name'] = INDEX_NAMES.get(r['type'], r['name'])
    # alphabetical, «ال» counted (as in the sidebar)
    coll = sorted(rows, key=lambda r: r['name'])
    out = [INDEX_HEAD]
    for r in coll:
        links = ['<a href="%s">القائمة</a>' % r['list']]
        if r.get('add'):
            links.append('<a href="%s">إضافة</a>' % r['add'])
        if r.get('edit'):
            links.append('<a href="%s">تحرير</a>' % r['edit'])
        fields = '<span class="f"><b>%s</b>%s</span>' % (
                h.escape('، '.join(r['outside']) or '—'),
                (' · حقول إضافية: ' + h.escape('، '.join(r['inside']))) if r['inside'] else '')
        note = '' if r['rows'] else ' <span class="live">القائمة فارغة في المصدر</span>'
        live = '<span class="live yes">نعم</span>' if r['type'] in LIVE_COPY else '<span class="live">لا، من CMS-improvements فقط</span>'
        out.append('<tr><th scope="row">%s<code>%s</code></th><td class="links">%s%s</td><td>%s</td><td>%s</td></tr>\n' % (
            h.escape(r['name']), r['type'], ''.join(links), note, fields, live))
    out.append('</tbody>\n</table></div>\n</main>\n<script src="proto-bar.js"></script>\n</body>\n</html>\n')
    with open(os.path.join(FINAL, 'content-types.html'), 'w', encoding='utf-8') as f:
        f.write(''.join(out))


# ── Links ───────────────────────────────────────────────────────────────────

A_TAG = re.compile(r'<a\b[^>]*>')


def fix_links(path, existing):
    """Live links to pages that exist, proto-dead links to pages that don't (regex, so
    hand-edited pages keep their formatting)."""
    with open(path, encoding='utf-8') as f:
        src = f.read()

    def local(href):
        return href and not re.match(r'^(#|[a-z]+:|//|docs/)', href) and href.split('#')[0].split('?')[0].endswith('.html')

    def fix(m):
        tag = m.group(0)
        href = re.search(r'\shref="([^"]*)"', tag)
        orig = re.search(r'\sdata-orig-href="([^"]*)"', tag)
        dead = re.search(r'\sclass="[^"]*\bproto-dead\b', tag)
        if dead and orig and local(orig.group(1)) and orig.group(1) in existing:
            tag = tag.replace(orig.group(0), '')
            tag = re.sub(r'\shref="#"', ' href="%s"' % orig.group(1), tag)
            tag = re.sub(r'(\sclass="[^"]*?)\s*\bproto-dead\b', r'\1', tag)
            tag = tag.replace(' class=""', '')
            return tag
        if not dead and href and local(href.group(1)) and href.group(1).split('#')[0] not in existing:
            target = href.group(1)
            tag = tag.replace(href.group(0), ' href="#" data-orig-href="%s"' % target)
            if re.search(r'\sclass="', tag):
                tag = re.sub(r'\sclass="([^"]*)"', lambda c: ' class="%s proto-dead"' % c.group(1).strip(), tag, count=1)
            else:
                tag = tag.replace('<a ', '<a class="proto-dead" ', 1)
            return tag
        return tag

    out = A_TAG.sub(fix, src)
    if out != src:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(out)
        return True
    return False


# ── Main ────────────────────────────────────────────────────────────────────

def picks():
    s = open(os.path.join(FINAL, 'list-pages-columns.html'), encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'<tr data-q="[^"]*"><th scope="row"><span class="nm">[^<]*</span><code>([^<]*)</code></th>(.*?)</tr>', s):
        out[m.group(1)] = re.findall(r'class="c on" title="([^"]*)"', m.group(2))
    return out


def edit_pages(improvements):
    out = {}
    for f in glob.glob(os.path.join(improvements, 'post__action-edit__*.html')):
        m = re.search(r'\bpost-type-([a-z-]+)', open(f, encoding='utf-8').read())
        if m:
            out[m.group(1)] = os.path.basename(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--improvements', default=os.path.join(os.path.dirname(FINAL), 'CMS-improvements'))
    ap.add_argument('--testing', default=os.path.join(os.path.dirname(FINAL), 'cms-testing'))
    args = ap.parse_args()

    # the sidebar and the «جديد» menu on every page use the new names too
    for p in sorted(glob.glob(os.path.join(FINAL, '*.html'))):
        with open(p, encoding='utf-8') as f:
            src = f.read()
        out = src
        for a, b in RENAMES:
            out = re.sub(a, b, out)
        if out != src:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)

    template = sidebar_template()
    live = live_fields(args.testing)
    columns = picks()
    edits = edit_pages(args.improvements)
    built = []
    index = []

    sources = []  # (type, list page, add page, edit page, text replacements, extra boxes to drop, page names)
    for list_src in sorted(glob.glob(os.path.join(args.improvements, 'edit__post_type-*.html'))):
        ptype = re.search(r'edit__post_type-(.+)\.html$', list_src).group(1)
        if ptype in SKIP:
            continue
        subs = RENAMES + RENAME_PAGES.get(ptype, [])
        add = os.path.join(args.improvements, 'post-new__post_type-%s.html' % ptype)
        edit = edits.get(ptype) and os.path.join(args.improvements, edits[ptype])
        sources.append((ptype, list_src, add, edit, subs, DROP_BOXES.get(ptype, []), {}))
    for ptype, (src, (old_id, new_id), subs, boxes) in DERIVED.items():
        subs = RENAMES + subs + [(r'(?<!\d)%s(?!\d)' % old_id, new_id)]
        edit = edits.get(src) and os.path.join(args.improvements, edits[src])
        names = {'edit': edit and os.path.basename(edit).replace(old_id, new_id)}
        sources.append((ptype, os.path.join(args.improvements, 'edit__post_type-%s.html' % src),
                        os.path.join(args.improvements, 'post-new__post_type-%s.html' % src), edit, subs, boxes, names))

    for ptype, list_src, add_src, edit_src, subs, boxes, names in sorted(sources):
        # list page
        page = soup(list_src, subs)
        put_sidebar(page, template, ptype, 0)
        if ptype in columns:
            apply_columns(page, columns[ptype])
        name = 'edit__post_type-%s.html' % ptype
        write(os.path.join(FINAL, name), page)
        built.append(name)
        row = {'type': ptype, 'name': page.select_one('.wp-heading-inline').get_text(strip=True),
               'list': name, 'rows': len(page.select('#the-list > tr:not(.no-items)'))}
        # add page, edit page
        for src, name, sub in ((add_src, 'post-new__post_type-%s.html' % ptype, 1),
                               (edit_src, names.get('edit') or (edit_src and os.path.basename(edit_src)), 0)):
            if not src or not os.path.exists(src):
                continue
            page = soup(src, subs)
            put_sidebar(page, template, ptype, sub)
            form_rules(page, ptype, live, boxes)
            write(os.path.join(FINAL, name), page)
            built.append(name)
            row['add' if sub else 'edit'] = name
            if sub:
                row['outside'], row['inside'] = field_split(page)
        index.append(row)
    write_index(index)
    built.append('content-types.html')

    existing = {os.path.basename(p) for p in glob.glob(os.path.join(FINAL, '*.html'))}
    changed = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(FINAL, '*.html'))) if fix_links(p, existing)]
    print('built %d pages; links fixed in %d pages' % (len(built), len(changed)))
    json.dump(built, open(os.path.join(HERE, 'content-pages.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.exit(main())
