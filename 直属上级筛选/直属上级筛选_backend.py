import os
# -*- coding: utf-8 -*-
"""
i人事 后端插件 — 获取员工直属上级清单 + 获取汇报类型选项
"""

from ihr360tools.runtime import handler
from ihr360tools.logger import logger
import asyncio, urllib.request, json, base64
from urllib.parse import urlencode

# ============ 配置 ============
import os

APP_ID = os.environ.get("IHR360_APP_ID", "your-app_id")
import os

APP_SECRET = os.environ.get("IHR360_APP_SECRET", "your-app_secret")

TOKEN_URL = "https://openapi.ihr360.com/openapi/oauth/token"
SUPERIORS_URL = "https://openapi.ihr360.com/openapi/thirdparty/api/staff/v1/superiors"
OPTIONS_TYPES_URL = "https://openapi.ihr360.com/openapi/thirdparty/api/other/v1/options/codeTypes"
OPTIONS_VALUES_URL = "https://openapi.ihr360.com/openapi/thirdparty/api/other/v1/options/codeValues"

BATCH_SIZE = 100
MAX_RETRIES = 2
REQUEST_TIMEOUT = 15

_cached_token = None


# ============ 令牌管理 ============
def _get_token() -> str:
    global _cached_token
    if _cached_token:
        return _cached_token

    auth = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    body = urlencode({"grant_type": "client_credentials", "scope": "client"}).encode()

    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
        token = (
            data.get("access_token")
            or data.get("data", {}).get("access_token")
        )
        if not token:
            raise RuntimeError(f"access_token not in OAuth response: {str(data)[:200]}")
        _cached_token = token
        logger.info("OAuth token 获取成功")
        return token


async def get_token():
    return _get_token()


# ============ HTTP ============
def _post(url: str, payload: dict, token: str) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=UTF-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=UTF-8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


# ============ 获取汇报类型 ============
def fetch_report_types(token: str) -> dict:
    """
    查询可用的汇报类型选项
    返回: { code: 0, data: [{ codeValue, displayName }, ...] }
    """
    # 第1步：获取选项类型清单
    types_raw = _get(OPTIONS_TYPES_URL, token)
    if types_raw.get("code") != 0:
        return {"code": 1, "message": f"选项类型查询失败: {types_raw.get('message','')}", "data": []}

    type_list = types_raw.get("data", []) or []

    # 查找"汇报类型"或"直属领导类型"的 codeTypeId
    report_type_id = None
    for t in type_list:
        name = (t.get("displayName") or "").strip()
        cid = (t.get("codeTypeId") or "").strip()
        # 匹配关键字：汇报类型 / 报告类型 / ReportToType / 直属领导类型 / 直属上级类型
        if any(kw in name for kw in ["汇报类型", "报告类型", "直属领导", "汇报关系"]) or \
           any(kw in cid for kw in ["ReportToType", "reportTo"]):
            report_type_id = cid
            logger.info(f"找到汇报类型: {name} -> {cid}")
            break

    if not report_type_id:
        # 没找到，返回三个标准类型
        logger.warning("未找到自定义汇报类型配置，使用默认三种类型")
        return {
            "code": 0,
            "data": [
                {"codeValue": "Enum.Administration", "displayName": "行政"},
                {"codeValue": "Enum.Business", "displayName": "业务"},
                {"codeValue": "Enum.Finance", "displayName": "财务"},
            ]
        }

    # 第2步：获取选项值
    values_raw = _post(OPTIONS_VALUES_URL, [report_type_id], token)
    if values_raw.get("code") != 0:
        return {"code": 1, "message": f"选项值查询失败: {values_raw.get('message','')}", "data": []}

    groups = values_raw.get("data", []) or []
    options = []
    for group in groups:
        if group.get("codeTypeId") == report_type_id:
            for opt in (group.get("options") or []):
                cv = opt.get("codeValue", "")
                dn = opt.get("displayName", "")
                if cv and (opt.get("isValid", True) is not False):
                    options.append({"codeValue": cv, "displayName": dn})
            break

    if not options:
        # 回退到三种标准类型
        options = [
            {"codeValue": "Enum.Administration", "displayName": "行政"},
            {"codeValue": "Enum.Business", "displayName": "业务"},
            {"codeValue": "Enum.Finance", "displayName": "财务"},
        ]

    return {"code": 0, "data": options}


# ============ 获取上级清单 ============
async def fetch_superiors(token: str, staff_ids: list, report_to_type: str) -> dict:
    all_results = []
    errors = []
    total_batches = (len(staff_ids) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(staff_ids), BATCH_SIZE):
        batch = staff_ids[i : i + BATCH_SIZE]
        batch_no = i // BATCH_SIZE + 1

        success = False
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                await asyncio.sleep(1)

            try:
                raw = _post(SUPERIORS_URL, {
                    "staffIds": batch,
                    "reportToType": report_to_type,
                }, token)

                code = raw.get("code")
                if code == 0:
                    items = raw.get("data", [])
                    if isinstance(items, list):
                        all_results.extend(items)
                        success = True
                        break
                    else:
                        last_error = f"批次 {batch_no}: data 非列表"
                else:
                    last_error = f"批次 {batch_no}: code={code}, msg={raw.get('message','')}"

            except urllib.error.HTTPError as e:
                last_error = f"批次 {batch_no} HTTP {e.code}: {str(e)[:200]}"
                if e.code < 500:
                    break

            except Exception as e:
                last_error = f"批次 {batch_no} 异常: {str(e)[:300]}"

        if not success:
            errors.append(last_error or f"批次 {batch_no} 失败")

    if errors and not all_results:
        return {"code": 1, "message": "; ".join(errors), "data": []}

    return {
        "code": 0,
        "message": "SUCCESS" if not errors else f"部分成功: {'; '.join(errors)}",
        "data": all_results,
    }


# ============ 主入口 ============
@handler
async def handler(input: dict, context: dict) -> dict:
    """
    支持两种动作:
      action = "getReportTypes"    → 返回可用汇报类型列表
      action = "getSuperiors" (默认) → 获取员工直属上级

    输入(上级查询):
        staffIds: list[str]
        reportToType: str (默认 Enum.Administration)
    """
    action = input.get("action", "getSuperiors")

    try:
        token = await get_token()
    except Exception as e:
        return {"code": 1, "message": f"OAuth: {str(e)[:200]}", "data": []}

    # === 获取汇报类型 ===
    if action == "getReportTypes":
        return fetch_report_types(token)

    # === 获取上级清单 ===
    staff_ids = input.get("staffIds", [])
    # 兼容 FaaS 可能传递 { "input": { staffIds: [...] } } 格式
    if not staff_ids or not isinstance(staff_ids, list) or len(staff_ids) == 0:
        inner = input.get("input", {})
        if isinstance(inner, dict):
            staff_ids = inner.get("staffIds", [])

    if not staff_ids or not isinstance(staff_ids, list) or len(staff_ids) == 0:
        return {"code": 1, "message": "staffIds 不能为空", "data": []}

    report_to_type = input.get("reportToType", "Enum.Administration")

    logger.info(
        f"上级查询: {len(staff_ids)} 个员工, reportToType={report_to_type}"
    )

    return await fetch_superiors(token, staff_ids, report_to_type)
