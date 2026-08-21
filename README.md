# iHR360 插件集合（iHR-plugin）

i人事（iHR360）HR SaaS 平台的自定义插件集合。所有插件遵循统一架构：

```
前端 HTML（JS 放 head）→ FaaS API → 后端 Python → iHR360 OpenAPI
```

## 插件清单

| 插件 | 类型 | 功能 | 部署 |
|------|------|------|------|
| [公式格式化工具](./公式格式化工具/) | 纯前端 | iHR360 公式解析/格式化/语法高亮/逻辑树（tokenizer+parser+renderer 全引擎） | 直接上传 HTML |
| [司龄计算](./司龄计算/) | 纯前端 | 员工司龄/工龄计算 | 直接上传 HTML |
| [年终奖个税计算器](./年终奖个税计算器/) | 纯前端 | 年终奖个税计算 | 直接上传 HTML |
| [未维护头像员工查询](./未维护头像员工查询/) | 纯前端 | 查询未设置头像的员工列表 | 直接上传 HTML |
| [花名册试用期状态查询](./花名册试用期状态查询/) | 纯前端 | 按试用期状态筛选花名册 | 直接上传 HTML |
| [流程台账文件导出](./流程台账文件导出/) | **前后端** | 流程台账列表 + 附件批量导出（多选/zip 打包/CSV/6 维筛选/动态自定义字段） | HTML 上传 + backend.py 部署 FaaS |
| [直属上级筛选](./直属上级筛选/) | **前后端** | 按直属上级/汇报链筛选员工 | HTML 上传 + backend.py 部署 FaaS |
| [rowan-ihr360-plugin](./rowan-ihr360-plugin/) | 插件开发 Skill | 页面生成型 skill：插件开发框架/API 模式/design-tokens/调试清单 | 导入宿主 AI |

## 使用前提（OAuth 凭证）

前后端插件（backend.py）需要客户开放平台凭证，通过环境变量注入（**不硬编码**）：

```bash
# 客户开放平台（open.ihr360.com 应用管理）获取 AppID/AppSecret
export IHR360_APP_ID="your-app-id"
export IHR360_APP_SECRET="your-app-secret"
```

- 鉴权链路：OAuth client_credentials → Bearer token → OpenAPI 全量接口
- OpenAPI 网关：`openapi.ihr360.com`（限速 10req/s，路径前缀 `/openapi/`）
- 纯前端插件受 CORS 限制，需走 FaaS 后端代理

## 插件开发规范

- 统一 UI 规范（design-tokens）：见 `rowan-ihr360-plugin/references/design-tokens.md`
- 分页必须含 200 行选择器（25/50/100/200）、列宽拖拽、列显隐齿轮、CSV(BOM)、6 维筛选
- 零外部依赖（不引用 CDN/沙盒），自包含单文件
- 输出 ID 一律转可读名称（staffId→姓名、枚举→中文），不暴露机器标识

## 隐私说明

- 插件不含任何真实企业数据/凭证（测试凭证已脱敏为环境变量占位）
- 员工姓名等 PII 均为演示占位，实际使用以客户环境实时查询为准
