#!/usr/bin/env python3
"""Apply the fields sheet («cms pages and fields», Omar, 2026-10-12) to the add and
edit pages of every content type, and the deleted fields to the list pages.

Run after build_content_pages.py (it rebuilds the pages without these rules).
Works on the HTML text, so the rest of each page stays byte for byte; running it
twice changes nothing.

In the content type's fields box («حقول …»):
  top   required and high-priority fields, shown directly
  alt   alternatives: a note «مطلوب تعبئة أحد هذه الحقول» (labels marked **) or
        «موصى بتعبئة أحد هذه الحقول», then the fields
  rest  low-priority, plain optional and unlisted fields, in the collapsed
        «حقول إضافية»
Deleted fields leave the add/edit pages and the list columns. The المقتطف box
moves after the fields box. Required side boxes (الفهارس، القراء) get a red *.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)

IMAGES_DESC = 'الصورة الأولى هي الصورة البارزة، وتظهر الصور الأخرى بعدها.'
COVER_DESC = 'الصورة الأولى هي صورة الغلاف، وتظهر الصور الأخرى بعدها.'
REQUIRED_NOTE = 'مطلوب تعبئة أحد هذه الحقول'
RECOMMENDED_NOTE = 'موصى بتعبئة أحد هذه الحقول'
LABELS = {'content': 'المحتوى'}  # the WordPress editor, outside the fields box

# Sheet sections; field names are the suffix after «<type>_fields_»
LESSONS = dict(top=['images'], alt=('required', ['content', 'youtube_id', 'audios', 'video_url', 'videos']),
               delete=['release_date'], rest=['transcript', 'clips', 'view_count', 'course'])
SERIES = dict(top=['images', 'status', 'author_name', 'author_about'], required=['images'],
              delete_boxes=['acf-group_series_shared_fields'], required_boxes=['radio-indexdiv'])
SERIES_LESSONS = dict(LESSONS, rest=['pdfs', 'transcript', 'clips', 'view_count', 'course'],
                      delete_boxes=['acf-group_series_shared_fields'], required_boxes=['radio-indexdiv'])
AUDIO_BOOKS = dict(top=['images', 'reciter_info', 'transcript'], required=['images', 'reciter_info'],
                   rest=['content_explanation', 'clips', 'view_count'],
                   delete_boxes=['acf-group_series_shared_fields'],
                   required_boxes=['radio-indexdiv', 'tagsdiv-reciter'])
TYPES = {
    'article': dict(top=['images'],
                    delete=['youtube_id', 'audios', 'videos', 'video_url', 'pdfs', 'release_date',
                            'transcript', 'clips', 'view_count', 'words'],
                    delete_columns=['الملفات الصوتية', 'ملفات PDF', 'ملفات Word']),
    'fatwa': dict(top=['question', 'answer', 'images'],
                  alt=('recommended', ['youtube_id', 'video_url', 'videos']),
                  delete=['release_date'], rest=['audios', 'transcript', 'clips', 'view_count', 'fatwas']),
    'book': dict(top=['cover_images'], alt=('required', ['pdfs', 'buy_url']),
                 top_after=['total_volumes', 'isbn', 'edition_number']),
    'static-page': dict(top=['images'], required=['images'], delete=['release_date']),
    'book-page': dict(),
    'short': dict(),
}
for t in ('lesson', 'speech', 'tilawa', 'podcast', 'lecture', 'supplication', 'benefit'):
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


def mark_label(field, mark):
    """Label marked «*» (required), «**» (required alternative) or nothing."""
    field = re.sub(r' ?<span class="acf-required">\*+</span>', '', field, count=1)
    if mark:
        field = re.sub(r'(<label for="[^"]*">.*?)(</label>)', r'\1 <span class="acf-required">%s</span>\2' % mark,
                       field, count=1, flags=re.S)
    return set_class(field, 'is-required', mark == '*')


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


def note(prefix, kind, labels):
    name = prefix + 'alternatives'
    text = (REQUIRED_NOTE if kind == 'required' else RECOMMENDED_NOTE) + ': ' + '، '.join(labels)
    return (f'<div class="acf-field acf-field-message acf-field-{name.replace("_", "-")} zad-alternatives -{kind}" '
            f'data-key="field_{name}" data-name="{name}" data-type="message">\n'
            f'<div class="acf-input"><p>{text}</p></div></div>\n')


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
    own.pop('alternatives', None)
    for x in cfg.get('delete', []):
        own.pop(x, None)

    required = set(cfg.get('required', []))
    for x in list(own):
        if x not in required and 'acf-required">*<' in own[x]:
            required.add(x)  # required before the sheet (الصور in المقالات، صور الغلاف)
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

    for x in own:
        mark = '*' if x in required else ('**' if kind == 'required' and x in alts else '')
        own[x] = mark_label(own[x], mark)
    if 'images' in own:
        own['images'] = describe(own['images'], IMAGES_DESC)
    if 'cover_images' in own:
        own['cover_images'] = describe(own['cover_images'], COVER_DESC)

    seq = [own[x] for x in top]
    if alts:
        labels = [LABELS.get(x) or label_text(own[x]) for x in alts]
        seq.append(note(prefix, kind, labels))
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
    for box_id in cfg.get('required_boxes', []):
        s = re.sub(r'(id="%s"[^>]*>\s*<div class="postbox-header"><h2 class="hndle[^"]*">)([^<]*?)(</h2>)' % box_id,
                   r'\1\2 <span class="zad-required">*</span>\3', s, count=1)
        s = s.replace('<span class="zad-required">*</span> <span class="zad-required">*</span>',
                      '<span class="zad-required">*</span>')
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


def index_text(sm):
    out = '، '.join(sm['top'])
    if sm['alt']:
        kind, labels = sm['alt']
        out += ('، ' if out else '') + ('مطلوب أحدها' if kind == 'required' else 'موصى بأحدها') + ' (' + '، '.join(labels) + ')'
    if sm['after']:
        out += '، ' + '، '.join(sm['after'])
    out = '<b>%s</b>' % out
    if sm['rest']:
        out += ' · حقول إضافية: ' + '، '.join(sm['rest'])
    return out


def main():
    pages = json.load(open(os.path.join(HERE, 'content-pages.json'), encoding='utf-8'))
    edit_of = {}
    for i, p in enumerate(pages):
        m = re.match(r'post-new__post_type-(.+)\.html$', p)
        if m and i + 1 < len(pages) and pages[i + 1].startswith('post__action-edit'):
            edit_of[m.group(1)] = pages[i + 1]
    edit_of['article'] = 'post__action-edit__lang-ar__post-272.html'
    idx_path = os.path.join(FINAL, 'content-types.html')
    idx = open(idx_path, encoding='utf-8').read()
    for ptype, cfg in sorted(TYPES.items()):
        summary = add_page(os.path.join(FINAL, 'post-new__post_type-%s.html' % ptype), cfg)
        if ptype in edit_of:
            add_page(os.path.join(FINAL, edit_of[ptype]), cfg)
        if cfg.get('delete_columns'):
            list_page(os.path.join(FINAL, 'edit__post_type-%s.html' % ptype), cfg['delete_columns'])
        if summary and cfg:
            idx = re.sub(r'(<code>%s</code></th>.*?<span class="f">).*?(</span></td>)' % re.escape(ptype),
                         lambda m: m.group(1) + index_text(summary) + m.group(2), idx, count=1)
    open(idx_path, 'w', encoding='utf-8').write(idx)


if __name__ == '__main__':
    main()
