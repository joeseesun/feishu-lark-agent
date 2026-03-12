#!/usr/bin/env python3
"""
feishu-lark-agent - Comprehensive Feishu/Lark API CLI
Based on capabilities from larksuite/openclaw-lark official plugin.

Usage: python3 feishu.py <category> <action> [--key value ...]

Categories:
  msg    - Messages (send, history, search, chats, reply)
  user   - Users (get, search)
  doc    - Documents (create, get, list)
  table  - Bitable/multi-dimensional tables (records, add, update, delete, tables)
  cal    - Calendar (list, add, delete)
  task   - Tasks (list, add, done, delete)
"""

import os, sys, json, urllib.request, urllib.error, urllib.parse
import time, tempfile, argparse
from pathlib import Path
from datetime import datetime

APP_ID = os.environ.get('FEISHU_APP_ID')
APP_SECRET = os.environ.get('FEISHU_APP_SECRET')
OWNER_OPEN_ID = os.environ.get('FEISHU_OWNER_OPEN_ID')
BASE = 'https://open.feishu.cn/open-apis'
_cache = Path(tempfile.gettempdir()) / f'.feishu_tok_{(APP_ID or "")[-8:]}.json'


def _http(method, path, data=None, params=None, token=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else b''
    headers = {'Content-Type': 'application/json', 'Content-Length': str(len(body))}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=body or None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read())
            if r.get('code', 0) != 0:
                sys.exit(f"API error {r.get('code')}: {r.get('msg')}")
            return r.get('data', r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:500]}")
    except Exception as e:
        sys.exit(f"Request failed: {e}")


def _token():
    if _cache.exists():
        try:
            c = json.loads(_cache.read_text())
            if c.get('expire', 0) > time.time() + 120:
                return c['token']
        except Exception:
            pass
    if not APP_ID or not APP_SECRET:
        sys.exit('Missing FEISHU_APP_ID or FEISHU_APP_SECRET. Add to ~/.zshrc and reload.')
    r = _http('POST', '/auth/v3/tenant_access_token/internal',
              {'app_id': APP_ID, 'app_secret': APP_SECRET})
    tok = r['tenant_access_token']
    _cache.write_text(json.dumps({'token': tok, 'expire': time.time() + r.get('expire', 7200)}))
    return tok


def api(method, path, data=None, params=None):
    return _http(method, path, data, params, token=_token())


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg):
    print(f'Error: {msg}', file=sys.stderr)
    sys.exit(1)


def parse_dt(s):
    for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M', '%Y/%m/%d']:
        try:
            return int(datetime.strptime(s, fmt).timestamp())
        except ValueError:
            pass
    die(f'Cannot parse datetime: {s}  (expected: YYYY-MM-DD or YYYY-MM-DD HH:MM)')


def resolve_user(email_or_id):
    if not email_or_id:
        return None
    if email_or_id.startswith('ou_'):
        return email_or_id
    r = api('POST', '/contact/v3/users/batch_get_id',
            {'emails': [email_or_id]}, {'user_id_type': 'open_id'})
    users = r.get('user_list', [])
    if not users:
        die(f'User not found: {email_or_id}')
    return users[0].get('user_id') or users[0].get('open_id')


# ==================== MSG ====================

def msg_send(a):
    if a.email:
        target = resolve_user(a.email)
        id_type = 'open_id'
    elif a.to:
        target = a.to
        id_type = 'chat_id' if a.to.startswith('oc_') else 'open_id'
    elif a.chat:
        target = a.chat
        id_type = 'chat_id'
    else:
        die('Specify --to <open_id|chat_id>, --email <email>, or --chat <chat_id>')
    text = a.text or (open(a.file).read() if a.file else None)
    if not text:
        die('Specify --text or --file')
    r = api('POST', '/im/v1/messages',
            {'receive_id': target, 'msg_type': 'text', 'content': json.dumps({'text': text})},
            {'receive_id_type': id_type})
    out({'ok': True, 'message_id': r.get('message_id')})


def msg_history(a):
    if not a.chat:
        die('Specify --chat <chat_id>')
    r = api('GET', '/im/v1/messages', params={
        'container_id_type': 'chat', 'container_id': a.chat,
        'page_size': a.limit or 20})
    msgs = []
    for m in r.get('items', []):
        try:
            body = json.loads(m.get('body', {}).get('content', '{}'))
        except Exception:
            body = m.get('body', {}).get('content', '')
        ts_ms = int(m.get('create_time', 0))
        msgs.append({
            'id': m.get('message_id'),
            'sender': m.get('sender', {}).get('id'),
            'time': datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M') if ts_ms else '',
            'type': m.get('msg_type'),
            'content': body,
        })
    out({'messages': msgs})


