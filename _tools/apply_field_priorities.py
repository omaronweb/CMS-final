#!/usr/bin/env python3
"""Apply the fields sheet («cms pages and fields», Omar, 2026-10-12) to the add and
edit pages of every content type, and the deleted fields to the list pages.

Run after build_content_pages.py (it rebuilds the pages without these rules).
Works on the HTML text, so the rest of each page stays byte for byte; running it
twice changes nothing.

In the content type's fields box («حقول …»):
  top   required and high-priority fields, shown directly
  alt   alternatives (one of them to fill): a help icon after the label, orange
        with «يجب تعبئة أحد هذه الحقول: …» when required, green with «يفضل تعبئة
        أحد هذه الحقول: …» when recommended (the label's data-alt-note, shown by
        CSS); the field's own help stays under the label. On publish, proto.js
        shows ACF's error message on them when none is filled (as ACF validation does)
  rest  low-priority, plain optional and unlisted fields, in the collapsed
        «حقول إضافية»
Deleted fields leave the add/edit pages and the list columns. The المقتطف box
moves after the fields box. Required side boxes (القراء) get a red *
(CSS, class zad-required on the box).

Only the CMS's own elements are used: ACF fields, labels, «acf-required» and
the field help (p.description, an ACF field's instructions); classes on them
are ACF «wrapper» classes.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)

IMAGES_DESC = 'الصورة الأولى هي الصورة البارزة، وتظهر الصور الأخرى بعدها.'
VIDEO_URL_DESC = 'رابط مباشر لملف فيديو مرفوع على خادم (وليس رابط يوتيوب)، ينتهي بامتداد الملف، مثل: https://www.example.com/video.mp4'
COVER_DESC = 'الصورة الأولى هي صورة الغلاف، وتظهر الصور الأخرى بعدها.'
ALT_NOTE = {'required': 'يجب تعبئة أحد هذه الحقول', 'recommended': 'يفضل تعبئة أحد هذه الحقول'}
# Field labels renamed on every type (Omar, 2026-10-13)
RENAME = {'video_url': 'رابط فيديو', 'videos': 'مقاطع فيديو', 'audios': 'ملفات صوتية'}
# Labels renamed on every add/edit page, wherever the field or box is (Omar, 2026-10-13)
LABEL_RENAMES = {'الصور': 'صور', 'الصورة': 'صورة', 'الملف الصوتي': 'ملف صوتي', 'مقطع الفيديو': 'مقطع فيديو',
                 'المادة الصوتية': 'مادة صوتية', 'الفتاوى ذات الصلة': 'فتاوى ذات صلة',
                 'النص البديل للصورة': 'نص بديل للصورة', 'معرف يوتيوب': 'رابط يوتيوب'}
BOX_RENAMES = {'خصائص المقالة': 'خصائص المحتوى', 'فهارس الدورات': 'فهارس', 'فهارس الكتب': 'فهارس'}
# List page columns renamed like their fields
COLUMN_RENAMES = {'الملفات الصوتية': 'ملفات صوتية'}
LABELS = {'content': 'المحتوى'}  # the WordPress editor, outside the fields box

# Sheet sections; field names are the suffix after «<type>_fields_»
LESSONS = dict(top=['images'], alt=('required', ['content', 'youtube_id', 'audios', 'video_url', 'videos']),
               delete=['release_date'], rest=['transcript', 'clips', 'view_count', 'course'])
SERIES = dict(top=['images', 'status', 'author_name', 'author_about'], required=['images'],
              delete_boxes=['acf-group_series_shared_fields'], required_boxes=[])
SERIES_LESSONS = dict(LESSONS, rest=['pdfs', 'transcript', 'clips', 'view_count', 'course'],
                      delete_boxes=['acf-group_series_shared_fields'], required_boxes=[])
# اسم القارئ and المادة الصوتية are the «القارئ» and «الملف الصوتي» of each معلومات القارئ row
AUDIO_BOOKS = dict(top=['images', 'reciter_info', 'transcript'], required=['images', 'reciter_info'],
                   rest=['content_explanation', 'clips', 'view_count'],
                   delete_boxes=['acf-group_series_shared_fields'],
                   required_boxes=['tagsdiv-reciter'])
TYPES = {
    'article': dict(top=['images'],
                    delete=['youtube_id', 'audios', 'videos', 'video_url', 'pdfs', 'release_date',
                            'transcript', 'clips', 'view_count', 'words'],
                    delete_columns=['الملفات الصوتية', 'ملفات PDF', 'ملفات Word']),
    'fatwa': dict(top=['question', 'answer', 'images'], required=['question', 'answer'],
                  alt=('recommended', ['youtube_id', 'video_url', 'videos']),
                  delete=['release_date'], rest=['audios', 'transcript', 'clips', 'view_count', 'fatwas']),
    'book': dict(top=['cover_images'], alt=('required', ['pdfs', 'buy_url']),
                 top_after=['total_volumes', 'isbn', 'edition_number']),
    'static-page': dict(top=['images'], required=['images'], delete=['release_date']),
    'book-page': dict(),
}
for t in ('lesson', 'speech', 'tilawa', 'podcast', 'lecture', 'supplication', 'benefit', 'short'):
    TYPES[t] = LESSONS
for t in ('interpret-series', 'radio-program-series', 'tv-program-series', 'book-series',
          'scientific-series', 'audio-book-series', 'book-browser-series'):
    TYPES[t] = SERIES
for t in ('interpret-lesson', 'radio-program-lesson', 'tv-program-lesson', 'book-lesson', 'scientific-lesson'):
    TYPES[t] = SERIES_LESSONS
for t in ('audio-book-lesson', 'book-browser-lesson'):
    TYPES[t] = AUDIO_BOOKS


def span(s, i):
    """End of the element opening at s[i] (balanced <div>s), with its newline."""
    depth = 0
    for t in re.finditer(r'<div\b|</div>', s[i:]):
        depth += 1 if t.group() == '<div' else -1
        if depth == 0:
            e = i + t.end()
            return e + 1 if s[e:e + 1] == '\n' else e
    raise ValueError('unbalanced')


def box_at(s, box_id):
    m = re.search(r'<div class="postbox[^"]*" id="%s"' % re.escape(box_id), s)
    return (m.start(), span(s, m.start())) if m else None


def cut(s, a, b):
    return s[:a] + s[b:], s[a:b]


def set_class(tag, name, on):
    m = re.match(r'(<div class=")([^"]*)(")', tag)
    cls = m.group(2).split()
    if on == (name in cls):
        return tag
    cls = [c for c in cls if c != name]
    if on:
        cls.insert(2 if cls[:1] == ['acf-field'] else len(cls), name)
    return m.group(1) + ' '.join(cls) + m.group(3) + tag[m.end():]


def label_text(field):
    m = re.search(r'<label[^>]*>(.*?)</label>', field, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).replace('*', '').strip() if m else ''


def mark_label(field, required, alt, note=''):
    """Red «*» after the label when required; an alternative's note on the label (its help icon)."""
    field = re.sub(r' ?<span class="acf-required">\*+</span>', '', field, count=1)
    field = re.sub(r'(<label for="[^"]*")(?: data-alt-note="[^"]*")?>', r'\1%s>' % (
        ' data-alt-note="%s"' % note if alt else ''), field, count=1)
    if required:
        field = re.sub(r'(<label for="[^"]*">.*?)(</label>)', r'\1 <span class="acf-required">*</span>\2',
                       field, count=1, flags=re.S)
    field = set_class(field, 'is-required', required)
    for kind in ALT_NOTE:
        field = set_class(field, 'zad-alt-' + kind, alt == kind)
    if 'data-required="' in field.split('>', 1)[0]:
        field = re.sub(r'data-required="\d"', 'data-required="%d"' % required, field, count=1)
    return field


