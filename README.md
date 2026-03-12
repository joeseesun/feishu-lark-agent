# feishu-lark-agent

[中文](#中文文档) | [English](#english-docs)

---

## 中文文档

让 Claude Code 直接操控飞书——发消息、建文档、管日程、写多维表格，全部用自然语言完成。

> 零依赖 Python 脚本，调用飞书开放 API，配合 Claude Code 使用效果最佳。

### 安装

```bash
npx skills add joeseesun/feishu-lark-agent
```

---

### 自然语言对话示例

安装并配置完成后，直接和 Claude Code 说话就好，不需要记任何命令。

---

**💬 发消息**

> 「发飞书消息给 zhang@company.com，说今天的站会改到11点」

Claude 自动通过邮箱查到 open_id，发送消息，返回确认。

---

> 「给乔木龙虾俱乐部群发一条消息：周五下午茶，大家来玩」

Claude 先列出群聊找到 chat_id，再发送到群组。

---

**📄 文档**

> 「帮我创建一个飞书文档，标题「2026 Q2 OKR」，内容从这个文件读：/tmp/okr.md」

Claude 创建文档，写入内容，自动将你加为编辑者，返回文档链接。

---

> 「读一下这个飞书文档的内容：https://xxx.feishu.cn/docx/DOC_ID」

Claude 提取 URL 中的 document_id，调用接口返回全文。

---

**📅 日历**

> 「明天下午3点到4点，帮我创建一个「产品评审会」日程，地点3楼大会议室」

Claude 解析时间、创建日程，并自动发送日历邀请给你（需配置 `FEISHU_OWNER_OPEN_ID`）。

---

> 「帮我看看本周还有哪些日程」

Claude 查询未来7天的日历事件，整理后展示给你。

---

**📊 多维表格**

> 「在我的读书记录表格里加一条：《穷查理宝典》，查理·芒格，状态在读」
> （表格链接：https://xxx.feishu.cn/base/APP_TOKEN）

Claude 先查表格字段结构，再按字段名写入记录。

---

> 「把多维表格里所有状态为「待审核」的记录都列出来」

Claude 用 Feishu 过滤语法查询并展示结果。

---

**✅ 任务**

> 「帮我创建一个飞书任务：准备季度述职，截止日期3月25日，备注要准备PPT和数据」

Claude 调用 Task API 创建任务并返回任务 ID。

---

**🔍 复合场景**

> 「查一下公司有没有叫王芳的同事，找到了就给她发一条飞书消息，说明天的设计评审希望她参加」

Claude 先用 `user search` 找人，确认后再发消息，两步自动完成。

---

> 「帮我把 /tmp/meeting_notes.md 的内容创建成飞书文档，然后发消息给 product-team@company.com 告诉他们文档链接」

Claude 创建文档拿到 URL，再发消息附上链接，一气呵成。

---

### 第一步：创建飞书自建应用，获取 App ID 和 App Secret

> 这是唯一需要手动操作的步骤，约 5 分钟完成。

**1. 进入飞书开发者后台**

打开 [https://open.feishu.cn/app](https://open.feishu.cn/app)，用飞书账号登录。

**2. 创建自建应用**

点击右上角 **「创建企业自建应用」**，填写应用名称（如「我的 AI 助手」）和描述。

**3. 获取 App ID 和 App Secret**

创建完成后，进入应用 → **「凭证与基础信息」**，复制：

```
App ID:     cli_xxxxxxxxxxxxxxxxx
App Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**4. 开通权限**

进入 **「权限管理」**，搜索并开通以下权限（按需开通）：

| 权限标识 | 用途 |
|---------|------|
| `im:message` | 读取消息 |
| `im:message:send_as_bot` | 发送消息 |
| `docx:document` | 创建/读取文档 |
| `drive:drive` | 文档授权管理 |
| `bitable:app` | 多维表格操作 |
| `calendar:calendar` | 日历读写 |
| `task:task:write` | 任务管理 |
| `contact:user.id:readonly` | 按邮箱查用户 |

**5. 发布应用**

进入 **「版本管理与发布」** → 创建版本 → 申请发布。企业管理员审批后生效（自己是管理员可立即通过）。

---

### 第二步：获取你的 Open ID（可选但推荐）

Open ID 是飞书中每个用户的唯一标识符（`ou_` 开头）。设置后，创建文档/日程时会自动将你加为参与者，无需手动共享。

**方法一：通过接口获取（推荐）**

先完成第三步配置，再运行：

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py user get --email 你的飞书邮箱
# 返回结果中的 user_id 字段即为 Open ID（ou_ 开头）
```

**方法二：通过群聊获取**

如果你是某个群的群主：

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py msg chats
# 找到你创建的群，owner_id 即为你的 Open ID
```

**方法三：通过开发者后台获取**

在飞书应用后台 → **「事件与回调」** 中，向 Bot 发一条消息，查看回调日志里的 `sender.sender_id.open_id`。

---

### 第三步：配置环境变量

将以下内容添加到 `~/.zshrc`（或 `~/.bashrc`）：

```bash
export FEISHU_APP_ID=cli_你的AppID
export FEISHU_APP_SECRET=你的AppSecret

# 可选：设置后，创建文档/日程时自动将你加为参与者
export FEISHU_OWNER_OPEN_ID=ou_你的OpenID
```

执行生效：

```bash
source ~/.zshrc
```

验证配置是否成功：

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py msg chats
# 看到群列表说明配置成功 ✓
```

---

### 与 Claude Code 配合使用

安装并配置完成后，直接用自然语言对 Claude Code 说：

```
发飞书消息给 zhang@company.com，说「今天的会议改到下午3点」
```

```
创建一个飞书文档，标题「Q2 OKR 规划」
```

```
明天上午10点到11点，创建日程「产品评审会」，地点「3楼大会议室」
```

```
在多维表格里查看状态为「进行中」的记录
```

Claude Code 会自动识别并调用对应的飞书操作。

---

### 常用场景演示

#### 场景一：发飞书消息

```bash
# 通过邮箱发消息
python3 feishu.py msg send --email colleague@company.com --text "周报已提交，请查收"

# 发消息到群组（chat_id 通过 msg chats 获取）
python3 feishu.py msg send --chat oc_xxxxxxxx --text "今日站会10分钟后开始"

# 发长文本（从文件读取）
python3 feishu.py msg send --email boss@company.com --file /tmp/report.txt

# 查看群聊列表
python3 feishu.py msg chats
```

#### 场景二：创建飞书文档

```bash
# 创建空文档（若配置了 FEISHU_OWNER_OPEN_ID，自动授权你编辑）
python3 feishu.py doc create --title "2026 Q2 规划"

# 创建文档并写入 Markdown 内容
python3 feishu.py doc create --title "会议记录" --file /tmp/meeting.md

# 查看文档内容（document_id 在 URL 中）
python3 feishu.py doc get --id DOC_ID
```

#### 场景三：管理日历

```bash
# 查看最近7天的日程
python3 feishu.py cal list --calendar YOUR_CALENDAR_ID

# 创建日程（若配置了 FEISHU_OWNER_OPEN_ID，自动发送日历邀请给你）
python3 feishu.py cal add \
  --title "周例会" \
  --start "2026-03-16 10:00" \
  --end "2026-03-16 11:00" \
  --location "3楼会议室" \
  --calendar YOUR_CALENDAR_ID

# 删除日程
python3 feishu.py cal delete --id EVENT_ID --calendar YOUR_CALENDAR_ID
```

> **如何获取 Calendar ID**：Bot 使用租户令牌，运行以下命令获取 Bot 的日历 ID：
> ```bash
> python3 -c "
> import sys, os, json; sys.path.insert(0, os.path.expanduser('~/.claude/skills/feishu-lark-agent'))
> import feishu
> r = feishu.api('GET', '/calendar/v4/calendars', params={'page_size': 50})
> print(json.dumps(r, ensure_ascii=False, indent=2))
> "
> ```

#### 场景四：多维表格（Bitable）

```bash
# App Token 在 URL 中：feishu.cn/base/APP_TOKEN
# 先查看字段结构，再操作
python3 feishu.py table fields --app bASc1234xxx --table tblXXXX

# 查询记录
python3 feishu.py table records --app bASc... --table tbl...

# 按条件过滤（支持飞书筛选语法）
python3 feishu.py table records --app bASc... --table tbl... \
  --filter 'AND(CurrentValue.[状态]="进行中")'

# 新增记录
python3 feishu.py table add --app bASc... --table tbl... \
  --data '{"书名":"深度工作","作者":"Cal Newport","状态":"在读"}'

# 更新记录
python3 feishu.py table update --app bASc... --table tbl... \
  --record recXXXX --data '{"状态":"已读"}'
```

#### 场景五：任务管理

```bash
# 查看当前任务
python3 feishu.py task list

# 创建任务并设置截止日期
python3 feishu.py task add --title "完成Q2复盘报告" --due "2026-03-20"

# 带备注的任务
python3 feishu.py task add \
  --title "准备产品演示" \
  --due "2026-03-18 09:00" \
  --note "需要准备30页PPT和数据看板"

# 完成任务
python3 feishu.py task done --id TASK_GUID
```

---

### 完整命令速查

| 分类 | 命令 | 说明 |
|------|------|------|
| **消息** | `msg send` | 发送消息 |
| | `msg history` | 获取群聊记录 |
| | `msg reply` | 回复消息 |
| | `msg search` | 搜索消息 |
| | `msg chats` | 列出所有群聊 |
| **用户** | `user get` | 按邮箱/ID 查用户 |
| | `user search` | 按姓名搜索用户 |
| **文档** | `doc create` | 创建文档 |
| | `doc get` | 读取文档内容 |
| | `doc list` | 列出文档 |
| **多维表格** | `table records` | 查询记录 |
| | `table add` | 新增记录 |
| | `table update` | 更新记录 |
| | `table delete` | 删除记录 |
| | `table tables` | 列出所有表 |
| | `table fields` | 查看字段结构 |
| **日历** | `cal list` | 查看日程 |
| | `cal add` | 创建日程 |
| | `cal delete` | 删除日程 |
| **任务** | `task list` | 查看任务 |
| | `task add` | 创建任务 |
| | `task done` | 完成任务 |
| | `task delete` | 删除任务 |

---

### 常见报错

| 错误码 | 原因 | 解决方法 |
|--------|------|---------|
| `99991671` | 应用未授权该接口 | 在开发者后台开通对应权限并重新发布 |
| `230006` | 无日历访问权限 | 开通 `calendar:calendar` 权限 |
| `1254043` | 多维表格 App Token 错误 | 检查 URL 中的 App Token |
| `191001` | 日历 ID 无效 | 使用 Bot 真实日历 ID，不要用 `primary` |
| `Missing FEISHU_APP_ID` | 环境变量未加载 | 执行 `source ~/.zshrc` |

---

## English Docs

Give Claude Code full control over Feishu/Lark — send messages, create docs, manage calendar events, and write to multi-dimensional tables, all through natural language.

> Zero-dependency Python CLI using the Feishu Open API. Works best with Claude Code.

### Installation

```bash
npx skills add joeseesun/feishu-lark-agent
```

---

### Natural Language Examples

Once installed and configured, just talk to Claude Code naturally — no commands to memorize.

---

**💬 Messaging**

> "Send a Feishu message to zhang@company.com: standup moved to 11am today"

Claude looks up the open_id by email, sends the message, and confirms.

---

> "Post in the team group chat: Friday afternoon tea, everyone's invited"

Claude finds the chat_id from your chat list and sends to the group.

---

**📄 Documents**

> "Create a Feishu doc titled '2026 Q2 OKR', content from /tmp/okr.md"

Claude creates the doc, writes the content, auto-grants you edit access, and returns the link.

---

> "Read the content of this Feishu doc: https://xxx.feishu.cn/docx/DOC_ID"

Claude extracts the document_id from the URL and returns the full text.

---

**📅 Calendar**

> "Schedule 'Product Review' tomorrow 3-4pm in Conference Room 3F"

Claude parses the time, creates the event, and auto-invites you (requires `FEISHU_OWNER_OPEN_ID`).

---

> "What's on my calendar this week?"

Claude queries the next 7 days of events and summarizes them.

---

**📊 Bitable**

> "Add a record to my reading list: Poor Charlie's Almanack, Charlie Munger, status: reading"
> (Table URL: https://xxx.feishu.cn/base/APP_TOKEN)

Claude checks the field schema first, then writes the record with correct field names.

---

> "Show me all records in the Bitable where status is 'Pending Review'"

Claude queries with Feishu filter syntax and displays the results.

---

**✅ Tasks**

> "Create a task: Prepare quarterly review, due March 25, note: need PPT and data dashboard"

Claude calls the Task API, creates the task, and returns the task ID.

---

**🔍 Multi-step**

> "Find a colleague named Wang Fang and send her a message saying I'd like her to join tomorrow's design review"

Claude searches for the user, confirms the match, then sends the message — two steps automatically chained.

---

> "Create a Feishu doc from /tmp/meeting_notes.md, then message product-team@company.com with the doc link"

Claude creates the doc, gets the URL, then sends the message with the link attached — all in one go.

---

### Step 1: Create a Feishu App and get App ID + App Secret

> This is the only manual step. Takes about 5 minutes.

**1. Open Feishu Developer Console**

Go to [https://open.feishu.cn/app](https://open.feishu.cn/app) and log in with your Feishu account.

**2. Create a custom app**

Click **"Create Enterprise Self-Built App"** in the top right. Fill in the app name (e.g. "My AI Assistant") and description.

**3. Get App ID and App Secret**

After creation, go to **"Credentials & Basic Info"** and copy:

```
App ID:     cli_xxxxxxxxxxxxxxxxx
App Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**4. Enable permissions**

Go to **"Permission Management"** and enable the permissions you need:

| Permission | Purpose |
|-----------|---------|
| `im:message` | Read messages |
| `im:message:send_as_bot` | Send messages as bot |
| `docx:document` | Create/read documents |
| `drive:drive` | Manage document permissions |
| `bitable:app` | Bitable operations |
| `calendar:calendar` | Calendar read/write |
| `task:task:write` | Task management |
| `contact:user.id:readonly` | Look up users by email |

**5. Publish the app**

Go to **"Version Management & Release"** → Create version → Submit for release. The enterprise admin needs to approve it (if you're the admin, you can approve immediately).

---

### Step 2: Get your Open ID (optional but recommended)

Your Open ID (`ou_` prefix) is your unique identifier in Feishu. When set, documents and calendar events are automatically shared with you — no manual sharing needed.

**Method 1: Via API (recommended)**

Complete Step 3 first, then run:

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py user get --email your@email.com
# The user_id field in the result is your Open ID (starts with ou_)
```

**Method 2: Via group chat**

If you own a group chat:

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py msg chats
# Find a group you created — owner_id is your Open ID
```

---

### Step 3: Set environment variables

Add to `~/.zshrc` (or `~/.bashrc`):

```bash
export FEISHU_APP_ID=cli_your_app_id
export FEISHU_APP_SECRET=your_app_secret

# Optional: auto-add yourself to docs/calendar events
export FEISHU_OWNER_OPEN_ID=ou_your_open_id
```

Reload:

```bash
source ~/.zshrc
```

Verify setup:

```bash
python3 ~/.claude/skills/feishu-lark-agent/feishu.py msg chats
# If you see a list of chats, you're all set ✓
```

---

### Using with Claude Code

Once installed, just tell Claude Code in natural language:

```
Send a Feishu message to zhang@company.com: "Meeting moved to 3pm today"
```

```
Create a Feishu doc titled "Q2 OKR Planning"
```

```
Schedule "Product Review" tomorrow at 10am-11am in Conference Room 3F
```

```
Show me all "In Progress" records in my Bitable
```

Claude Code will automatically handle the rest.

---

### Common Scenarios

#### Messaging

```bash
# Send to a user by email
python3 feishu.py msg send --email colleague@company.com --text "Report submitted, please review"

# Send to a group chat
python3 feishu.py msg send --chat oc_xxxxxxxx --text "Standup in 10 minutes"

# Send from a file
python3 feishu.py msg send --email boss@company.com --file /tmp/report.txt

# List all chats
python3 feishu.py msg chats
```

#### Documents

```bash
# Create a document (auto-grants you edit access if FEISHU_OWNER_OPEN_ID is set)
python3 feishu.py doc create --title "Q2 Planning"

# Create from Markdown file
python3 feishu.py doc create --title "Meeting Notes" --file /tmp/meeting.md

# Read document content
python3 feishu.py doc get --id DOC_ID_FROM_URL
```

#### Calendar

```bash
# List upcoming events
python3 feishu.py cal list --calendar YOUR_CALENDAR_ID

# Create an event (auto-invites you if FEISHU_OWNER_OPEN_ID is set)
python3 feishu.py cal add \
  --title "Weekly Sync" \
  --start "2026-03-16 10:00" \
  --end "2026-03-16 11:00" \
  --location "Conference Room 3F" \
  --calendar YOUR_CALENDAR_ID
```

> **How to get Calendar ID**: The bot uses a tenant access token and can only access its own calendar. Run this to find the real calendar ID:
> ```bash
> python3 -c "
> import sys, os, json; sys.path.insert(0, os.path.expanduser('~/.claude/skills/feishu-lark-agent'))
> import feishu
> r = feishu.api('GET', '/calendar/v4/calendars', params={'page_size': 50})
> print(json.dumps(r, indent=2))
> "
> ```

#### Bitable (Multi-dimensional Tables)

```bash
# App Token is in the URL: feishu.cn/base/APP_TOKEN
# Check fields first before writing
python3 feishu.py table fields --app bASc1234xxx --table tblXXXX

# Query records with filter
python3 feishu.py table records --app bASc... --table tbl... \
  --filter 'AND(CurrentValue.[Status]="In Progress")'

# Add a record
python3 feishu.py table add --app bASc... --table tbl... \
  --data '{"Name":"New Project","Status":"Todo","Owner":"John"}'
```

#### Tasks

```bash
# List active tasks
python3 feishu.py task list

# Create a task with due date
python3 feishu.py task add --title "Submit Q2 Report" --due "2026-03-20"

# Mark as done
python3 feishu.py task done --id TASK_GUID
```

---

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `99991671` | App not authorized | Enable the required permission in developer console |
| `230006` | No calendar access | Enable `calendar:calendar` permission |
| `1254043` | Bitable App Token not found | Check the App Token in the URL |
| `191001` | Invalid calendar ID | Use the bot's real calendar ID, not `primary` |
| `Missing FEISHU_APP_ID` | Env vars not loaded | Run `source ~/.zshrc` |

---

## 📱 关注作者 / Follow the Author

- **X (Twitter)**: [@vista8](https://x.com/vista8)
- **微信公众号「向阳乔木推荐看」**:

<p align="center">
  <img src="https://github.com/joeseesun/terminal-boost/raw/main/assets/wechat-qr.jpg?raw=true" alt="向阳乔木推荐看公众号二维码" width="300">
</p>

## License

MIT