def msg_reply(a):
    if not a.to:
        die('Specify --to <message_id>')
    text = a.text or (open(a.file).read() if a.file else None)
    if not text:
        die('Specify --text or --file')
    r = api('POST', f'/im/v1/messages/{a.to}/reply',
            {'msg_type': 'text', 'content': json.dumps({'text': text})})
    out({'ok': True, 'message_id': r.get('message_id')})


def msg_search(a):
    if not a.query:
        die('Specify --query')
    r = api('POST', '/im/v1/messages/search', {'query': a.query},
            {'page_size': a.limit or 20})
    out({'messages': r.get('items', [])})


def msg_chats(a):
    r = api('GET', '/im/v1/chats', params={'page_size': a.limit or 50})
    chats = [{'id': c.get('chat_id'), 'name': c.get('name'),
               'type': c.get('chat_type'), 'members': c.get('member_count')}
              for c in r.get('items', [])]
    out({'chats': chats})


# ==================== USER ====================

def user_get(a):
    if a.email:
        r = api('POST', '/contact/v3/users/batch_get_id',
                {'emails': [a.email]}, {'user_id_type': 'open_id'})
        out({'users': r.get('user_list', [])})
    elif a.id:
        r = api('GET', f'/contact/v3/users/{a.id}',
                params={'user_id_type': 'open_id'})
        out({'user': r.get('user')})
    else:
        die('Specify --email <email> or --id <open_id>')


def user_search(a):
    if not a.name:
        die('Specify --name')
    r = api('GET', '/contact/v3/users/search',
            params={'query': a.name, 'page_size': a.limit or 20})
    out({'users': r.get('results', [])})


# ==================== DOC ====================

def _md_to_blocks(text):
    """Convert simple Markdown text to Feishu docx block list."""
    blocks = []
    for line in text.split('\n'):
        line = line.rstrip()
        if line.startswith('### '):
            blocks.append({'block_type': 5, 'heading3': {'style': {}, 'elements': [{'text_run': {'content': line[4:], 'text_element_style': {}}}]}})
        elif line.startswith('## '):
            blocks.append({'block_type': 4, 'heading2': {'style': {}, 'elements': [{'text_run': {'content': line[3:], 'text_element_style': {}}}]}})
        elif line.startswith('# '):
            blocks.append({'block_type': 3, 'heading1': {'style': {}, 'elements': [{'text_run': {'content': line[2:], 'text_element_style': {}}}]}})
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({'block_type': 12, 'bullet': {'style': {}, 'elements': [{'text_run': {'content': line[2:], 'text_element_style': {}}}]}})
        elif line and line[0].isdigit() and '. ' in line[:4]:
            blocks.append({'block_type': 13, 'ordered': {'style': {}, 'elements': [{'text_run': {'content': line.split('. ', 1)[1], 'text_element_style': {}}}]}})
        elif line:
            blocks.append({'block_type': 2, 'text': {'style': {}, 'elements': [{'text_run': {'content': line, 'text_element_style': {}}}]}})
    return blocks


def _grant_doc_permission(doc_id, open_id, perm='full_access'):
    """Grant a user edit access to a document."""
    try:
        api('POST', f'/drive/v1/permissions/{doc_id}/members',
            {'member_type': 'openid', 'member_id': open_id, 'perm': perm},
            {'type': 'docx', 'need_notification': 'false'})
    except SystemExit:
        pass  # Non-fatal: doc created, permission grant failed


def _write_blocks(doc_id, blocks):
    """Write blocks to a document, chunked to avoid API limits."""
    chunk = 50
    for i in range(0, len(blocks), chunk):
        api('POST', f'/docx/v1/documents/{doc_id}/blocks/{doc_id}/children',
            {'children': blocks[i:i+chunk], 'index': i})


def doc_create(a):
    r = api('POST', '/docx/v1/documents',
            {'title': a.title or '新文档', 'folder_token': a.folder or ''})
    doc = r.get('document', {})
    doc_id = doc.get('document_id')
    url = doc.get('document_uri') or f"https://feishu.cn/docx/{doc_id}"

    # Write content if provided
    content = a.content or (open(a.file).read() if a.file else None)
    if content and doc_id:
        blocks = _md_to_blocks(content)
        if blocks:
            _write_blocks(doc_id, blocks)

    # Auto-grant edit permission to owner
    share_to = getattr(a, 'share_to', None) or OWNER_OPEN_ID
    if share_to and doc_id:
        _grant_doc_permission(doc_id, share_to)

    out({'ok': True, 'document_id': doc_id, 'url': url})


