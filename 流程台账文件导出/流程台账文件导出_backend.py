import os
# -*- coding: utf-8 -*-
"""
i人事 后端插件 — 流程台账文件导出
链路: Access Token → 拉流程列表 → 提取文件
"""

from ihr360tools.runtime import handler
from ihr360tools.logger import logger
from urllib.parse import unquote, urlparse

import re


def _filename_from_url(url, fallback):
    """从 URL 末尾提取带扩展名的文件名"""
    try:
        path = urlparse(url).path.rstrip("/")
        name = unquote(path.split("/")[-1]) if "/" in path else ""
        if name and "." in name and not name.startswith("."):
            return name
    except Exception:
        pass
    return fallback


def _extract_form_fields(process):
    """从流程的 formInfoList 中提取非文件类的自定义字段"""
    fields = {}
    for f in (process.get("formInfoList") or []):
        code = f.get("inheritCode", "")
        title = f.get("title", "") or code
        val = f.get("value")
        # 跳过文件类字段（附件、图片）
        if code in ("accessoryIdList", "imageIdList"):
            continue
        # 跳过文件对象数组（含有 fileId/fileName 的对象）
        if isinstance(val, list):
            if any(isinstance(v, dict) and ("fileId" in v or "fileName" in v or "url" in v) for v in val if isinstance(v, dict)):
                continue
            fields[title] = "; ".join(str(v) for v in val)
        elif isinstance(val, dict):
            fields[title] = str(val.get("name") or val.get("text") or val.get("label", ""))
        elif val is not None:
            fields[title] = str(val)
    return fields

import os

APP_ID = os.environ.get("IHR360_APP_ID", "your-app_id")
import os

APP_SECRET = os.environ.get("IHR360_APP_SECRET", "your-app_secret")

TOKEN_URL = "https://openapi.ihr360.com/openapi/oauth/token"
LIST_URL = "https://openapi.ihr360.com/openapi/thirdparty/api/workflow/v1/process/finish/page"

PAGE_SIZE = 50
_cached_token = None


