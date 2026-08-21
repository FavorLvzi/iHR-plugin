---
name: rowan-ihr360-plugin
description: Rowan's verified iHR360 plugin development pattern library. Covers the framework rules, API patterns, design tokens, and debugging checklists for building single-file HTML plugins on the iHR360 platform. Use when building employee-facing HR tools (query pages, calculators, dashboards, exception lists) for iHR360.
---

# Rowan iHR360 插件开发通用技能

## 概述

iHR360（i人事）平台上的插件开发实战经验整合。每条规则都对应真实发生过的问题——不是理论推导，是踩坑记录。

**设计原则**：
- 只收录**通用**模式——具体业务逻辑（司龄计算规则、个税公式等）不在此处，归入各自插件文档
- 优先纯前端 Cookie 方案，需 OpenAPI 时才引入后端 FaaS
- 单文件 HTML，无外部依赖

## 适用范围

- 构建 iHR360 前端 HTML 插件页面（查询页、计算页、统计页、异常清单）
- 开发 iHR360 后端 Python 插件（数据处理、批量计算、OpenAPI 调用）
- 调试 API 调用问题（401、403、数据异常、按钮无响应）

## 默认假设

- 插件运行在 `plugin.ihr360.com` 子域名下，由 i人事框架沙盒托管
- 默认使用 Gateway API（`/web/gateway/` 前缀），Cookie + XSRF-TOKEN 自动鉴权
- 仅在 Gateway 无法覆盖时才用 OpenAPI（需要后端 FaaS 中转或直接 Bearer token）
- 中文界面

---

## 一、十一大铁律（绝对不可违反）

### 铁律 1：框架脚本必须位于 `<head>` 最前

```html
<head>
  <script src="https://plugin.ihr360.com/system/ihr360-base-framework.js"></script>
  <!-- 所有其他内容在框架之后 -->
```

**原因**：框架脚本会接管 DOM 事件系统。若放在 `<body>` 之后，框架加载时会清除之前已注册的所有事件绑定，导致按钮失效。

### 铁律 2：`html-page-builder` 元数据注释（必需）

```html
<!-- ihr360-html-page-builder: {"schema":"1","title":"页面标题","generatedAt":"2026-06-12T16:00:00+08:00"} -->
```

- i人事框架通过此注释识别插件页面，**必须保留**
- 修改文件后建议更新 `generatedAt` 时间戳，帮助平台感知变更

### 铁律 3：所有事件绑定必须用 `addEventListener`，禁止 `onclick`

```javascript
// ✅ 正确
document.getElementById('btn').addEventListener('click', function() { ... });

// ❌ 禁止 — i人事沙盒会屏蔽内联事件属性
<button onclick="doSomething()">查询</button>
```

### 铁律 4：API 原始数据必须转换为可读格式后再展示

从 i人事 API 获取的数据中，涉及**编码型字段**（时间戳日期、审批编码、文件 ID 等），必须在前端展示前转换为人类可读的格式。

```javascript
// ✅ 正确 — 时间戳先解析再格式化
var d = parseDate(s.enrollInDate);         // 处理毫秒时间戳
var display = d ? fmtDate(d) : '-';        // 输出 "2024-05-22"

// ✅ 正确 — 审批编码、字段 ID 等直接取 readable 版本
var code = s.processCode || s.processId;   // "PRC20240522001"
var label = s.templateName || s.templateId;// "请假审批"

// ❌ 禁止 — 直接显示原始编码
<td>{{s.enrollInDate}}</td>                // 显示 "1716334000000"
<td>{{s.templateId}}</td>                  // 显示 "tpl_abc123"
```

**需要转换的常见编码字段类型**：

| 原始格式 | 典型值 | 转换目标 | 转换方式 |
|---------|--------|---------|---------|
| 毫秒时间戳 | `1716334000000` | `2024-05-22` | `parseDate()` → `fmtDate()` |
| UNIX 秒时间戳 | `1716334000` | `2024-05-22` | `new Date(ts * 1000)` → `fmtDate()` |
| 审批编码 | `PRC12345` | 原样显示（已是 readable） | 直接使用 |
| UUID/ID | `tpl_abc123_form_xyz` | 配合对应 label 字段展示 | `s.templateName || s.templateId` |
| 枚举值 | `FULLTIME`, `IN_SERVICE` | 全职, 在职 | 使用 STAFF_TYPE_MAP 等映射表 |
| 布尔值 | `true`, `false` | 是, 否 | 三元表达式转换 |

