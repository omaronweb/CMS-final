#!/usr/bin/env python3
"""The prototype's six members, consistent on every page (Omar, 2026-10-26).

- Content the generic «admin» account wrote is shared out among the members
  who write (editors more than managers): the list rows' «بواسطة …» and hidden
  author, the edit page's «آخر تحرير بواسطة …», its revisions and author picker.
  So no account outside the six, and no one-word «مدير» role, is left.
- أعضاء: «الكل (6)» without the administrator filter, no repeated header row or
  role controls at the bottom, every member's name and «تحرير» open his edit page.
- user-edit__user_id-N.html: each member's edit page, built from profile.html
  (the logged-in member's own page), with his name, email, photo and role.

Run it after the build scripts. Running it twice changes nothing.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)

MANAGER, EDITOR, VIEWER = 'zad_common_wp_project_manager', 'zad_common_wp_project_editor', 'zad_common_wp_project_viewer'
# id: (login, first, last, role); 8 is the logged-in account (profile.html)
MEMBERS = {
    8: ('mohammed.ali', 'محمد', 'علي', MANAGER),
    3: ('ahmed.yousef', 'أحمد', 'يوسف', MANAGER),
    7: ('tariq.benissa', 'طارق', 'بن عيسى', EDITOR),
    5: ('samer.alnajjar', 'سامر', 'النجار', EDITOR),
    4: ('ibrahim.abdullah', 'إبراهيم', 'عبد الله', EDITOR),
    6: ('khaled.mansour', 'خالد', 'منصور', VIEWER),
}
LOGGED_IN = 8
ADMIN = 1
# who takes over admin's posts, in turn (editors more often than managers)
AUTHORS = [5, 7, 4, 8, 5, 7, 3, 4]
SITE = 'https://mushkat-admin-testing.zadapps.info'


def name(uid):
    return '%s %s' % MEMBERS[uid][1:3]


def avatar(uid):
    return 'assets/avatar-%s.jpg' % MEMBERS[uid][0]


def read(p):
    return open(os.path.join(FINAL, p), encoding='utf-8').read()


def write(p, s):
    path = os.path.join(FINAL, p)
    if not os.path.exists(path) or open(path, encoding='utf-8').read() != s:
        open(path, 'w', encoding='utf-8').write(s)


def authors_in_lists():
    """admin's rows get a member, in turn; returns post id → member id."""
    owner = {}
    for p in sorted(glob.glob(os.path.join(FINAL, 'edit__post_type-*.html'))):
        p = os.path.basename(p)
        s = read(p)
        k = 0

        def row(m):
            nonlocal k
            r = m.group(0)
            pid = int(m.group(1))
            if '<div class="post_author">%d</div>' % ADMIN in r:
                uid = AUTHORS[k % len(AUTHORS)]
                k += 1
                r = r.replace('<div class="post_author">%d</div>' % ADMIN, '<div class="post_author">%d</div>' % uid)
                r = r.replace('بواسطة <strong>admin</strong>', 'بواسطة <strong>%s</strong>' % name(uid))
            am = re.search(r'<div class="post_author">(\d+)</div>', r)
            if am:
                owner[pid] = int(am.group(1))
            return r
        s = re.sub(r'<tr[^>]*id="post-(\d+)".*?</tr>', row, s, flags=re.S)
        write(p, s)
    return owner


def author_options(s, selected):
    """Author pickers list the members only; «selected» picks one (or keeps the page's choice)."""
    def fix(m):
        sel = m.group(0)
        sel = re.sub(r'\n?<option (?:selected="" )?value="%d">admin \(admin\)</option>' % ADMIN, '', sel)
        for uid, m in MEMBERS.items():  # viewers can't author: not in the picker
            if m[3] == VIEWER:
                sel = re.sub(r'\n?<option (?:selected="" )?value="%d">[^<]*</option>' % uid, '', sel)
        if selected and 'selected=""' not in sel.replace('value="-1"', ''):
            sel = sel.replace('<option value="%d">' % selected, '<option selected="" value="%d">' % selected, 1)
        return sel
    return re.sub(r'<select[^>]*name=["\']post_author(?:_override)?["\'][^>]*>.*?</select>', fix, s, flags=re.S)