def help_text(field):
    m = re.search(r'</label><p class="description">(.*?)</p>', field, re.S)
    text = m.group(1) if m else ''
    if text.startswith(tuple(ALT_NOTE.values())):
        text = text.split('. ', 1)[1] if '. ' in text else ''  # the note added before
    return text


def describe(field, text):
    """The field's help under its label is «text» (replacing what was there)."""
    field = re.sub(r'(</label>)<p class="description">.*?</p>', r'\1', field, count=1, flags=re.S)
    return field.replace('</label>', '</label><p class="description">%s</p>' % text, 1)


def accordion(prefix):
    name = prefix + 'additional_fields'
    key = 'field_' + name
    return (f'<div class="acf-field acf-field-accordion acf-field-{name.replace("_", "-")}" data-key="{key}" '
            f'data-name="{name}" data-type="accordion">\n<div class="acf-label">\n'
            f'<label for="acf-{key}">حقول إضافية</label></div>\n<div class="acf-input">\n'
            '\t\t<div class="acf-fields" data-endpoint="0" data-multi_expand="1" data-open="0"></div>\n\t\t\t</div>\n</div>\n')


def describe_or_drop(field, text):
    if text:
        return describe(field, text)
    return re.sub(r'(</label>)<p class="description">.*?</p>', r'\1', field, count=1, flags=re.S)