**原因**：i人事 API 返回的原始数据通常是内部存储格式（时间戳数字、系统 ID、枚举码），直接显示对最终用户毫无意义，严重降低插件可用性。

### 铁律 5：Gateway API 调用必须带 Cookie + XSRF-TOKEN 鉴权

```javascript
// ✅ 正确 — 统一封装的 request() 函数已包含
var DEFAULT_HEADERS = {
  "x-requested-with": "XMLHttpRequest",
  "IHR-Request-Origin": "frontend_skill_page",
};
function request(url, options) {
  var xsrfToken = getCookie("XSRF-TOKEN") || getCookie("xsrf-token");
  return fetch(url + "?r_id=" + Date.now().toString(36), {
    credentials: "include",                                          // 必须 — 带 Cookie
    headers: Object.assign({}, DEFAULT_HEADERS,
      xsrfToken ? {"x-xsrf-token": xsrfToken} : {}),                // 必须 — 从 Cookie 读 XSRF
    method: (options || {}).method || "GET",
    body: (options || {}).body,
  });
}

// ❌ 禁止 — 缺少 credentials 或 x-xsrf-token
fetch(url, { method: "GET" });                                      // → 401 Unauthorized
```

**`credentials: "include"` 和 `x-xsrf-token` 两者缺一不可**。缺少任一都会导致 Gateway API 返回 401/403。统一封装的 `request()` 函数自动处理这两项，禁止绕过封装直接调 `fetch()`。

**违反后果**：所有 Gateway API 调用返回 401 Unauthorized，页面数据为空。

### 铁律 6：FaaS 调用四要素缺一不可

```javascript
// ✅ 正确 — 四个要素都必须包含
fetch(FAAS_URL, {
  method: "POST",
  mode: "cors",
  credentials: "omit",                                              // 要素1：防止自动带 Cookie 触发 CORS 报错
  headers: {
    "Content-Type": "application/json",
    "Api-Key": FAAS_KEY,                                            // 要素2：请求头必须是 Api-Key（不是 x-api-key）
  },
  body: JSON.stringify({"input": {}}),                              // 要素3：请求体必须是 {"input": {...}}
});
// 要素4：FaaS 返回 {code:0, data:<result>}，需要解一层 data 包裹
var raw = await resp.json();
var result = raw.data;                                              // 解包裹

// ❌ 错误1：credentials: "include" 或省略 → CORS 报错
// ❌ 错误2：请求头 "x-api-key" 或 "X-Api-Key" → 401 "Required request header 'Api-Key'"
// ❌ 错误3：请求体直接传对象 → 后端 input 参数接收不到
// ❌ 错误4：直接用 raw.data.list 而非 raw.data.data 或先用 raw.data 解一层 → undefined
```

**违反任意一条**：FaaS 调用失败或数据为空。

### 铁律 7：Gateway 与 OpenAPI 路径不互通，混用即 401

| | 前端 Cookie 插件 | 后端 Python 插件 |
|--|----------------|----------------|
| 路径前缀 | `/web/gateway/...` | `/openapi/...` |
| 域名 | 浏览器当前域名（`plugin.ihr360.com`） | `openapi.ihr360.com` |
| 鉴权 | Cookie + XSRF-TOKEN | OAuth Bearer token（AppID+AppSecret） |

```javascript
// ✅ 正确 — 前端调花名册用 Gateway
"/web/gateway/roster/aggregate/v1/staffs/search"

// ✅ 正确 — 后端调工作流用 OpenAPI
"https://openapi.ihr360.com/openapi/thirdparty/api/workflow/..."

// ❌ 禁止 — 前端直接调 OpenAPI（无 Bearer token）→ 401
"https://openapi.ihr360.com/openapi/..."

// ❌ 禁止 — 后端用 Gateway 路径（无 Cookie）→ 401
"/web/gateway/roster/..."
```

