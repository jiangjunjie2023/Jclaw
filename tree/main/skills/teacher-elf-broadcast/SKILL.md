---
name: teacher-elf-broadcast
description: 创建企微群发任务。当用户要求向学员、家长、企微群发消息，或创建教师精灵任务(如课后反馈、课前提醒）时使用。需先配置 appId、appSecret。
homepage: ""
user-invocable: true
metadata:
  {
    "openclaw": {
      "emoji": "📤",
      "requires": {
        "bins": ["python3"],
        "env": ["TEACHER_ELF_APP_ID", "TEACHER_ELF_APP_SECRET"]
      },
      "os": ["darwin", "linux"]
    }
  }
---

# 群发任务

通过教师精灵 OpenAPI 创建群发任务：提交前可预检参数，提交后任务由教师精灵侧执行并推送结果（见对接文档中的 Kafka 结果消息）。

## 前置条件

- 已申请教师精灵 **appId** 与 **appSecret**（对接文档要求调用需验签）。
- 环境变量已配置（或在 `~/.openclaw/openclaw.json` 的 `skills.entries.teacher-elf-broadcast.env` 中配置）：
  - `TEACHER_ELF_APP_ID`：应用 ID
  - `TEACHER_ELF_APP_SECRET`：应用秘钥，用于验签
- 可选：`TEACHER_ELF_BASE_URL`，不设则默认生产 `https://gateway.staff.xdf.cn`；测试环境可设为 `https://gateway.test.xdf.cn`。

配置示例（`openclaw.json`，建议用环境变量占位不写死秘钥）：

```json5
{
  "skills": {
    "entries": {
      "teacher-elf-broadcast": {
        "enabled": true,
        "env": {
          "TEACHER_ELF_APP_ID": "${TEACHER_ELF_APP_ID}",
          "TEACHER_ELF_APP_SECRET": "${TEACHER_ELF_APP_SECRET}"
        }
      }
    }
  }
}
```
- 技能目录路径在说明中可用 `{baseDir}` 引用。

详细接口说明与鉴权方式见 `{baseDir}/references/api.md`。

## 验证技能包是否能正常运行

在已拿到 appId 和 appSecret 后，可按以下步骤自测脚本与鉴权是否正常。

1. **设置环境变量**（当前终端或写入 `~/.profile` / 部署环境）  
   ```bash
   export TEACHER_ELF_APP_ID="你的appId"
   export TEACHER_ELF_APP_SECRET="你的appSecret"
   ```
   若用测试环境，再设置：  
   ```bash
   export TEACHER_ELF_BASE_URL="https://gateway.test.xdf.cn"
   ```

2. **用预检接口做一次请求**  
   进入技能目录（或将下面路径中的 `{baseDir}` 换成实际技能目录，如 `~/.openclaw/skills/teacher-elf-broadcast` 或仓库中的 `skills/teacher-elf-broadcast`），执行：  
   ```bash
   cd {baseDir}
   python3 scripts/teacher_elf_task.py preflight --payload-file scripts/examples/preflight-minimal.json
   ```
   先把 `scripts/examples/preflight-minimal.json` 里的 `email` 改成你的邮箱，`studentCode` 改成你环境里存在的学员编码（接口可能返回业务校验错误，但能说明请求已到达服务端且鉴权通过）。

3. **看返回结果**  
   - **能拿到 JSON 响应**（无论 `success` 为 true 或 false）：说明网络、鉴权、脚本均正常；若为业务错误（如参数不合法、学员不存在），按接口文档调整请求体即可。  
   - **401 / 403**：鉴权失败，检查 appId、appSecret、环境变量是否与申请一致。  
   - **连接超时 / 无法解析域名**：检查网络与 `TEACHER_ELF_BASE_URL` 是否正确（生产/测试域名）。

4. **在 OpenClaw 中验证**  
   若技能已放入 OpenClaw 的加载目录（如 workspace 的 `skills/` 或 `~/.openclaw/skills`），可在对话中让 Agent 执行「对教师精灵做一次预检」或「用教师精灵预检接口验证一下」，确认 Agent 能正确调用本技能与脚本。

## 常用流程

1. **预检（推荐先执行）**  
   检查组装的参数是否符合创建任务要求，避免提交后因校验失败退回。

   ```bash
   python3 {baseDir}/scripts/teacher_elf_task.py preflight --payload-file /path/to/task.json
   ```

   或从 stdin 传入 JSON：

   ```bash
   cat /path/to/task.json | python3 {baseDir}/scripts/teacher_elf_task.py preflight
   ```

2. **提交任务**  
   组装好 `email`、`taskName`、`taskType`、`schoolId`、`receiverList` 等（见对接文档），写入 JSON 文件后提交：

   ```bash
   python3 {baseDir}/scripts/teacher_elf_task.py save --payload-file /path/to/task.json
   ```

3. **批量查询关系 / 校验并初始化关系**  
   需要时调用（见 references/api.md）：
   - 批量查询关系（一次最多 50 学员）：`batch-query`
   - 校验并初始化关系（一次最多 100 学员）：`init-verify`

   ```bash
   python3 {baseDir}/scripts/teacher_elf_task.py batch-query --payload-file /path/to/query.json
   python3 {baseDir}/scripts/teacher_elf_task.py init-verify --payload-file /path/to/init.json
   ```

## 请求体格式要点

- **提交任务** 必填：`email`、`taskName`、`taskType`、`schoolId`、`receiverList`。
- `taskType`：1-课后服务 2-课前提醒 3-开班提醒 4-首课回访 5-续费沟通 6-其他 7-学习包学情反馈 8-作业任务反馈。
- `receiverList[].receiveType`：0-家长 1-本人 2-群聊。
- `receiverList[].sendContentList`：支持文本（含占位符 `#学员姓名#` 等）、链接（link）、文件（file）；链接/文件需按文档传 `msgType`、`msgFileSize`、`msgFileType` 等。

完整字段与示例见 `{baseDir}/references/api.md`。

## OpenClaw/Agent 调用规范

使用本技能时请严格按以下规范执行，否则容易出现「入参 JSON 格式错误」或「接口已报错却误判为成功」。

### 入参要求

1. **必须使用 `--payload-file` 指定 JSON 文件路径**，不要通过 stdin 或命令行片段传复杂 JSON。
2. **JSON 文件要求**：
   - 文件编码为 **UTF-8**；
   - 合法 JSON（可先用 `python3 -c "import json; json.load(open('你的文件.json'))"` 自检）；
   - 字段名、类型与下表一致，**不要**多写无关字段或错误类型（如 `taskType` 为数字不是字符串）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 发起人邮箱 |
| taskName | string | 是 | 任务名称 |
| taskType | number | 是 | 1–8，见上文 |
| schoolId | number | 是 | 学校 ID |
| receiverList | array | 是 | 接收人列表，见下 |

**receiverList[] 每项**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| receiveType | number | 是 | 0-家长 1-本人 2-群聊 |
| studentCode | string | 是 | 学员编码 |
| studentName | string | 是 | 学员姓名 |
| sendContentList | array | 是 | 内容列表，见下 |

**sendContentList[] 每项**（文本消息最少字段）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 正文，可用占位符如 `#学员姓名#` |
| msgType | string | 是 | 固定 `"text"` |
| placeholderLabelList | array | 否 | 占位符标签列表，无则 `[]` |

3. **可直接复用的最小示例**（保存为 `task.json` 后替换邮箱、学员编码等）：

```json
{
  "email": "your-email@xdf.cn",
  "taskName": "任务名称",
  "taskType": 6,
  "schoolId": 1,
  "receiverList": [
    {
      "receiveType": 0,
      "studentCode": "学员编码",
      "studentName": "学员姓名",
      "sendContentList": [
        {
          "content": "消息正文",
          "msgType": "text",
          "placeholderLabelList": []
        }
      ]
    }
  ]
}
```

### 结果解析（必须按此判断成功/失败）

脚本会在 **stdout 最后输出一行** 供 Agent 解析，格式固定为：

```
OPENCLAW_RESULT={"success": true|false, "message": "可选错误信息", "data": 可选接口返回数据}
```

- **成功**：`OPENCLAW_RESULT` 中 `success` 为 `true`，且进程 exit code 为 0。可把 `data` 中的 `taskId` 等告知用户。
- **失败**：`OPENCLAW_RESULT` 中 `success` 为 `false`，且进程 exit code 非 0。**必须**把 `message` 中的错误原因告知用户，不得回复「任务创建成功」。

**解析步骤建议**：在脚本完整输出中查找包含 `OPENCLAW_RESULT=` 的那一行，解析其后的 JSON，根据 `success` 与 `message` 决定回复内容；若未找到该行，则根据 exit code 和 stderr 判断（如文件不存在、JSON 格式错误等）。

**调试**：需要查看完整请求/响应时，可设置环境变量 `TEACHER_ELF_DEBUG=1` 再执行脚本，会输出待签字符串、接口返回等；正常派发时无需设置。

## 安全与确认

- 写操作（提交任务、初始化关系）前必须明确用户意图并确认。
- 不在日志或回复中输出 appSecret 或完整 token。
- 验签逻辑以对接文档为准；若与脚本实现不一致，需按文档调整脚本或联系接口提供方。