def relabel(s):
    """Field labels and box titles (and their «خيارات الشاشة» toggles) renamed."""
    for old, new in LABEL_RENAMES.items():
        s = re.sub(r'(<label\b[^>]*>)%s(?=\s*(?:<span|</label>))' % re.escape(old), lambda m: m.group(1) + new, s)
    for old, new in BOX_RENAMES.items():
        s = re.sub(r'(<h2 class="hndle[^"]*">)%s(?=</h2>)' % re.escape(old), lambda m: m.group(1) + new, s)
        s = re.sub(r'(-hide"[^>]*>)%s(?=\s*</label>)' % re.escape(old), lambda m: m.group(1) + new, s)
    return s


def relabel_columns(s):
    for old, new in COLUMN_RENAMES.items():
        s = s.replace('data-colname="%s"' % old, 'data-colname="%s"' % new)
        s = s.replace('title="%s"' % old, 'title="%s"' % new)
        s = re.sub(r'>%s(?=</(?:th|a|span|label)>|<span class="sorting-indicators|<div class="acp-co-drag-handle)' % re.escape(old),
                   '>' + new, s)
    return s


def fields_box(s):
    for m in re.finditer(r'<div class="postbox[^"]*" id="acf-group_([a-z_]+_fields)"', s):
        if m.group(1) not in ('views_fields', 'series_shared_fields'):
            return m.group(1) + '_'


def arrange(s, cfg):
    prefix = fields_box(s)
    if not prefix:
        return s, None
    box_id = 'acf-group_' + prefix[:-1]
    a, b = box_at(s, box_id)
    box = s[a:b]
    own = {}
    first = None
    while True:
        m = re.search(r'<div class="acf-field [^"]*"[^>]*? data-name="%s([a-z_]+)"' % prefix, box)
        if not m:
            break
        first = m.start() if first is None else first
        box, f = cut(box, m.start(), span(box, m.start()))
        own[m.group(1)] = f
    if first is None:
        return s, None
    acc = own.pop('additional_fields', None) or accordion(prefix)
    own.pop('alternatives', None)  # the note field of an earlier version
    for x in cfg.get('delete', []):
        own.pop(x, None)

    required = set(cfg.get('required', []))
    kind, alts = cfg.get('alt', (None, []))
    alts = [x for x in alts if x in own or x in LABELS]

    def take(names):
        return [x for x in names if x in own]
    top = take(cfg.get('top', [])) + [x for x in own if x in required and x not in cfg.get('top', [])]
    after = take(cfg.get('top_after', []))
    listed = set(top) | set(after) | set(alts)
    rest = take(cfg.get('rest', [])) + [x for x in own if x not in listed and x not in cfg.get('rest', [])]
    if 'rest' not in cfg and 'top' not in cfg:
        top, rest = list(own), []  # not in the sheet: order unchanged

    for x, label in RENAME.items():
        if x in own:
            own[x] = re.sub(r'(<label for="[^"]*"[^>]*>)[^<]*', lambda m: m.group(1) + label, own[x], count=1)
    labels = [LABELS.get(x) or label_text(own[x]) for x in alts]
    for x in own:
        note = '%s: %s.' % (ALT_NOTE[kind], '، '.join(labels)) if x in alts else ''
        own[x] = mark_label(own[x], x in required, kind if x in alts else None, note)
        own[x] = describe_or_drop(own[x], help_text(own[x]))
    if 'video_url' in own:
        own['video_url'] = describe(own['video_url'], VIDEO_URL_DESC)
    if 'images' in own:
        own['images'] = describe(own['images'], IMAGES_DESC)
    if 'cover_images' in own:
        own['cover_images'] = describe(own['cover_images'], COVER_DESC)

    seq = [own[x] for x in top]
    seq += [own[x] for x in alts if x in own]
    seq += [own[x] for x in after]
    shown = bool(seq)
    if rest and shown:
        seq.append(acc)
    seq += [own[x] for x in rest]
    box = box[:first] + ''.join(seq) + box[first:]
    # open when something shows directly; all low priority: closed, no «حقول إضافية»
    head = re.match(r'<div class="[^"]*"', box).group()
    box = set_class(head + '>', 'closed', not shown)[:-1] + box[len(head):]
    s = s[:a] + box + s[b:]

    summary = dict(top=[label_text(own[x]) for x in top], alt=(kind, labels) if alts else None,
                   after=[label_text(own[x]) for x in after], rest=[label_text(own[x]) for x in rest])
    return s, (box_id, summary)