**用错路径直接返回 401，无任何数据**。

### 铁律 8：CSV 导出必须加 UTF-8 BOM（`\uFEFF`）

```javascript
// ✅ 正确
var BOM = "\uFEFF";
var csvContent = BOM + headers.join(",") + "\n" + rows;

// ❌ 错误 — 不加 BOM 在 Excel 中中文变成乱码
var csvContent = headers.join(",") + "\n" + rows;  // "姓名" → "���"
```

**违反后果**：用户下载的 CSV 在 Excel 中全中文乱码，插件导出的数据完全不可用。

### 铁律 9：含表格的插件必须有列显隐齿轮（列多了折叠起来）

```html
<!-- ✅ 必须 — 齿轮按钮 + 弹出面板 -->
<span class="settings-wrap">
  <button class="settings-btn" id="settingsBtn" title="列设置">⚙</button>
  <div class="settings-pop" id="settingsPop"></div>
</span>
```

表格列数 ≥8 时，非核心列必须默认隐藏，用户通过齿轮面板按需打开。核心列（姓名、工号、部门等）始终显示，自定义字段/补充字段默认折叠。

设置必须保存到 `localStorage`，关闭页面后不丢失。

**违反后果**：列太多时页面拥挤，用户无法聚焦关键信息，水平滚动条过长。

### 铁律 10：含表格的插件必须有表头宽度拖拽调整

每个 `<th>` 右侧必须有拖拽手柄，鼠标拖拽可调节列宽，拖拽时同步更新同列所有 `<td>`：

```css
th .resizer{position:absolute;right:0;top:0;bottom:0;width:5px;cursor:col-resize;z-index:2}
```

- 最小宽度 40px，防止拖拽过头
- `rebuildHeader()` 后**必须**重新调用 `initColResize()`
- 列显隐变化后也需重新绑定

**违反后果**：列宽固定不可调，某些列内容过长被截断，用户无法手动展开查看。

### 铁律 11：含表格的插件必须有分页行数选择器（25/50/100/200）

每页展示行数可自定义，选中的值持久化到 `localStorage`：

```html
<span class="page-size">每页<select id="pageSizeSelect">
  <option value="25">25</option>
  <option value="50">50</option>
  <option value="100">100</option>
  <option value="200">200</option>
</select>条</span>
```

- 默认 25 条/页
- 切换后重置到第 1 页
- 200 为**可选项**（数据量大时才有意义），25/50/100 为必选项

**违反后果**：数据量较大时用户无法提高单页密度，翻页次数过多，体验极差。

---

## 二、开发工作流

### 2.1 识别页面模式

| 模式 | 适用场景 | 典型特征 |
|------|---------|---------|
| 查询页 | 条件搜索、列表展示 | 筛选栏 + 表格 + 分页 |
| 计算页 | 输入参数、计算结果 | 表单 + 结果显示区 |
| 统计页 | 汇总数据、趋势分析 | 统计卡片 + 图表 + 分段列表 |
| 异常清单 | 筛选异常数据 | 条件筛选 + 标注突出 + 导出 |

### 2.2 选择数据源

| 数据源 | 鉴权方式 | 调用方 | 适用场景 |
|--------|---------|--------|---------|
| Gateway API | Cookie + XSRF | 前端 HTML 插件 | 花名册、离职、年假、试用期等基础查询 |
| OpenAPI | OAuth Bearer token | **后端 FaaS** 或独立调用 | 合同、身份证号、考勤日报/月报、工作流、审批等 Gateway 不提供的接口 |
| FaaS（后端 Python） | Api-Key header | 前端直调 | Gateway 无法覆盖、需 OAuth 鉴权的 OpenAPI 场景 |

**推荐路线**：优先尝试 Gateway API → 不够用再加 FaaS 后端

**已验证的关键发现（2026-06-12）**：
- Gateway 花名册搜索接口已在 6 个插件中验证，可返回 `probationStatus` / `probationEndDate` 等 15+ 个字段
- 流程台账文件导出**必须走 FaaS**（工作流接口仅 OpenAPI 提供，无 Gateway 代理通道）
- 花名册查询类插件优先走纯前端 Gateway 方案，除非目标数据仅 OpenAPI 有

