# CMS-final

Offline prototype of the CMS admin with the final CSS and usability changes.
Only the unique pages are kept (one list page, one add-post page, …). The HTML
structure is the CMS's own; all design lives in CSS (`custom.css` plus the
plugin CSS in `assets/`) and `proto.js` only re-creates what WordPress/ACF JS
does on the live CMS.

## Pages
| Page | File | HTML from |
| --- | --- | --- |
| Home | `index.html` | CMS-improvements |
| List page (articles) | `edit__post_type-article.html` | CMS-improvements |
| Add post (article) | `post-new__post_type-article.html` | CMS-improvements, article fields in the live order with the "حقول إضافية" accordion (cms-testing) |
| Edit article (top row of the list) | `post__action-edit__lang-ar__post-272.html` | CMS-improvements, same field order and accordion as Add post |
| Categories | `edit-tags__post_type-article__taxonomy-topic.html` | CMS-improvements |
| Groups (المجموعات) | `edit-tags__post_type-article__taxonomy-article-type.html` | CMS-improvements |
| Site homepage (واجهة الموقع) | `homepage.html` | cms-testing (front end; plain المقالات menu item, تجريب removed) |
| Improvements list (قائمة التحسينات) | `improvements.html` | Developer handoff: every change compared with cms-testing, plus the development rules |
| General settings | `post__action-edit__post-702.html` | cms-testing (live), with the CMS-improvements sidebar and admin bar |
| Every other content type (أنواع المحتوى) | `edit__post_type-*.html`, `post-new__post_type-*.html`, `post__action-edit__lang-ar__post-*.html`, index in `content-types.html` | CMS-improvements, built by `_tools/build_content_pages.py` |

Open `index.html` in a browser. Links to pages that are not part of this set show a toast.

## Content type pages
`python3 _tools/build_content_pages.py` (with CMS-improvements and cms-testing checked out next to
CMS-final) rebuilds the list, add and edit pages of every content type except المقالات and
الإعدادات العامة, which are hand-tuned. It takes the sidebar from `edit__post_type-article.html`,
the columns from `list-pages-columns.html` and the article add/edit rules, then makes links
between pages that exist live and the rest `proto-dead`. Re-run it after changing the sidebar
or the column picks.

Types CMS-improvements doesn't have (الكتب الصوتية, `audio-book-series`) are built from a look-alike
type's pages (`DERIVED`), and renamed labels (التفسير → الدورات) are applied on every page (`RENAMES`),
both checked against production add pages on 2026-10-07.

`python3 _tools/build_admin_pages.py` (run after it) builds the users (أعضاء، إضافة عضو، حسابك), media
(المكتبة، إضافة ملف، ترجمة الوسائط) and التصنيفات pages: one list page and one edit page per taxonomy,
plus ترتيب التصنيفات (one page per tab; drag and drop in `proto.js`).

## Where the styles come from
- `custom.css` — CMS-improvements skin (navy + gold), plus what was borrowed from cms-testing:
  sidebar layout, page background, list table colouring, row actions on hover,
  filters/bars above the list table, Additional fields accordion.
- `assets/c0f6f5a9e1-admin.css` and `assets/1c4c38122f-admin.css` — the live zad-common admin CSS
  (copied from cms-testing; includes the General settings and ACF layout improvements).