def edit_pages(owner):
    for p in glob.glob(os.path.join(FINAL, 'post__action-edit*.html')) + glob.glob(os.path.join(FINAL, 'post-new__*.html')):
        p = os.path.basename(p)
        s = read(p)
        m = re.search(r'post-(\d+)\.html$', p)
        uid = owner.get(int(m.group(1))) if m else None
        had_admin = re.search(r'<option selected="" value="%d">admin \(admin\)' % ADMIN, s)
        uid = uid or (AUTHORS[0] if had_admin else None)
        s = author_options(s, uid if had_admin else None)
        if uid:
            s = s.replace('آخر تحرير بواسطة admin ', 'آخر تحرير بواسطة %s ' % name(uid))
            # revisions by admin: the member's name and photo
            s = re.sub(r'src="[^"]*" srcset="[^"]*8dfc0a32e93bca406911c8f655133030[^"]*" width="24"/> admin،',
                       'src="%s" srcset="%s 2x" width="24"/> %s،' % (avatar(uid), avatar(uid), name(uid)), s)
        write(p, s)
    for p in glob.glob(os.path.join(FINAL, 'edit__post_type-*.html')):
        p = os.path.basename(p)
        write(p, author_options(read(p), None))


def settings_page():
    """الإعدادات العامة (captured on another site): its author picker lists the members and
    its revisions are the logged-in manager's."""
    p = 'post__action-edit__post-702.html'
    s = read(p)
    opts = ''.join("\t<option value='%d'%s>%s (%s)</option>\n" % (uid, " selected='selected'" if uid == LOGGED_IN else '', name(uid), m[0])
                   for uid, m in sorted(MEMBERS.items(), key=lambda kv: kv[1][0]) if m[3] != VIEWER)
    s = re.sub(r"(<select name='post_author_override'[^>]*>\n).*?(</select>)", lambda m: m.group(1) + opts + m.group(2), s, count=1, flags=re.S)
    s = re.sub(r"src='[^']*8dfc0a32e93bca406911c8f655133030[^']*' srcset='[^']*' (class='avatar avatar-24 photo'[^>]*/>) admin،",
               lambda m: "src='%s' srcset='%s 2x' %s %s،" % (avatar(LOGGED_IN), avatar(LOGGED_IN), m.group(1), name(LOGGED_IN)), s)
    write(p, s)


def row_actions(uid):
    login = MEMBERS[uid][0]
    edit = 'profile.html' if uid == LOGGED_IN else 'user-edit__user_id-%d.html' % uid
    parts = ['<span class="edit"><a href="%s">تحرير</a> | </span>' % edit]
    if uid != LOGGED_IN:
        parts.append('<span class="delete"><a class="submitdelete proto-dead" data-orig-href="%s/wp/wp-admin/users.php'
                     '?action=delete&amp;user=%d" href="#">حذف</a> | </span>' % (SITE, uid))
    parts.append('<span class="view"><a aria-label="مشاهدة المقالات بواسطة %s" class="proto-dead" data-orig-href="%s/ar/author/%s/"'
                 ' href="#">عرض</a>%s</span>' % (name(uid), SITE, login, '' if uid == LOGGED_IN else ' | '))
    if uid != LOGGED_IN:
        parts.append('<span class="resetpassword"><a class="resetpassword proto-dead" data-orig-href="%s/wp/wp-admin/users.php'
                     '?action=resetpassword&amp;users=%d" href="#">إرسال إعادة تعيين كلمة المرور</a></span>' % (SITE, uid))
    return edit, '<div class="row-actions">%s</div>' % ''.join(parts)


