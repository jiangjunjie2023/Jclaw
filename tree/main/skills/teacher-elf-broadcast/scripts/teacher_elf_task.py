#!/usr/bin/env python3
"""
教师精灵群发任务 OpenAPI 最终版
- 读取指定JSON文件作为请求体（与Java使用相同数据）
- 100%对齐Java的签名逻辑（HmacSHA1 + UTF-8 + Base64）
- 全步骤调试日志，方便核对
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
from typing import Any
from collections import OrderedDict

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError  # type: ignore

# 全局配置（与 SKILL 一致：不设则默认生产）
DEFAULT_BASE_URL = os.environ.get("TEACHER_ELF_BASE_URL", "").strip() or "https://gateway.staff.xdf.cn"

ENDPOINTS = {
    "preflight": "/magic-open/api/group/send/task/preflight",
    "save": "/magic-open/api/group/send/task/save",
    "batch-query": "/magic-open/relation/api/batch/query",
    "init-verify": "/magic-open/relation/api/init/verify",
}


def _get_env(name: str, required: bool = True) -> str:
    """读取环境变量，缺失则退出"""
    val = os.environ.get(name, "").strip()
    if required and not val:
        print(f"Error: 环境变量 {name} 未设置！", file=sys.stderr)
        sys.exit(2)
    return val


def bytes_to_hex(bytes_data: bytes) -> str:
    """字节数组转16进制（与Java的bytesToHex对齐）"""
    return ''.join([f"{b:02x}" for b in bytes_data])


def compute_sign(app_secret: str, param_str: str) -> tuple[str, str]:
    """
    计算签名（返回签名+原始哈希16进制）
    :param app_secret: 密钥（对应Java的appKey）
    :param param_str: 待签字符串（JSON.toJSONString结果）
    :return: (签名, 原始哈希16进制)
    """
    # 1. 编码为UTF-8字节
    app_secret_bytes = app_secret.encode("UTF-8")
    param_bytes = param_str.encode("UTF-8")
    
    # 2. HmacSHA1计算
    hmac_obj = hmac.new(app_secret_bytes, param_bytes, hashlib.sha1)
    raw_hash = hmac_obj.digest()
    raw_hash_hex = bytes_to_hex(raw_hash)
    
    # 3. Base64编码
    sign = base64.b64encode(raw_hash).decode("ASCII")
    
    return sign, raw_hash_hex


def _is_debug() -> bool:
    return os.environ.get("TEACHER_ELF_DEBUG", "").strip().lower() in ("1", "true", "yes")


def load_payload_file(file_path: str) -> str:
    """
    读取JSON文件并序列化为与Java一致的字符串
    :param file_path: JSON文件路径
    :return: 无缩进、无空格、key不排序的JSON字符串
    """
    try:
        with open(file_path, "r", encoding="UTF-8") as f:
            payload = json.load(f, object_pairs_hook=OrderedDict)
        if _is_debug():
            print("\n===== 读取的JSON文件内容 =====")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    except FileNotFoundError:
        _emit_openclaw_result(False, f"JSON文件不存在: {file_path}")
        sys.exit(4)
    except json.JSONDecodeError as e:
        _emit_openclaw_result(False, f"JSON格式错误: {e}")
        sys.exit(5)

    param_str = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
        skipkeys=False,
        allow_nan=True,
    )
    return param_str


def _emit_openclaw_result(success: bool, message: str = "", data: dict | None = None) -> None:
    """向 stdout 输出单行 OPENCLAW_RESULT，供 OpenClaw/Agent 解析。"""
    out: dict[str, Any] = {"success": success}
    if message:
        out["message"] = message
    if data:
        out["data"] = data
    line = "OPENCLAW_RESULT=" + json.dumps(out, ensure_ascii=False)
    print(line, flush=True)


def _request(
    base_url: str,
    path: str,
    app_id: str,
    app_secret: str,
    param_str: str,
) -> dict[str, Any]:
    """发送POST请求"""
    url = base_url.rstrip("/") + path
    sign, raw_hash_hex = compute_sign(app_secret, param_str)

    if _is_debug():
        print("\n===== Python端步骤输出 =====")
        print(f"1. 待签字符串: {param_str}")
        print(f"   待签字符串UTF-8字节长度: {len(param_str.encode('UTF-8'))}")
        print(f"2. HmacSHA1原始哈希（16进制）: {raw_hash_hex}")
        print(f"3. Base64编码后的签名: {sign}")
        print(f"\n[DEBUG] 请求头: appId={app_id}, sign={sign[:20]}...")

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "appId": app_id,
        "sign": sign,
    }
    body_bytes = param_str.encode("UTF-8")

    try:
        req = Request(url, data=body_bytes, headers=headers, method="POST")
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("UTF-8"))
    except HTTPError as e:
        body = e.read().decode("UTF-8", errors="replace")
        if _is_debug():
            print(f"\n[ERROR] HTTP错误 {e.code}: {body}", file=sys.stderr)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            _emit_openclaw_result(False, f"HTTP {e.code}: {body[:200]}")
            raise
    except URLError as e:
        err_msg = f"网络错误: {e.reason if getattr(e, 'reason', None) else e}"
        print(err_msg, file=sys.stderr)
        _emit_openclaw_result(False, err_msg)
        sys.exit(3)


def main() -> None:
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="教师精灵 OpenAPI 客户端（最终版）")
    parser.add_argument(
        "action",
        choices=list(ENDPOINTS),
        help="操作类型：preflight=预检, save=提交任务, batch-query=批量查询关系, init-verify=初始化关系"
    )
    parser.add_argument(
        "--payload-file",
        type=str,
        required=True,  # 强制要求用户指定，无默认值
        help="JSON请求体文件路径（必填，例如：scripts/examples/task-save.json）"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help="API根地址（默认: TEACHER_ELF_BASE_URL 或生产网关）"
    )
    args = parser.parse_args()

    # 获取鉴权信息
    app_id = _get_env("TEACHER_ELF_APP_ID")
    app_secret = _get_env("TEACHER_ELF_APP_SECRET")

    # 加载并序列化请求体
    param_str = load_payload_file(args.payload_file)

    path = ENDPOINTS[args.action]
    result = _request(args.base_url, path, app_id, app_secret, param_str)

    if _is_debug():
        print("\n===== 接口返回结果 =====")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    success = result.get("success") is True or result.get("code") == 100000
    if success:
        _emit_openclaw_result(True, data=result.get("data"))
        sys.exit(0)
    else:
        msg = _extract_error_message(result)
        _emit_openclaw_result(False, message=msg)
        sys.exit(1)


def _extract_error_message(result: dict[str, Any]) -> str:
    """从接口返回中提取可读错误信息"""
    if isinstance(result.get("message"), str) and result["message"].strip():
        return result["message"].strip()
    if isinstance(result.get("msg"), str) and result["msg"].strip():
        return result["msg"].strip()
    data = result.get("data")
    if isinstance(data, dict):
        for key in ("errorInfo", "errorMsg", "preflightStatusDesc"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key].strip()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        first = data[0]
        if isinstance(first.get("errorInfo"), str):
            return first["errorInfo"]
        if isinstance(first.get("preflightStatusDesc"), str):
            return first["preflightStatusDesc"]
    return json.dumps(result, ensure_ascii=False)[:500]


if __name__ == "__main__":
    main()
