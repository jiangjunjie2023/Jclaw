---
name: get-qiwei-message
description: 查询员工聊天记录分页列表。当用户需要获取员工与外部联系人的聊天记录时使用。需配置 QIWEI_OPEN_APP_KEY 和 QIWEI_OPEN_CORP_ID 环境变量。
homepage: ""
user-invocable: true
metadata:
  {
    "openclaw": {
      "emoji": "💬",
      "requires": {
        "bins": ["python3"],
        "env": ["QIWEI_OPEN_APP_ID", "QIWEI_OPEN_APP_KEY", "QIWEI_OPEN_CORP_ID"]
      },
      "os": ["darwin", "linux"]
    }
  }
---

# 企业微信消息查询

通过企业微信 OpenAPI 查询员工与外部联系人的聊天记录分页列表，支持按时间范围、员工ID、外部用户ID等条件筛选。

## 前置条件

- 已获取企业微信 **appKey** 与 **corpId**。
- 环境变量已配置（或在 `~/.openclaw/openclaw.json` 的 `skills.entries.get-qiwei-message.env` 中配置）：
  - `QIWEI_OPEN_APP_ID`：应用ID
  - `QIWEI_OPEN_APP_KEY`：应用秘钥，用于验签
  - `QIWEI_OPEN_CORP_ID`：企业ID
- 可选：`QIWEI_OPEN_BASE_URL`，不设则默认生产环境地址。

配置示例（`openclaw.json`，建议用环境变量占位不写死秘钥）：

```json5
{
  "skills": {
    "entries": {
      "get-qiwei-message": {
        "enabled": true,
        "env": {
          "QIWEI_OPEN_APP_ID": "${QIWEI_OPEN_APP_ID}",
          "QIWEI_OPEN_APP_KEY": "${QIWEI_OPEN_APP_KEY}",
          "QIWEI_OPEN_CORP_ID": "${QIWEI_OPEN_CORP_ID}"
        }
      }
    }
  }
}
```
- 技能目录路径在说明中可用 `{baseDir}` 引用。

详细接口说明与鉴权方式见 `{baseDir}/references/api.md`。

## 验证技能包是否能正常运行

在已拿到 appKey 和 corpId 后，可按以下步骤自测脚本与鉴权是否正常。

1. **设置环境变量**（当前终端或写入 `~/.profile` / 部署环境）  
   ```bash
   export QIWEI_OPEN_APP_ID="你的appId"
   export QIWEI_OPEN_APP_KEY="你的appKey"
   export QIWEI_OPEN_CORP_ID="你的corpId"
   ```

2. **执行查询**  
   进入技能目录（或将下面路径中的 `{baseDir}` 换成实际技能目录），执行：  
   ```bash
   cd {baseDir}
   python3 scripts/get_qiwei_message.py --payload-file scripts/examples/query.json
   ```

3. **看返回结果**  
   - **能拿到 JSON 响应**（无论 `success` 为 true 或 false）：说明网络、鉴权、脚本均正常；若为业务错误（如参数不合法），按接口文档调整请求体即可。  
   - **401 / 403**：鉴权失败，检查 appKey、corpId、环境变量是否与申请一致。  
   - **连接超时 / 无法解析域名**：检查网络与 `QIWEI_OPEN_BASE_URL` 是否正确。

4. **在 OpenClaw 中验证**  
   若技能已放入 OpenClaw 的加载目录（如 workspace 的 `skills/` 或 `~/.openclaw/skills`），可在对话中让 Agent 执行「查询企业微信消息」或「用企业微信消息接口查询一下」，确认 Agent 能正确调用本技能与脚本。

## 常用流程

1. **准备请求参数**  
   组装好 `startDate`、`endDate`、`staffId`、`externalUserIds` 等参数，写入 JSON 文件。

2. **执行查询**  
   ```bash
   python3 {baseDir}/scripts/get_qiwei_message.py --payload-file /path/to/query.json
   ```

## 请求体格式要点

- **必填**：`startDate`（开始日期，格式：YYYY-MM-DD）、`endDate`（结束日期，格式：YYYY-MM-DD）、`staffId`（员工ID）、`externalUserIds`（外部用户ID列表）。
- **可选**：`unionIds`（unionId列表）、`valueIdList`（valueId列表）、`pageSize`（每页大小，默认10）。

完整字段与示例见 `{baseDir}/references/api.md`。

## 安全与确认

- 不在日志或回复中输出 appKey 或完整签名。
- 验签逻辑以 Java 实现为准；若与脚本实现不一致，需按 Java 实现调整脚本。