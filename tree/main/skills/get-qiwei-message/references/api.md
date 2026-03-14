# 企业微信消息查询 API 文档

## 接口信息

- **接口名称**：查询员工聊天记录分页列表
- **接口路径**：`/msg/staff/chat`
- **请求方法**：POST
- **内容类型**：`application/json; charset=UTF-8`

## 请求参数

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| startDate | String | 是 | 开始日期，格式：YYYY-MM-DD |
| endDate | String | 是 | 结束日期，格式：YYYY-MM-DD |
| externalUserIds | Array<String> | 否 | 外部用户ID列表 |
| unionIds | Array<String> | 否 | unionId列表 |
| staffId | String | 否 | 员工ID |
| valueIdList | Array<String> | 否 | valueId列表 |
| pageSize | Integer | 否 | 每页大小，默认10 |
| sortMap | Object | 否 | 排序规则，默认按消息时间戳升序 |

### sortMap 结构

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| msgTimestamp | String | 否 | 排序方向：asc（升序）或 desc（降序） |

## 响应结构

### 成功响应

```json
{
  "success": true,
  "data": {
    "total": 100,
    "pageSize": 10,
    "pageNum": 1,
    "data": [
      {
        "msgId": "msg_123",
        "fromId": "staff_id_1",
        "toId": "external_user_id_1",
        "msgType": "text",
        "content": "您好，这是一条测试消息",
        "msgTimestamp": 1678456789000,
        "staffEntity": {
          "name": "张三",
          "avatar": "https://example.com/avatar.jpg"
        },
        "externalUserEntity": {
          "name": "李四",
          "avatar": "https://example.com/avatar2.jpg"
        }
      }
    ]
  },
  "errorCode": "",
  "errorMsg": ""
}
```

### 失败响应

```json
{
  "success": false,
  "data": null,
  "errorCode": "400",
  "errorMsg": "参数错误"
}
```

## 鉴权方式

### 签名生成

1. **待签字符串**：将请求体 JSON 对象序列化为字符串（无缩进、无空格、key不排序）
2. **签名算法**：HmacSHA1
3. **编码方式**：UTF-8
4. **结果处理**：Base64编码

### 请求头

| 头部名称 | 类型 | 必填 | 描述 |
| -------- | ---- | ---- | ---- |
| Content-Type | String | 是 | 固定为 `application/json; charset=UTF-8` |
| appId | String | 是 | 应用ID |
| sign | String | 是 | 签名值 |

## 签名生成示例（Python）

```python
import base64
import hmac
import hashlib
import json

app_key = "your_app_key"
param_dict = {
    "startDate": "2026-03-01",
    "endDate": "2026-03-14",
    "externalUserIds": ["external_user_id_1"],
    "staffId": "staff_id_1"
}

# 序列化为与Java一致的字符串
param_str = json.dumps(
    param_dict,
    ensure_ascii=True,
    separators=(",", ":"),
    sort_keys=False
)

# 计算签名
app_key_bytes = app_key.encode("UTF-8")
param_bytes = param_str.encode("UTF-8")
hmac_obj = hmac.new(app_key_bytes, param_bytes, hashlib.sha1)
raw_hash = hmac_obj.digest()
sign = base64.b64encode(raw_hash).decode("ASCII")

print("签名:", sign)
```

## 签名生成示例（Java）

```java
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.apache.commons.codec.binary.Base64;

String appKey = "your_app_key";
String param = "{\"startDate\":\"2026-03-01\",\"endDate\":\"2026-03-14\",\"externalUserIds\":[\"external_user_id_1\"],\"staffId\":\"staff_id_1\"}";

final String HMAC_SHA1_ALGORITHM = "HmacSHA1";
final String CHARSET_NAME = "UTF-8";

byte[] appKeyBytes = appKey.getBytes(CHARSET_NAME);
SecretKeySpec signingKey = new SecretKeySpec(appKeyBytes, HMAC_SHA1_ALGORITHM);
Mac mac = Mac.getInstance(HMAC_SHA1_ALGORITHM);
mac.init(signingKey);

byte[] rawHash = mac.doFinal(param.getBytes(CHARSET_NAME));
String sign = Base64.encodeBase64String(rawHash);

System.out.println("签名:" + sign);
```

## 错误码

| 错误码 | 描述 |
| ------ | ---- |
| 400 | 参数错误 |
| 401 | 鉴权失败 |
| 403 | 权限不足 |
| 500 | 服务器内部错误 |

## 注意事项

1. 请确保请求体中的 `startDate` 和 `endDate` 格式正确（YYYY-MM-DD）
2. 签名生成时请确保 JSON 序列化方式与 Java 一致（无缩进、无空格、key不排序）
3. 建议设置合理的 `pageSize`，避免单次请求返回过多数据
4. 若需要获取完整的聊天记录，可通过分页参数进行多次请求