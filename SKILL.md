---
name: feishu-lark-agent
description: |
  飞书/Lark 全能操作 Agent（消息/文档/多维表格/日历/任务/用户）。

  ⚠️ skill 选择规则：
  - 发普通文本消息 → 本 skill（msg send）
  - 发富文本/卡片 → feishu-post / feishu-card
  - 查考勤 → feishu-attendance
  - 其余所有飞书操作 → 本 skill

  触发词（任一匹配即调用）：
  发飞书、发消息给、查群消息、回复飞书、搜飞书消息、列群聊、
  创建飞书文档、读飞书文档、查多维表、添加bitable记录、更新表格、
  飞书日历、查日程、加日程、飞书任务、创建任务、完成任务、
  查飞书用户、找联系人、获取open_id
---

# Feishu Lark Agent

## Run

```bash
source ~/.zshrc && python3 ~/.claude/skills/feishu-lark-agent/feishu.py <category> <action> [--key value ...]
```

---

## ID 格式速查（关键）

| 前缀 | 类型 | 用途 |
|------|------|------|
| `ou_` | open_id | 用户 ID，用于 `--to` |
| `oc_` | chat_id | 群聊 ID，用于 `--chat` |
| 邮箱 | email | 用于 `--email`，自动解析为 open_id |
| `docx/xxx` URL 后半段 | document_id | 飞书文档 ID |
| `base/xxx` URL 后半段 | app_token | 多维表格 App Token |

**如果只有姓名**：先 `user search --name "张三"` 获取 open_id，再执行目标操作。

---

## 命令速查

### 消息 `msg`
```bash
msg send  --to <open_id|chat_id>   --text "..."     # open_id → ou_, chat_id → oc_
msg send  --email <email>          --text "..."     # 用邮箱发
msg send  --chat <chat_id>         --text "..."     # 发群
msg send  --to <open_id>           --file /path     # 发文件内容
msg reply --to <message_id>        --text "..."
msg history --chat <chat_id>      [--limit 20]
msg search  --query "关键词"       [--limit 20]
msg chats  [--limit 50]                             # 列出所有群聊
```

### 用户 `user`
```bash
user search --name "张三"          # 模糊搜索，返回 open_id
user get    --email <email>        # 精确查询
user get    --id <open_id>
```

### 文档 `doc`
```bash
doc create  --title "标题"  [--content "markdown内容"]  [--file /path.md]
doc get     --id <document_id>     # 从 URL feishu.cn/docx/DOC_ID 取
doc list   [--folder <token>]     [--limit 50]
```
> 创建后自动授权 `FEISHU_OWNER_OPEN_ID` 编辑权限。

### 多维表格 `table`
```bash
table tables  --app <token>                         # 先列出所有 table
table fields  --app <token>  --table <id>           # 必须先查字段！
table records --app <token>  --table <id>  [--filter 'AND(CurrentValue.[状态]="进行中")']  [--limit 100]
table add     --app <token>  --table <id>  --data '{"字段名":"值"}'
table update  --app <token>  --table <id>  --record <recXXX>  --data '{"字段名":"新值"}'
table delete  --app <token>  --table <id>  --record <recXXX>
```
> **App token 在 URL 中**：`feishu.cn/base/APP_TOKEN`

### 日历 `cal`
```bash
cal calendars                                    # ⚠️ 第一步：列出 Bot 可访问的日历，获取 cal_id
cal list   --calendar <cal_id>   [--days 7]
cal add    --calendar <cal_id>   --title "..." --start "YYYY-MM-DD HH:MM" --end "YYYY-MM-DD HH:MM"  [--location "..."]  [--attendees "a@x.com,b@x.com"]
cal delete --calendar <cal_id>   --id <event_id>
```
> **⚠️ 重要**：Bot 无法访问个人日历（`primary` 会报错）。必须先 `cal calendars` 获取 Bot 自己的日历 ID，再用该 ID 操作。

### 任务 `task`
```bash
task list  [--completed true]  [--limit 50]
task add   --title "..."  [--due "YYYY-MM-DD"]  [--note "..."]
task done  --id <task_guid>
task delete --id <task_guid>
```

---

## 高频场景（直接复制执行）

**1. 按姓名发消息**
```bash
# step1 获取 open_id
python3 feishu.py user search --name "张三"
# step2 发消息
python3 feishu.py msg send --to ou_xxx --text "你好"
```

**2. 给群发消息**（已知群名 → 先查 chat_id）
```bash
python3 feishu.py msg chats        # 找到目标群的 chat_id (oc_xxx)
python3 feishu.py msg send --chat oc_xxx --text "通知内容"
```

**3. 添加多维表记录**（先查字段避免字段名写错）
```bash
python3 feishu.py table fields --app APP_TOKEN --table TABLE_ID
python3 feishu.py table add --app APP_TOKEN --table TABLE_ID --data '{"标题":"xxx","状态":"进行中"}'
```

**4. 创建文档并写入内容**
```bash
python3 feishu.py doc create --title "会议记录" --content "# 会议记录\n\n## 议题\n- 内容"
```

**5. 查看近期日程**（先查可用日历）
```bash
python3 feishu.py cal calendars                  # 获取 Bot 的日历 ID
python3 feishu.py cal list --calendar <cal_id> --days 7
```

**6. 创建日程**（先查日历 ID）
```bash
python3 feishu.py cal calendars                  # 先获取 cal_id
python3 feishu.py cal add --calendar <cal_id> --title "周会" --start "2026-03-20 10:00" --end "2026-03-20 11:00"
```

---

## 错误速查

| 错误码 | 原因 | 解决 |
|--------|------|------|
| `99991671` | 权限未开通 | 飞书开放平台添加权限 |
| `230006` | 日历权限缺失 | 开通 `calendar:calendar` |
| `1254043` | Bitable 未找到 | 检查 URL 中的 app_token |
| `191001` | 日历 ID 错误 | 不能用 `primary`，用真实 cal_id |
| `Missing FEISHU_APP_ID` | 环境变量未加载 | `source ~/.zshrc` |
