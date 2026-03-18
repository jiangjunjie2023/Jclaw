# 教师精灵 OpenAPI 对接说明

根据《教师精灵对接文档》整理的接口与鉴权要点，供本技能脚本与模型参考。

## 环境与鉴权

- **域名**  
  - 生产：`https://gateway.staff.xdf.cn`  
  - 测试：`https://gateway.test.xdf.cn`
- **鉴权**  
  需先申请 appId、appSecret（对接文档要求调用需验签）。脚本从环境变量读取 `TEACHER_ELF_APP_ID`、`TEACHER_ELF_APP_SECRET`，可选 `TEACHER_ELF_BASE_URL`（默认生产域名）。
- **验签方式**（与官方 Java 示例一致）  
  - 算法：**HmacSHA1**  
  - 待签内容：请求体 **JSON 字符串**（UTF-8）  
  - 密钥：appSecret（appKey）  
  - 签名结果：**Base64** 编码后放入请求头  
  - 请求头：`appId`、`sign`（上述 Base64 签名）

## 接口列表

| 说明           | 路径                                   | 说明 |
|----------------|----------------------------------------|------|
| 提交前预检     | `POST /magic-open/api/group/send/task/preflight` | 提前检查组装的参数是否符合创建任务要求 |
| 提交任务       | `POST /magic-open/api/group/send/task/save`      | 发布任务到教师精灵 |
| 批量查询关系   | `POST /magic-open/relation/api/batch/query`      | 一次最多 50 学员 |
| 校验并初始化关系 | `POST /magic-open/relation/api/init/verify`    | 一次最多 100 学员 |

请求体均为 JSON，`Content-Type: application/json`。

## 提交任务请求体要点

- **必填**：`email`、`taskName`、`taskType`、`schoolId`、`receiverList`
- **taskType**（number）：1-课后服务 2-课前提醒 3-开班提醒 4-首课回访 5-续费沟通 6-其他 7-学习包学情反馈 8-作业任务反馈
- **receiverList[]**：每项必含 `receiveType`（number, 0-家长 1-本人 2-群聊）、`studentCode`（string）、`studentName`（string）、`sendContentList`（array）
- **sendContentList[]**：`content`（string）、`msgType`（string: text/link/file）；文本消息需 `msgType: "text"`，可选 `placeholderLabelList`（array）；链接/文件需 `id`、`msgFileSize`、`msgFileType` 等（见对接文档）

### 提交任务(save) 最小合法示例（类型严格）

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

注意：`taskType`、`schoolId`、`receiveType` 为 **数字**，不要写成字符串；`receiverList`、`sendContentList`、`placeholderLabelList` 为 **数组**。

## 响应与结果通知

- 成功：`success: true`，`data` 中含 `taskId`、`name`、`creator`、`createTime` 等
- 失败：`success: false` 或 `code` 非成功码，`data` 中可能有 `taskPreflightList`、`errorInfo`、`preflightStatusDesc` 等
- 发送结果由教师精灵侧推送到 Kafka（topic：`projects.work-wechat-job.topics.work-wechat-magic-task-send-result`），格式见对接文档

## YAPI 文档地址（需权限）

- 提交前预检：https://capi.staff.xdf.cn/project/1201/interface/api/92909  
- 提交任务：https://capi.staff.xdf.cn/project/1201/interface/api/91115  
- 批量查询关系：https://capi.staff.xdf.cn/project/1201/interface/api/94967  
- 验证并初始化关系：https://capi.staff.xdf.cn/project/1201/interface/api/94982  

开通 yapi 权限需联系对接文档中指定负责人。
