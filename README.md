# feishu-lark-agent

Comprehensive Feishu/Lark workspace agent. Handles messages, docs, bitable (multi-dimensional tables

## 安装

```bash
npx skills add joeseesun/feishu-lark-agent
```

# Feishu Lark Agent

Full-featured Feishu/Lark workspace integration. Powered by `feishu.py` — a zero-dependency Python CLI using Feishu Open API.

## Script Path

```
~/.claude/skills/feishu-lark-agent/feishu.py
```

## Prerequisites

```bash
# Credentials must be set (already in ~/.zshrc)
export FEISHU_APP_ID=your_app_id_here
export FEISHU_APP_SECRET=your_app_secret_here
```

Run as:
```bash
source ~/.zshrc && python3 ~/.claude/skills/feishu-lark-agent/feishu.py <category> <action> [--key value ...]
```

---

## Messages (`msg`)

### Send message
```bash
# Send to user by email
python3 feishu.py msg send --email user@example.com --text "Hello"

# Send to user by open_id
python3 feishu.py msg send --to ou_xxxxxxxx --text "Hello"

# Send to group chat
python3 feishu.py msg send --chat oc_xxxxxxxx --text "Hello group"

# Send from file
python3 feishu.py msg send --email user@example.com --file /tmp/msg.txt
```

### Get chat history
```bash
python3 feishu.py msg history --chat oc_xxxxxxxx --limit 20
```

### Reply to message
```bash
python3 feishu.py msg reply --to <message_id> --text "Reply content"
```

### Search messages
```bash
python3 feishu.py msg search --query "关键词" --limit 20
```

### List chats (groups + DMs)
```bash
python3 feishu.py msg chats --limit 50
```

---

## Users (`user`)

### Look up user by email
```bash
python3 feishu.py user get --email someone@example.com
# Returns: open_id, user_id, name, avatar, etc.
```

### Look up user by open_id
```bash
python3 feishu.py user get --id ou_xxxxxxxx
```

### Search users by name
```bash
python3 feishu.py user search --name "张三"
```

---

## Documents (`doc`)

### Create document
```bash
python3 feishu.py doc create --title "会议记录"
python3 feishu.py doc create --title "报告" --folder <folder_token>
```

### Read document content
```bash
python3 feishu.py doc get --id <document_id>
# document_id is in the URL: feishu.cn/docx/DOC_ID
```

### List documents in folder
```bash
python3 feishu.py doc list
python3 feishu.py doc list --folder <folder_token> --limit 20
```

---

## Bitable / Multi-dimensional Tables (`table`)

App token is in URL: `feishu.cn/base/APP_TOKEN`
Table ID is the table identifier (from the API or UI).

### List records
```bash
python3 feishu.py table records --app bASc1234xxx --table tblXXXX
python3 feishu.py table records --app bASc... --table tbl... --limit 50

# With filter (Feishu filter syntax)
python3 feishu.py table records --app bASc... --table tbl... \
  --filter 'AND(CurrentValue.[状态]="进行中")'
```

### Add record
```bash
python3 feishu.py table add --app bASc... --table tbl... \
  --data '{"名称":"新项目","状态":"待开始","负责人":"张三"}'

# From JSON file
python3 feishu.py table add --app bASc... --table tbl... --file /tmp/record.json
```

### Update record
```bash
python3 feishu.py table update --app bASc... --table tbl... \
  --record recXXXX --data '{"状态":"已完成"}'
```

### Delete record
```bash
python3 feishu.py table delete --app bASc... --table tbl... --record recXXXX
```

### List tables in app
```bash
python3 feishu.py table tables --app bASc...
```

### List fields in table
```bash
python3 feishu.py table fields --app bASc... --table tbl...
```

---

## Calendar (`cal`)

> Note: Calendar operations use tenant access token. If "primary" calendar isn't accessible,
> the app may need calendar permissions or the user's personal calendar_id.

### List upcoming events
```bash
# Default: next 7 days
python3 feishu.py cal list

# Next 30 days
python3 feishu.py cal list --days 30

# Specific calendar
python3 feishu.py cal list --calendar <calendar_id> --days 7
```

### Create event
```bash
python3 feishu.py cal add \
  --title "产品评审会" \
  --start "2026-03-15 14:00" \
  --end "2026-03-15 15:30"

# With location and description
python3 feishu.py cal add \
  --title "团队午饭" \
  --start "2026-03-15 12:00" \
  --end "2026-03-15 13:00" \
  --location "3楼会议室" \
  --desc "季度复盘"

# With attendees (comma-separated emails)
python3 feishu.py cal add \
  --title "对齐会" \
  --start "2026-03-16 10:00" \
  --end "2026-03-16 11:00" \
  --attendees "a@example.com,b@example.com"
```

### Delete event
```bash
python3 feishu.py cal delete --id <event_id>
```

---

## Tasks (`task`)

> Note: Task API (v2) may require the app to have task permissions enabled.

### List tasks
```bash
# Active tasks
python3 feishu.py task list

# Completed tasks
python3 feishu.py task list --completed true --limit 20
```

### Create task
```bash
python3 feishu.py task add --title "完成季度报告"

# With due date
python3 feishu.py task add --title "提交报告" --due "2026-03-20"

# With note
python3 feishu.py task add --title "准备演示" --due "2026-03-18 09:00" \
  --note "需要准备PPT和数据"
```

### Mark task as done
```bash
python3 feishu.py task done --id <task_guid>
```

### Delete task
```bash
python3 feishu.py task delete --id <task_guid>
```

---

## Workflow: Sending to a Person by Name

When user says "发飞书消息给张三" but you only have a name:
1. `user search --name "张三"` to get open_id
2. `msg send --to <open_id> --text "..."` to send

## Workflow: Working with Bitable

When user says "在多维表格里添加一条记录":
1. Ask user for app_token and table_id (or check if they mentioned a URL)
2. `table fields --app ... --table ...` to see available fields
3. `table add --app ... --table ... --data '{...}'` to add record

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `API error 99991671` | App not authorized | Enable permissions in Feishu Open Platform |
| `API error 230006` | No access to calendar | Need calendar.event:write permission |
| `API error 1254043` | Bitable not found | Check app_token in URL |
| `Missing FEISHU_APP_ID` | Env not loaded | `source ~/.zshrc` first |

## App Permissions Required (Feishu Open Platform)

For full functionality, ensure these are enabled:
- `im:message` - Send/read messages
- `im:message:send_as_bot` - Send as bot
- `docs:doc` - Create/read docs
- `bitable:app` - Bitable operations
- `calendar:calendar:write` - Calendar write
- `task:task:write` - Task write
- `contact:user.id:readonly` - User lookup

## License

MIT

## 📱 关注作者

如果这个项目对你有帮助，欢迎关注我获取更多技术分享：

- **X (Twitter)**: [@vista8](https://x.com/vista8)
- **微信公众号「向阳乔木推荐看」**:

<p align="center">
  <img src="https://github.com/joeseesun/terminal-boost/raw/main/assets/wechat-qr.jpg?raw=true" alt="向阳乔木推荐看公众号二维码" width="300">
</p>