def doc_get(a):
    if not a.id:
        die('Specify --id <document_id>')
    r = api('GET', f'/docx/v1/documents/{a.id}/raw_content', params={'lang': 0})
    out({'content': r.get('content')})


def doc_list(a):
    params = {'page_size': a.limit or 50, 'order_by': 'EditedTime', 'direction': 'DESC'}
    if a.folder:
        params['folder_token'] = a.folder
    r = api('GET', '/drive/v1/files', params=params)
    out({'files': r.get('files', [])})


# ==================== TABLE (BITABLE) ====================

def table_records(a):
    if not a.app or not a.table:
        die('Specify --app <app_token> and --table <table_id>')
    params = {'page_size': a.limit or 100}
    if a.filter:
        params['filter'] = a.filter
    if a.sort:
        params['sort'] = a.sort
    r = api('GET', f'/bitable/v1/apps/{a.app}/tables/{a.table}/records', params=params)
    out({'records': r.get('items', []), 'total': r.get('total')})


def table_add(a):
    if not a.app or not a.table:
        die('Specify --app and --table')
    raw = a.data or (open(a.file).read() if a.file else None)
    if not raw:
        die('Specify --data \'{"field":"value"}\' or --file <json-file>')
    r = api('POST', f'/bitable/v1/apps/{a.app}/tables/{a.table}/records',
            {'fields': json.loads(raw)})
    out({'ok': True, 'record_id': r.get('record', {}).get('record_id')})


def table_update(a):
    if not a.app or not a.table or not a.record:
        die('Specify --app, --table, and --record')
    if not a.data:
        die('Specify --data \'{"field":"value"}\'')
    r = api('PUT', f'/bitable/v1/apps/{a.app}/tables/{a.table}/records/{a.record}',
            {'fields': json.loads(a.data)})
    out({'ok': True, 'record': r.get('record')})


def table_delete(a):
    if not a.app or not a.table or not a.record:
        die('Specify --app, --table, and --record')
    api('DELETE', f'/bitable/v1/apps/{a.app}/tables/{a.table}/records/{a.record}')
    out({'ok': True})


def table_tables(a):
    if not a.app:
        die('Specify --app <app_token>')
    r = api('GET', f'/bitable/v1/apps/{a.app}/tables', params={'page_size': 50})
    out({'tables': r.get('items', [])})


def table_fields(a):
    if not a.app or not a.table:
        die('Specify --app and --table')
    r = api('GET', f'/bitable/v1/apps/{a.app}/tables/{a.table}/fields',
            params={'page_size': 100})
    out({'fields': r.get('items', [])})


# ==================== CALENDAR ====================

def cal_list(a):
    now = int(time.time())
    days = int(a.days or 7)
    cal_id = a.calendar or 'primary'
    r = api('GET', f'/calendar/v4/calendars/{cal_id}/events', params={
        'start_time': str(now), 'end_time': str(now + days * 86400), 'page_size': 50})
    events = []
    for e in r.get('items', []):
        st, et = e.get('start_time', {}), e.get('end_time', {})
        def fmt_time(t):
            if t.get('date'):
                return t['date']
            ts = t.get('timestamp')
            return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M') if ts else ''
        events.append({'id': e.get('event_id'), 'title': e.get('summary'),
                        'start': fmt_time(st), 'end': fmt_time(et),
                        'location': e.get('location', {}).get('name'),
                        'description': e.get('description')})
    out({'events': events})