def users_page():
    s = read('users.html')
    # the six members only: no administrator filter, «الكل» counts the rows
    s = re.sub(r'\s*<li class="administrator">.*?</li>', '', s, flags=re.S)
    s = re.sub(r'(<li class="all">.*?<span class="count">\()\d+(\)</span>)', lambda m: m.group(1) + str(len(MEMBERS)) + m.group(2), s,
               count=1, flags=re.S)
    # no repeated column header under the list
    s = re.sub(r'\s*<tfoot>.*?</tfoot>', '', s, count=1, flags=re.S)
    # «إضافة دور…» / «إزالة دور…» only above the list, not again below it
    s = re.sub(r'\n?<div class="alignleft actions">\n(?:(?!</div>).)*?members-add-role-bottom.*?</div>', '', s, count=1, flags=re.S)

    def row(m):
        r = m.group(0)
        uid = int(m.group(1))
        edit, actions = row_actions(uid)
        login = MEMBERS[uid][0]
        r = re.sub(r'<strong>(?:<a[^>]*>)?%s(?:</a>)?</strong>' % re.escape(login), '<strong><a href="%s">%s</a></strong>' % (edit, login), r)
        r = re.sub(r'<div class="row-actions">.*?</div>', actions, r, count=1, flags=re.S)
        return r
    s = re.sub(r'<tr data-id="(\d+)" id="user-\d+">.*?</tr>', row, s, flags=re.S)
    write('users.html', s)


def user_edit_pages():
    """user-edit__user_id-N.html for every member but the logged-in one, from profile.html."""
    base = read('profile.html')
    me = MEMBERS[LOGGED_IN]
    for uid, (login, first, last, role) in MEMBERS.items():
        if uid == LOGGED_IN:
            continue
        s = base
        s = s.replace('<title>حسابك ›', '<title>تحرير العضو ›')
        s = re.sub(r'(<h1 class="wp-heading-inline">\s*)حسابك', r'\1تحرير العضو', s, count=1)
        s = s.replace(' profile-php ', ' user-edit-php ')
        # the menu: «كافة الأعضاء» is the current item, not «حسابك»
        s = s.replace('<li class="current"><a aria-current="page" class="current" href="profile.html">حسابك',
                      '<li><a href="profile.html">حسابك')
        s = s.replace('<li class="wp-first-item"><a class="wp-first-item" href="users.html">كافة الأعضاء',
                      '<li class="wp-first-item current"><a aria-current="page" class="wp-first-item current" href="users.html">كافة الأعضاء')
        # the member's own details, in the profile form only (the admin bar stays the logged-in member)
        a = s.index('id="your-profile"')
        b = s.index('</form>', a)
        f = s[a:b]
        f = f.replace('wp-admin/profile.php', 'wp-admin/user-edit.php?user_id=%d' % uid)
        f = f.replace('value="%s"' % me[0], 'value="%s"' % login)
        f = f.replace('id="first_name" name="first_name" type="text" value="%s"' % me[1], 'id="first_name" name="first_name" type="text" value="%s"' % first)
        f = f.replace('id="last_name" name="last_name" type="text" value="%s"' % me[2], 'id="last_name" name="last_name" type="text" value="%s"' % last)
        f = f.replace('%s@zadgroup.net' % me[0], '%s@zadgroup.net' % login)
        f = f.replace(avatar(LOGGED_IN), avatar(uid))
        f = re.sub(r'(<select id="display_name" name="display_name">).*?(</select>)',
                   lambda m: m.group(1) + '\n<option>%s</option>\n<option>%s</option>\n<option selected="">%s %s</option>\n' % (login, first, first, last) + m.group(2),
                   f, count=1, flags=re.S)
        f = f.replace('<input checked="" name="members_user_roles[]"', '<input name="members_user_roles[]"')
        f = f.replace('<input name="members_user_roles[]" type="checkbox" value="%s"/>' % role,
                      '<input checked="" name="members_user_roles[]" type="checkbox" value="%s"/>' % role)
        s = s[:a] + f + s[b:]
        write('user-edit__user_id-%d.html' % uid, s)


def main():
    owner = authors_in_lists()
    edit_pages(owner)
    settings_page()
    users_page()
    user_edit_pages()


if __name__ == '__main__':
    main()