def add_page(path, cfg):
    s = open(path, encoding='utf-8').read()
    for box_id in cfg.get('delete_boxes', []):
        ab = box_at(s, box_id)
        if ab:
            s, _ = cut(s, *ab)
        s = re.sub(r'<label for="%s-hide">.*?</label>' % box_id, '', s)
    s, res = arrange(s, cfg)
    # المقتطف right after the content type's fields box
    if res and box_at(s, 'postexcerpt'):
        s, ex = cut(s, *box_at(s, 'postexcerpt'))
        _, b = box_at(s, res[0])
        s = s[:b] + ex + s[b:]
    s = s.replace(' <span class="zad-required">*</span>', '')  # earlier version
    for box_id in cfg.get('required_boxes', []):
        ab = box_at(s, box_id)
        if ab:
            tag = s[ab[0]:s.index('>', ab[0]) + 1]
            s = s[:ab[0]] + set_class(tag, 'zad-required', True) + s[ab[0] + len(tag):]
    open(path, 'w', encoding='utf-8').write(s)
    return res and res[1]


def list_page(path, labels):
    s = open(path, encoding='utf-8').read()
    for label in labels:
        m = re.search(r'<input class="hide-column-tog" id="([^"]+)-hide"[^>]*/>%s</label>' % re.escape(label), s)
        if not m:
            continue
        col = m.group(1)
        s = re.sub(r'<label for="%s-hide">.*?</label>' % col, '', s)
        s = re.sub(r'<(t[hd]) class="[^"]*\bcolumn-%s\b[^"]*"[^>]*>.*?</\1>' % col, '', s, flags=re.S)
    open(path, 'w', encoding='utf-8').write(s)


# Taxonomies Omar deleted (2026-10-18): no box on the add/edit pages, no list column.
# فهارس is covered by «الفهارس وقوائم المحتويات».
REMOVED_BOXES = ['tagsdiv-keyword', 'article-typediv', 'course-indexdiv', 'radio-indexdiv']
REMOVED_COLUMNS = ['taxonomy-keyword', 'taxonomy-article-type', 'taxonomy-course-index', 'taxonomy-index']


def cut_div(s, div_id):
    """Remove the <div id="div_id"> element (with its nested divs) from the text."""
    m = re.search(r'<div\b[^>]*\bid="%s"[^>]*>' % re.escape(div_id), s)
    if not m:
        return s
    depth, i = 1, m.end()
    for t in re.finditer(r'<(/?)div\b[^>]*>', s[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return s[:m.start()] + s[i + t.end():].lstrip('\n')
    return s


def drop_removed(s):
    for box in REMOVED_BOXES:
        s = cut_div(s, box)
        s = re.sub(r'<label for="%s-hide">.*?</label>\s*' % box, '', s, flags=re.S)
    for col in REMOVED_COLUMNS:
        s = re.sub(r'<label><input[^>]*id="%s-hide"[^>]*/>[^<]*</label>\s*' % col, '', s)
        s = re.sub(r'<(t[hd]) class="[^"]*\bcolumn-%s\b[^"]*"[^>]*>.*?</\1>' % col, '', s, flags=re.S)
    return s


def main():
    pages = json.load(open(os.path.join(HERE, 'content-pages.json'), encoding='utf-8'))
    edit_of = {}
    for i, p in enumerate(pages):
        m = re.match(r'post-new__post_type-(.+)\.html$', p)
        if m and i + 1 < len(pages) and pages[i + 1].startswith('post__action-edit'):
            edit_of[m.group(1)] = pages[i + 1]
    edit_of['article'] = 'post__action-edit__lang-ar__post-272.html'
    for path in glob.glob(os.path.join(FINAL, 'post-new__*.html')) + glob.glob(os.path.join(FINAL, 'post__action-edit*.html')):
        s = open(path, encoding='utf-8').read()
        open(path, 'w', encoding='utf-8').write(relabel(drop_removed(s)))
    for path in glob.glob(os.path.join(FINAL, 'edit__post_type-*.html')) + [os.path.join(FINAL, 'list-pages-columns.html')]:
        s = open(path, encoding='utf-8').read()
        open(path, 'w', encoding='utf-8').write(relabel_columns(drop_removed(s)))
    for ptype, cfg in sorted(TYPES.items()):
        add_page(os.path.join(FINAL, 'post-new__post_type-%s.html' % ptype), cfg)
        if ptype in edit_of:
            add_page(os.path.join(FINAL, edit_of[ptype]), cfg)
        if cfg.get('delete_columns'):
            list_page(os.path.join(FINAL, 'edit__post_type-%s.html' % ptype), cfg['delete_columns'])


if __name__ == '__main__':
    main()