### 2.3 构建页面 → 交付

详见下方各章节。

---

## 三、前端插件核心模式

### 3.1 请求封装

```javascript
var DEFAULT_HEADERS = {
  "x-requested-with": "XMLHttpRequest",
  "IHR-Request-Origin": "frontend_skill_page",
};

function getCookie(name) {
  var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

function request(url, options) {
  options = options || {};
  var headers = options.headers || {};
  var credentials = options.credentials || "include";
  var restOptions = {};
  for (var k in options) {
    if (k !== "headers" && k !== "credentials") restOptions[k] = options[k];
  }
  var separator = url.indexOf("?") !== -1 ? "&" : "?";
  var urlWithRId = url + separator + "r_id=" + Date.now().toString(36);
  var xsrfToken = getCookie("XSRF-TOKEN") || getCookie("xsrf-token");
  return fetch(urlWithRId, {
    credentials: credentials,
    headers: Object.assign({}, DEFAULT_HEADERS, xsrfToken ? {"x-xsrf-token": xsrfToken} : {}, headers),
    method: restOptions.method || "GET",
    body: restOptions.body || undefined,
  });
}
```

**要点**：
- `credentials: "include"` — 告诉浏览器附带域名的 Cookie
- `x-xsrf-token` — 从 Cookie 动态读取，i人事 平台的 CSRF 防护
- `r_id` — 缓存破坏参数，时间戳随机化
- `IHR-Request-Origin` — 标识请求来源，i人事 日志追踪用

### 3.2 分页全量拉取

两种模式，推荐使用第二种（`fields` + `flexSearchItems`）：

**模式 A：使用 `query` 对象（旧模式，参考司龄计算）**

```javascript
async function queryAllPages(url, query) {
  var all = [], page = 1, hasMore = true, pageSize = 100;

  while (hasMore) {
    var res = await request("POST", url, {
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query: query, page: page, pageSize: pageSize}),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    var data = await res.json();
    if (data.code !== 0) throw new Error(data.message || "code=" + data.code);

    var list = data.data.list || [];
    all = all.concat(list);

    if (page >= (data.data.totalPages || 0)) hasMore = false;
    else page++;
  }
  return all;
}
```

**模式 B：使用 `fields` + `flexSearchItems`（新模式，花名册搜索推荐）**

```javascript
async function queryAllPages(url, body) {
  var all = [], page = 1, hasMore = true, pageSize = 100;

  while (hasMore) {
    var res = await request("POST", url, {
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        fields: body.fields,                                                  // 指定返回的字段列表
        flexSearchItems: body.flexSearchItems,                                // 筛选条件数组
        page: page,
        pageSize: pageSize,
      }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    var data = await res.json();
    if (data.code !== 0) throw new Error(data.message || "code=" + data.code);

    var list = data.data.list || [];
    all = all.concat(list);

    if (page >= (data.data.totalPages || 0)) hasMore = false;
    else page++;
  }
  return all;
}

// 调用示例
var fields = ["staffName", "departmentName", "probationStatus", "probationEndDate"];
var flexSearchItems = [
  {fieldType: "EQUAL", searchKey: "staffStatus", searchParam: "IN_SERVICE"},
];
queryAllPages("/web/gateway/roster/aggregate/v1/staffs/search",
  {fields: fields, flexSearchItems: flexSearchItems});
```

**要点**：
- 使用 `async/await + while`（不用 `Promise.all` 并发翻页）
- 每页最大 100 条
- 用 `data.data.totalPages` 判断终止条件（不是 `data.data.list.length === 0`）
- 分页查询**已豁免限流**，不需要 rate limiter
- 模式 B 用 `fields` 数组精确控制返回字段，`flexSearchItems` 数组灵活组合筛选条件

### 3.3 加载动画

大数量拉取场景（预估 >100 条）必须有加载动画：

```html
<div class="loading-box" id="loadingCard">
  <img src="https://plugin.ihr360.com/system/dancingkitty.gif" class="loading-character" />
  <div class="loading-title" id="loadingTitle">小喵正在努力拉取数据...</div>
  <div class="progress-track">
    <div class="progress-fill" id="progressFill"></div>
  </div>
  <div class="loading-status" id="loadingStatus">准备中...</div>
  <div class="loading-detail" id="loadingDetail"></div>
</div>
```