def _get_token() -> str:
    import urllib.request, base64
    from urllib.parse import urlencode
    auth = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    body = urlencode({"grant_type": "client_credentials", "scope": "client"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        import json
        data = json.loads(resp.read().decode())
        token = data.get("access_token") or data.get("data", {}).get("access_token")
        if not token:
            raise RuntimeError("access_token not in response")
        return token


async def get_token():
    global _cached_token
    if not _cached_token:
        _cached_token = _get_token()
    return _cached_token


def _post(url, body, token):
    import urllib.request, json
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError(f"API 返回非对象: type={type(parsed).__name__}")
        return parsed


async def fetch_list(token, max_pages=0):
    all_items = []
    page = 1
    while True:
        logger.info(f"列表第{page}页...")
        result = _post(LIST_URL, {
            "page": page, "rows": PAGE_SIZE, "source": None,
            "requireComments": True, "statuses": [],
        }, token)
        if result.get("code") != 0:
            if page == 1:
                raise RuntimeError(f"列表异常 code={result.get('code')}")
            break
        items = result.get("data", {}).get("content") or result.get("data", {}).get("rows") or []
        all_items.extend(items)
        if not items or (max_pages and page >= max_pages):
            break
        page += 1
    return all_items


def extract_files(processes):
    files = []
    for p in processes:
        pid = str(p.get("id", ""))
        form_fields = _extract_form_fields(p)
        base = dict(
            processId=pid,
            processCode=str(p.get("applicationCode") or p.get("processCode") or p.get("code") or p.get("serialNumber") or ""),
            createTime=str(p.get("applyTime") or p.get("createTime") or p.get("finishTime") or ""),
            applicantName=str(p.get("applicantName", "")),
            templateName=str(p.get("approvalSettingName", "")),
            title=str(p.get("respondentName", "")),
            formFields=form_fields,
        )

        for field in (p.get("formInfoList") or []):
            code = field.get("inheritCode", "")
            val = field.get("value")
            if code == "accessoryIdList" and isinstance(val, list):
                for url in val:
                    if isinstance(url, str) and url.startswith("http"):
                        files.append(dict(base, fileType="attach", fileId="", fileName=_filename_from_url(url, "附件"), fileUrl=url, officeFileUrl=""))
            if code == "imageIdList" and isinstance(val, list):
                for url in val:
                    if isinstance(url, str) and url.startswith("http"):
                        files.append(dict(base, fileType="image", fileId="", fileName=_filename_from_url(url, "图片"), fileUrl=url, officeFileUrl=""))
            if isinstance(val, list):
                for obj in val:
                    if isinstance(obj, dict):
                        fid = obj.get("fileId") or obj.get("dataId")
                        fname = obj.get("fileName") or obj.get("dataName") or _filename_from_url(obj.get("fileUrl", "") or obj.get("url", ""), "")
                        furl = obj.get("fileUrl") or obj.get("url", "")
                        if fid or fname or furl:
                            files.append(dict(base,
                                fileType="image" if str(obj.get("type", "")).startswith("image") else "attach",
                                fileId=str(fid or ""), fileName=str(fname or "文件"),
                                fileUrl=str(furl), officeFileUrl=str(obj.get("officeFileUrl", obj.get("previewUrl", ""))),
                            ))

        for comment in (p.get("comments") or []):
            data = comment.get("data") or comment
            for item, ftype in [
                (data.get("pics"), "image"),
                (data.get("attaches"), "attach"),
            ]:
                for obj in (item or []):
                    furl = str(obj.get("fileUrl", ""))
                    fname = str(obj.get("fileName", "") or _filename_from_url(furl, ""))
                    files.append(dict(base, fileType=ftype,
                        fileId=str(obj.get("fileId", "")), fileName=fname or "文件",
                        fileUrl=furl, officeFileUrl=str(obj.get("officeFileUrl", "")),
                    ))
    return files


@handler
async def handler(input: dict, context: dict) -> dict:
    logger.info("=== 流程台账文件导出 ===")
    try:
        token = await get_token()
    except Exception as e:
        return {"code": 1, "message": f"Token: {e}", "data": {}}

    max_pages = int(input.get("maxPages", 0))
    try:
        processes = await fetch_list(token, max_pages=1 if input.get("sample") else max_pages)
    except Exception as e:
        return {"code": 1, "message": f"列表: {e}", "data": {}}

    if input.get("raw") and processes:
        return {"code": 0, "message": f"raw: {len(processes)} 条", "data": processes}

    all_files = extract_files(processes)
    attach_cnt = sum(1 for f in all_files if f["fileType"] == "attach")
    image_cnt = sum(1 for f in all_files if f["fileType"] == "image")

    # 收集所有流程中出现的自定义字段标题
    all_form_keys = set()
    form_fields_by_template = {}
    for p in processes:
        tname = str(p.get("approvalSettingName", ""))
        form_fields = _extract_form_fields(p)
        all_form_keys.update(form_fields.keys())
        if tname and form_fields:
            form_fields_by_template[tname] = list(form_fields.keys())

    # 构建流程级数据（一流程一条记录）
    process_data = []
    file_by_pid = {}
    for f in all_files:
        file_by_pid.setdefault(f["processId"], []).append(f)

    for p in processes:
        pid = str(p.get("id", ""))
        pfiles = file_by_pid.get(pid, [])
        process_data.append({
            "processId": pid,
            "processCode": str(p.get("applicationCode") or p.get("processCode") or p.get("code") or p.get("serialNumber") or ""),
            "createTime": str(p.get("applyTime") or p.get("createTime") or p.get("finishTime") or ""),
            "applicantName": str(p.get("applicantName", "")),
            "templateName": str(p.get("approvalSettingName", "")),
            "title": str(p.get("respondentName", "")),
            "formFields": _extract_form_fields(p),
            "hasFile": len(pfiles) > 0,
            "fileCount": len(pfiles),
            "files": pfiles,
        })

    return {
        "code": 0, "message": "ok",
        "data": {
            "totalProcesses": len(processes),
            "totalFiles": len(all_files),
            "attachCount": attach_cnt,
            "imageCount": image_cnt,
            "formFieldKeys": sorted(all_form_keys),
            "formFieldsByTemplate": form_fields_by_template,
            "files": all_files,
            "processes": process_data,
        },
    }