def cal_add(a):
    if not a.title or not a.start or not a.end:
        die('Specify --title, --start "YYYY-MM-DD HH:MM", --end "YYYY-MM-DD HH:MM"')
    cal_id = a.calendar or 'primary'
    data = {
        'summary': a.title,
        'start_time': {'timestamp': str(parse_dt(a.start)), 'timezone': 'Asia/Shanghai'},
        'end_time': {'timestamp': str(parse_dt(a.end)), 'timezone': 'Asia/Shanghai'},
    }
    if a.desc:
        data['description'] = a.desc
    if a.location:
        data['location'] = {'name': a.location}
    r = api('POST', f'/calendar/v4/calendars/{cal_id}/events', data)
    event_id = r.get('event', {}).get('event_id')
    if event_id:
        attendees = []
        # Auto-add owner as attendee
        if OWNER_OPEN_ID:
            attendees.append({'type': 'user', 'user_id': OWNER_OPEN_ID})
        # Add extra attendees from --attendees flag
        if a.attendees:
            emails = [e.strip() for e in a.attendees.split(',')]
            attendees += [{'type': 'third_party', 'third_party_email': e} for e in emails]
        if attendees:
            try:
                api('POST', f'/calendar/v4/calendars/{cal_id}/events/{event_id}/attendees',
                    {'attendees': attendees}, {'user_id_type': 'open_id'})
            except SystemExit:
                pass  # Non-fatal
    out({'ok': True, 'event_id': event_id})


def cal_delete(a):
    if not a.id:
        die('Specify --id <event_id>')
    api('DELETE', f'/calendar/v4/calendars/{a.calendar or "primary"}/events/{a.id}')
    out({'ok': True})


# ==================== TASK ====================

def task_list(a):
    params = {'page_size': a.limit or 50, 'user_id_type': 'open_id'}
    if a.completed:
        params['completed'] = 'true'
    r = api('GET', '/task/v2/tasks', params=params)
    tasks = []
    for t in r.get('items', []):
        due = t.get('due', {})
        ts = due.get('timestamp')
        tasks.append({
            'id': t.get('guid'),
            'title': t.get('summary'),
            'due': due.get('date') or (datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d') if ts else None),
            'done': bool(t.get('completed_at')),
        })
    out({'tasks': tasks})


def task_add(a):
    if not a.title:
        die('Specify --title')
    data = {'summary': a.title}
    if a.due:
        ts = parse_dt(a.due)
        data['due'] = {'timestamp': str(ts), 'is_all_day': ':' not in a.due}
    if a.note:
        data['description'] = {'text': a.note}
    r = api('POST', '/task/v2/tasks', data, {'user_id_type': 'open_id'})
    out({'ok': True, 'task_id': r.get('task', {}).get('guid')})


def task_done(a):
    if not a.id:
        die('Specify --id <task_guid>')
    api('POST', f'/task/v2/tasks/{a.id}/complete')
    out({'ok': True})


def task_delete(a):
    if not a.id:
        die('Specify --id')
    api('DELETE', f'/task/v2/tasks/{a.id}')
    out({'ok': True})


# ==================== DISPATCH ====================

COMMANDS = {
    'msg send': msg_send,
    'msg history': msg_history,
    'msg reply': msg_reply,
    'msg search': msg_search,
    'msg chats': msg_chats,
    'user get': user_get,
    'user search': user_search,
    'doc create': doc_create,
    'doc get': doc_get,
    'doc list': doc_list,
    'table records': table_records,
    'table add': table_add,
    'table update': table_update,
    'table delete': table_delete,
    'table tables': table_tables,
    'table fields': table_fields,
    'cal list': cal_list,
    'cal add': cal_add,
    'cal delete': cal_delete,
    'task list': task_list,
    'task add': task_add,
    'task done': task_done,
    'task delete': task_delete,
}

ATTRS = ['to', 'email', 'text', 'file', 'chat', 'id', 'query', 'name', 'title',
         'content', 'folder', 'app', 'table', 'record', 'data', 'filter', 'sort', 'revision_id',
         'limit', 'days', 'start', 'end', 'desc', 'location', 'calendar', 'note',
         'due', 'completed', 'tasklist', 'attendees', 'share_to']


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print('Usage: feishu.py <category> <action> [--key value ...]\n')
        print('Commands:')
        for k in COMMANDS:
            print(f'  {k}')
        sys.exit(0)

    key = f'{args[0]} {args[1]}'
    if key not in COMMANDS:
        die(f'Unknown command: {key}\nAvailable: {", ".join(COMMANDS)}')

    ns = argparse.Namespace(**{a: None for a in ATTRS})
    rest = args[2:]
    i = 0
    while i < len(rest):
        if rest[i].startswith('--'):
            k = rest[i][2:].replace('-', '_')
            if i + 1 < len(rest) and not rest[i + 1].startswith('--'):
                setattr(ns, k, rest[i + 1])
                i += 2
            else:
                setattr(ns, k, True)
                i += 1
        else:
            i += 1

    COMMANDS[key](ns)


if __name__ == '__main__':
    main()