```javascript
function updateProgress(page, totalPages) {
  var fill = document.getElementById("progressFill");
  if (totalPages > 0) {
    fill.classList.remove("indeterminate");
    fill.style.width = Math.round(page / totalPages * 100) + "%";
  } else {
    fill.classList.add("indeterminate");
  }
  document.getElementById("loadingStatus").textContent = "第 " + page + "/" + totalPages + " 页";
  document.getElementById("loadingDetail").textContent = "已获取 " + allData.length + " 条数据";
}
```

### 3.4 CSV 导出

```javascript
function exportCSV(headers, rows, filename) {
  var BOM = "\uFEFF";
  var lines = [BOM + headers.join(",")];
  for (var i = 0; i < rows.length; i++) {
    lines.push(rows[i].map(function(v) {
      return '"' + String(v || "").replace(/"/g, '""') + '"';
    }).join(","));
  }
  var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = filename || "导出_" + new Date().toISOString().slice(0, 10) + ".csv";
  a.click();
  URL.revokeObjectURL(url);
}
```

**关键**：`\uFEFF` BOM 头确保 Excel 正确识别 UTF-8 编码的中文。

### 3.5 空态展示

```html
<div class="empty-state" id="emptyState" style="display:none;">
  <p>暂无数据</p>
  <p class="helper-text">请检查筛选条件或数据源是否有数据</p>
</div>
```

- 数据为空时显示空态，不显示空白表格
- 加载完成后无数据才显示，**不在加载中时显示**

### 3.6 表格基础功能（必备模板）

每个含表格的插件**必须**包含以下两个功能，直接作为固定模板写入 HTML：

#### 3.6.1 每页行数自定义（25/50/100/200）

在分页栏左侧加一个行数选择器，选中的值保存到 `localStorage`：

```html
<span class="page-size">每页<select id="pageSizeSelect">
  <option value="25">25</option>
  <option value="50">50</option>
  <option value="100">100</option>
  <option value="200">200</option>
</select>条</span>
```

```css
.page-size{display:flex;align-items:center;gap:4px;margin-left:12px;font-size:12px;color:var(--neutral-500)}
.page-size select{height:26px;border:1px solid var(--neutral-200);border-radius:var(--radius-control);padding:0 4px;font-size:12px;color:var(--neutral-600);outline:0;background:#fff;cursor:pointer}
```

```javascript
/* 每页行数，从 localStorage 读取 */
var pageSize=parseInt(localStorage.getItem('procPageSize'))||25;
document.getElementById('pageSizeSelect').value=pageSize;
document.getElementById('pageSizeSelect').addEventListener('change',function(){
  pageSize=parseInt(this.value);
  try{localStorage.setItem('procPageSize',pageSize)}catch(e){}
  currentPage=1;renderPage();
});
```

- 默认 25 条/页
- 切换后**重置到第 1 页**
- `localStorage` 持久化，关闭页面后仍保留
- `input` 的 `value` 必须与 `pageSize` 保持同步

#### 3.6.2 表头宽度拖拽调整

为每个 `<th>` 元素右侧添加拖拽手柄，鼠标拖拽即可调整列宽：

```css
th{position:relative}
th .resizer{position:absolute;right:0;top:0;bottom:0;width:5px;cursor:col-resize;z-index:2}
th .resizer:hover{background:var(--primary-500);opacity:.5}
```

