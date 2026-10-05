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
| General settings | `post__action-edit__post-702.html` | cms-testing (live), with the CMS-improvements sidebar and admin bar |

Open `index.html` in a browser. Links to pages that are not part of this set show a toast.

## Where the styles come from
- `custom.css` — CMS-improvements skin (navy + gold), plus what was borrowed from cms-testing:
  sidebar layout, page background, list table colouring, row actions on hover,
  filters/bars above the list table, Additional fields accordion.
- `assets/c0f6f5a9e1-admin.css` and `assets/1c4c38122f-admin.css` — the live zad-common admin CSS
  (copied from cms-testing; includes the General settings and ACF layout improvements).