```javascript
function initColResize(){
  document.querySelectorAll('#theadInner th').forEach(function(th){
    if(th.querySelector('.resizer'))return;
    var div=document.createElement('div');
    div.className='resizer';
    th.appendChild(div);
    var startX=0,startW=0,resizing=0;
    div.addEventListener('mousedown',function(e){
      e.preventDefault();resizing=1;startX=e.clientX;startW=th.offsetWidth;
      document.body.style.cursor='col-resize';document.body.style.userSelect='none';
      document.addEventListener('mousemove',onMouseMove);
      document.addEventListener('mouseup',onMouseUp);
    });
    function onMouseMove(e){
      if(!resizing)return;
      var w=Math.max(40,startW+(e.clientX-startX));
      th.style.width=w+'px';th.style.maxWidth=w+'px';
      var colIdx=Array.from(th.parentNode.children).indexOf(th);
      document.querySelectorAll('#mainBody tr').forEach(function(tr){
        var td=tr.children[colIdx];if(td){td.style.width=w+'px';td.style.maxWidth=w+'px'}
      });
    }
    function onMouseUp(){
      resizing=0;document.body.style.cursor='';document.body.style.userSelect='';
      document.removeEventListener('mousemove',onMouseMove);
      document.removeEventListener('mouseup',onMouseUp);
    }
  });
}
```

**要点**：
- 每次 `rebuildHeader()` 后**必须**调用 `initColResize()`（因为表头被重新创建）
- `rebuildHeader()` 中需要保存并恢复已调整的列宽
- 最小宽度 40px，防止拖拽过头
- 拖拽时同步更新同列 tbody 中所有 td 的宽度
- 鼠标悬停时拖拽柄高亮显示

#### 3.6.3 表头固定（sticky header）

表格容器必须限制最大高度并启用垂直滚动，使表头在滚动表格内容时始终固定在顶部：

```css
.table-wrap{overflow:auto;max-height:calc(100vh - 280px)}
th{position:sticky;top:0;z-index:1}
```

**要点**：
- `max-height` 值根据页面布局调整，确保表格不超出页面底部
- `position:sticky` + `top:0` 让表头在容器内滚动时固定在顶部
- `z-index:1` 确保表头浮在内容之上
- 表头字段过多时通过齿轮面板折叠隐藏（见 3.6.4）

#### 3.6.4 列显隐面板（齿轮小工具）

当表格列数过多时，用小齿轮按钮折叠非核心列，避免页面拥挤：

```html
<span class="settings-wrap">
  <button class="settings-btn" id="settingsBtn" title="列设置">⚙</button>
  <div class="settings-pop" id="settingsPop"></div>
</span>
```

```css
.settings-wrap{position:relative;display:inline-block}
.settings-btn{width:28px;height:28px;border:1px solid var(--neutral-200);border-radius:var(--radius-control);background:#fff;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:15px;color:var(--neutral-600);line-height:1;vertical-align:middle}
.settings-btn:hover{border-color:var(--primary-500);color:var(--primary-500)}
.settings-pop{display:none;position:absolute;right:0;top:34px;background:#fff;border:1px solid var(--neutral-200);border-radius:var(--radius-card);box-shadow:0 4px 16px rgba(0,0,0,.12);padding:10px 14px;min-width:190px;z-index:20;font-size:13px}
.settings-pop.show{display:block}
.settings-pop label{display:flex;align-items:center;gap:7px;padding:5px 0;cursor:pointer;color:var(--neutral-600)}
.settings-pop label input[type=checkbox]{margin:0;width:15px;height:15px;cursor:pointer}
```

**要点**：
- 核心列默认显示，补充列（自定义字段等）默认隐藏
- 设置保存到 `localStorage`
- 列显隐变化时需重新 `rebuildHeader()` + `initColResize()` + `renderPage()`
- 切换审批模板时，自定义字段的齿轮选项随之联动刷新

---

## 四、元数据与缓存控制

### 必须添加的 meta 标签

```html
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**原因**：i人事 平台对插件 HTML 做双层缓存（浏览器 + 平台 CDN）。不加此标签的话，内容更新后需重新登录才能生效。加上后刷新浏览器即可看到变更。

### 修改文件后记得更新 `generatedAt`

第一条元数据注释中的时间戳帮助平台感知变更，建议每次修改后更新。

---

## 五、FaaS（后端 Python 插件）集成

### 什么时候需要后端 FaaS

| 需要后端 | 不需要后端 |
|---------|-----------|
| 调用 OpenAPI（需 Bearer token + AppSecret） | 调用 Gateway API（Cookie 即可） |
| 批量数据计算（大数据集） | 简单的本地计算（个税、司龄） |
| 访问 Gateway 未覆盖的接口 | 查询花名册、离职、年假等基础接口 |
| 多步骤级联操作 | 单次查询 + 前端展示 |

**典型必用 FaaS 场景**：流程台账文件导出
- 数据来源：`POST /openapi/thirdparty/api/workflow/v1/process/finish/page`
- 该接口**仅 OpenAPI 提供**，无 `web/gateway/` 代理通道
- 后端持有 AppID+AppSecret，在前端和后端 OpenAPI 之间充当安全代理
- 前端通过 `Api-Key` header 调用 FaaS → FaaS 用 OAuth 调 OpenAPI → 返回文件列表
- ⚠️ **如果不想用 FaaS**，也可以手动获取 Token 直接调 OpenAPI（见 `references/流程台账附件直链下载.md`）

**无需 FaaS 的反例（已验证）**：花名册试用期状态查询
- 原以为 `probationStatus` 仅 OpenAPI 有，设计了 FaaS 后端
- 实测 Gateway 搜索接口直接返回 `probationStatus` / `probationEndDate`
- 最终删除后端，纯前端实现

### 调用格式

```javascript
// 前端调用 FaaS
fetch("https://faasapi.ihr360.com/public/api/function/execute/v1/{functionId}/version/latest", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Api-Key": "{ApiKey}",           // 注意是 "Api-Key"，不是 "x-api-key" 或 "X-Api-Key"
  },
  credentials: "omit",               // 防止自动带 Cookie 导致 CORS 报错
  body: JSON.stringify({"input": {}}),  // 对应后端 handler 的 input 参数
});
```

- 后端返回格式：`{code: 0, data: <handler_return>}` — 需要解一层 `data` 包裹
- FaaS 调用是 `POST`，请求体必须是 `{"input": {...}}`
- `credentials: "omit"` **必须设置**，否则浏览器自动附带页面 Cookie 会导致 CORS 被拒

### 后端 Python 通用模板

```python
from ihr360tools.runtime import handler
from ihr360tools.logger import logger
from ihr360tools.api_caller import api_caller

@handler
async def handler(input: dict, context: dict) -> dict:
    # input: 调用方（前端）传入的参数
    # context: { companyId, functionName, relatedDataId }
    logger.info(f"开始执行: {context.get('functionName', 'unknown')}")
    # ... 业务逻辑 ...
    return {"success": True, "data": result}
```

### OpenAPI 鉴权（在后端中使用）

```python
import urllib.request, base64, json
from urllib.parse import urlencode

APP_ID = "xxx"
APP_SECRET = "xxx"
TOKEN_URL = "https://openapi.ihr360.com/openapi/oauth/token"
BASE_URL = "https://openapi.ihr360.com/openapi"

def _get_token():
    auth_str = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    body = urlencode({"grant_type": "client_credentials", "scope": "client"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        return data.get("access_token") or data["data"]["access_token"]
```

- OpenAPI 限速 **10 req/s**，后端需要自行控制并发
- 前端 Gateway 和 OpenAPI 路径**不互通**，混淆使用会导致 401

---

## 六、常见错误排查

| 错误现象 | 根因 | 修复 |
|---------|------|------|
| 按钮点击无响应 | `onclick="..."` 内联被沙盒屏蔽 | 改用 `addEventListener` |
| 页面白屏 / 所有按钮失效 | `document.getElementById()` 返回 `null` | 删除 DOM 元素后同步清理 JS 引用 |
| 401 Unauthorized | Gateway 路径 vs OpenAPI 路径混用 | 前端用 `/web/gateway/`，后端用 `/openapi/` |
| FaaS 调用 CORS 报错 | 未设置 `credentials: "omit"` | 添加此参数 |
| FaaS 返回 "Required request header 'Api-Key'" | 请求头名字错误 | 用 `Api-Key`（不是 `x-api-key` 或 `X-Api-Key`） |
| 查询返回空数据但无报错 | 使用了未验证的字段名，或字段在 Gateway 不存在 | 先小范围测试确认字段可用性 |
| 插件内容更新后不生效 | 浏览器 + CDN 双层缓存 | 加 Cache-Control meta 标签 + 更新 `generatedAt` |
| CSV 导出在 Excel 中乱码 | 缺少 UTF-8 BOM | 添加 `\uFEFF` 前缀 |
| 分页无限循环 | `totalPages` 判断错误 | 检查 `page >= totalPages` 条件 |
| FaaS 数据返回但前端无响应 | 未解 FaaS 数据包裹 | FaaS 返回 `{code:0, data:<result>}`，需要取出内层 `data` |
| 下载文件直接跳转页面 | `<a href>` 直接暴露文件 URL | 改用 `window.open(url, '_blank')` 或 iframe 预览

---

## 七、交付前检查清单

### 结构
- [ ] `ihr360-base-framework.js` 在 `<head>` 最先加载
- [ ] `ihr360-html-page-builder` 元数据注释存在且 `generatedAt` 已更新
- [ ] Cache-Control meta 标签已添加
- [ ] 禁用 `onclick=""`，全部使用 `addEventListener`
- [ ] 禁用 `alert()` / `confirm()` / `prompt()`
- [ ] CSS 和 JS 全部内联，无外部文件依赖
- [ ] 不依赖海外 CDN

### API 调用
- [ ] 使用统一封装的 `request()` 函数（不绕过封装直接调用 `fetch()`）
- [ ] `credentials: "include"` 已设置
- [ ] `x-xsrf-token` 从 Cookie 动态读取
- [ ] **Gateway 与 OpenAPI 路径未混用**（前 `/web/gateway/`，后 `/openapi/`）
- [ ] 分页使用 `async/await + while` 模式，有明确终止条件
- [ ] 使用 `fields` 数组精确控制返回字段（推荐）
- [ ] 查询字段只使用已验证的字段名（见 `api-field-mapping.md`）
- [ ] **编码字段已转换为可读格式**（时间戳→日期、枚举→中文标签、ID→名称等）
- [ ] 大数量场景有 loading 动画 + 进度条
- [ ] 若计划用 FaaS，确认该接口是否已有 Gateway 代理通道

### FaaS（仅当使用后端时）
- [ ] 请求头用 `Api-Key`（不是 `x-api-key` 或 `X-Api-Key`）
- [ ] `credentials: "omit"` 已设置（防止自动带 Cookie）
- [ ] 请求体格式为 `{"input": {...}}`
- [ ] 响应已解 FaaS 包裹层（`raw.data`）
- [ ] **流程台账附件提取时 `requireComments: true` 已设置**
- [ ] **文件名扩展名推断已覆盖（URL提取 → Content-Type映射 → 按类型默认）**
- [ ] **批量下载使用串行 `next(i+1)` 模式，非并行 fetch**

### UI
- [ ] 空态有明确提示
- [ ] 错误态有用户可见提示（不暴露原始错误）
- [ ] 统计卡片布局合理
- [ ] 表格在移动端支持横向滚动
- [ ] **CSV 导出使用 BOM（`\uFEFF`）**，否则 Excel 中文乱码
- [ ] `zhidayun-storage` 中的 `applicationName`/`applicationCode` 建议补全
- [ ] **有每页行数自定义（25/50/100/200）**，选择值持久化到 localStorage
- [ ] **表头支持拖拽调整列宽**，最小宽度 40px，rebuildHeader 后重新绑定
- [ ] 表头 sticky 固定（`.table-wrap{overflow:auto;max-height:...}`）
- [ ] **非核心列可折叠至小齿轮**（列显隐面板），列数≥8时必须配置

---

## 八、参考资料索引

| 用途 | 文件 |
|------|------|
| 流程台账附件直链下载（手动Token方案） | `references/流程台账附件直链下载.md` |
| 流程台账附件插件下载（FaaS批量方案） | `references/流程台账附件插件下载.md` |
| API 端点与字段定义（含109个接口概览） | `references/api-field-mapping.md` |
| CSS 设计变量与 UI 模式 | `references/design-tokens.md` |
| 页面模板（含完整结构，可复用） | `assets/template/index.html` |
| 已有插件参考 | 同级目录下的 `.html` / `.py` 文件 |
| 完整 109 接口参考手册 | `D:\WorkBuddy\逻辑演算\iHR360-API-参考手册.md` |
