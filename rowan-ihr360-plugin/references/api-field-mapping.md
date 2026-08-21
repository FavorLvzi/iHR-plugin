# API 字段映射与端点参考

> 来源：open.ihr360.com 官方文档 + 109 个接口系统归档  
> 完整参考手册：`D:\WorkBuddy\逻辑演算\iHR360-API-参考手册\`（含每接口独立 .md 文件）  
> 更新日期：2026-06-18

---

## 鉴权方案选择

| 方案 | 鉴权方式 | 调用方 | 适用路径 | 限速 |
|------|---------|--------|---------|------|
| Gateway | Cookie + XSRF-TOKEN | **前端 HTML 插件**（浏览器自动携带） | `/web/gateway/...` | 已豁免 |
| OpenAPI | OAuth Bearer token | 后端 Python 插件 / 独立客户端 | `/openapi/...` | 10 req/s |
| FaaS 调用 | Api-Key header | 前端直调后端 Python 插件 | `faasapi.ihr360.com` | 无 |

**⚠️ 前端 Gateway 和 OpenAPI 路径不互通，混淆使用会导致 401。**

---

## 前端 Gateway API（Cookie + XSRF）

### 花名册员工搜索

```
POST /web/gateway/roster/aggregate/v1/staffs/search
```

**请求体**：
```json
{
  "fields": ["staffName", "departmentName", "probationStatus", ...],
  "page": 1,
  "pageSize": 100,
  "flexSearchItems": [
    {"fieldType": "EQUAL", "searchKey": "staffStatus", "searchParam": "IN_SERVICE"}
  ]
}
```

**已验证可用的查询/返回字段**：

| 字段 | 类型 | 说明 | 验证状态 |
|------|------|------|----------|
| `staffName` | String | 员工姓名 | ✅ |
| `mobileNo` | String | 手机号 | ✅ |
| `staffImageId` | String | 头像ID（空=未上传） | ✅ |
| `departmentName` | String | 部门名称 | ✅ |
| `staffStatus` | String | IN_SERVICE / LEAVE | ✅ |
| `enrollInDate` | String | 入职日期 | ✅ |
| `probationStatus` | String | PASSED(已转正) / ONPROBATION(试用期) | ✅ |
| `probationEndDate` | String | 试用期结束日 | ✅ |
| `probationLength` | Integer | 试用期月数 | ✅ |
| `isProbation` | Boolean | 是否试用期 | ✅ |
| `positiveDate` | String | 转正日期 | ✅ |
| `lastWorkDay` | String | 最后工作日 | ✅ |
| `staffNo` | String | 工号 | ✅ |
| `positionName` | String | 职位名称 | ✅ |
| `staffType` | String | 员工类型 | ✅ |

`lastWorkDay` 和 `confirmQuitDate` 在花名册搜索接口的可用性**已验证**（`lastWorkDay` 可用于司龄计算），但 `confirmQuitDate` 仍**未验证**，避免使用。

### 其他 Gateway 端点

| 接口 | 端点 | 用途 |
|------|------|------|
| 员工花名册详情 | `POST /gateway/hr/core/api/employee/detail/list` | 批量员工详情 |
| 离职清单 | `POST /gateway/hr/core/api/dimission/list` | 离职员工列表 |
| 年假报表 | `POST /gateway/attendance/leave/api/annual/report/summary` | 年假汇总 |

---

## OpenAPI 模块概览（109 个接口）

### 01 — 组织架构（17 个接口，#9~#25）

| 子模块 | 接口 | 核心路径 |
|--------|------|----------|
| 部门 | #9~#14 | `org/v1/organizations/` — 搜索/创建/更新/详情/负责人/元数据 |
| 职位 | #15~#18 | `org/v1/organizations/positions/` — 搜索/部门下/按ID/职级 |
| 职务·职级·体系表 | #19~#21 | 均为 GET 无参：`jobTitles` / `positiongrades` / `gradesystem/all` |
| 法律实体·工作地点·职务分类 | #22~#24 | `corporations` / `companysites` / `jobCategory/get` |
| 多维组织 | #25 | `dimensionOrganization/v1/dimension/organizations` |

### 02 — 员工管理（27 个接口，#1~#4, #26~#52）

| 子模块 | 接口 | 说明 |
|--------|------|------|
| 基础信息 | #1~#3, #26, #27 | ID清单/详情/领导/删除员工/复职 |
| 合同 | #4, #35 | 合同清单/当前合同 |
| 信息子集 | #28~#37 | 任职/教育/工作/证照/银行卡/上级/兼任/自定义子集/元数据 |
| 入职 | #38~#40 | 字段定义/待入职清单/详情 |
| 转正 | #41~#43 | 按日期查/v2当天/按ID批量 |
| 调动 | #44~#46 | 待调动/时间段/设置 |
| 离职 | #47~#49 | 待离职/当日/时间段 |
| 绩效档案 | #50 | 绩效档案查询 |
| 家庭成员 | #51 | 家庭成员查询 |
| 多维组织任职 | #52 | 多维组织任职记录 |

### 03 — Gateway 接口（4 个接口，#5~#8）

即花名册搜索、员工详情批量、离职清单、年假报表，供前后端双端参考。

### 05 — 薪资管理（19 个接口，#53~#71）

| 分类 | 接口 | 说明 |
|------|------|------|
| 考勤导入 | #53, #54 | 考勤数据导入 + 动态表头查询 |
| 薪资方案 | #55, #56 | 方案列表（GET）+ 方案详情（POST） |
| 薪资核算 | #57, #58 | 核算中数据V2 + 审批文件地址 |
| 薪资调整 | #59 (PUT), #60 | 更新薪资档案 + 调整记录查询 |
| 个税 | #61, #62 | 个税扣缴义务人（GET 单员工 / POST 批量） |
| 结果定义 | #63 (GET), #64 (GET) | 年月定义列表 + 详情 |
| 月度结果 | #65~#67 | 按部门/手机号/员工ID查薪资明细 |
| 薪资项目 | #68~#71 | 系统项目/员工月度结果/档案项目/公司项目 |

**#59 是 109 个接口中唯一的 PUT 方法接口。**

### 06 — 福利管理（5 个接口，#72~#76）

| 接口 | 说明 |
|------|------|
| #72 社保缴纳方案集合 | GET，查社保/公积金/其他福利方案列表 |
| #73 社保基数字段 | GET，`payBaseHeaders/query/SI` |
| #74 公积金基数字段 | GET，`payBaseHeaders/query/HF` |
| #75 其他福利基数字段 | GET，`payBaseHeaders/query/OTHER` |
| #76 社保台账结果 | POST，按年月+员工查已存档台账明细 |

\#73~#75 三个基数字段接口结构完全相同，仅路径后缀不同（SI/HF/OTHER）。

### 07 — 考勤管理（26 个接口，#77~#102，字段最丰富的模块）

| 分类 | 接口 | 核心路径 |
|------|------|----------|
| 假期 | #77~#82 | 休假单 / 假期类型v1&v2 / 假期余额 / 法定节假日 / 年假余额 |
| 加班 | #83~#86 | 加班单v2 / 加班设置 / 时长试算 / 按结转日期查 |
| 外出 | #87 | 外出单V2 |
| 出差 | #88 | 出差单V2 |
| 补卡 | #89, #90 | 补卡原因 / 补卡单 |
| 打卡记录 | #91 | 打卡记录（20种来源） |
| 排班 | #92 | 排班V4（≤100人，非分页） |
| 日月报 | #93, #94 | 日报V4（40+字段） / 月报V3（50+字段） |
| 考勤周期 | #95~#102 | 周期设置 / 员工归属 / 实例 / 自定义字段 / 出勤班次 |

**日报V4 (#93) vs 月报V3 (#94) 对比**：
- 日报：按天，含签到班段详情（signBlockList），40+字段
- 月报：按月，双维度（天+时），加班拆分为转调休/转薪资，50+字段

**考勤周期三层查询链路**：#95 周期模板 → #97/#98 员工归属 → #99 周期实例

### 08 — 审批相关（7 个接口，#103~#109）

| 分类 | 接口 | 说明 |
|------|------|------|
| OA回调 | #103, #104 | GET/POST 第三方选项数据（URL由运营配置） |
| 待办查询 | #105 | 根据流程id+审批人id查待办链接 |
| 已完结查询 | #106 | 多维筛选已完结单据（page=1起始，支持跨年source） |
| 状态修改 | #107 | 修改三方推送流程状态（仅PASS/DENIED） |
| 表单更新 | #108 | 按标记码更新表单数据（需JWT dataToken，联系实施经理申请） |
| 执行审批 | #109 | 模拟审批：APPROVE/REJECT/BACK |

**#106 是最复杂的审批接口**：37种modelShowType + 5种statuses + 57种suiteType枚举，分页 page=1 起始。

---

## OpenAPI 认证与员工端点

### 认证

```text
POST https://openapi.ihr360.com/openapi/oauth/token?grant_type=client_credentials
Authorization: Basic base64(AppID:AppSecret)
```

返回 `access_token`，后续请求携带 `Authorization: Bearer {token}`。

### 员工基础端点

| # | 接口 | 方法 | 路径 | 用途 |
|---|------|------|------|------|
| 1 | 员工ID清单 | GET | `/openapi/thirdparty/api/staff/v1/staffs/ids?staffStatus=IN_SERVICE&pageNo=N` | 分页获取全部员工ID |
| 2 | 员工详情 | GET | `/openapi/thirdparty/api/staff/v1/staffs/{staffId}/detail` | 单员工完整信息 |
| 3 | 员工详情（含领导） | GET | `/openapi/thirdparty/api/staff/v1/staffs/{staffId}/superiors/detail` | 同上 + 直属领导 |
| 4 | 合同清单 | POST | `/openapi/thirdparty/api/staff/v1/contracts` | 批量查合同（≤100人/批） |

### OpenAPI 特有字段（Gateway 不保证返回）

- `idCardNo`（身份证号）
- `contractType`, `contractBeginDate`, `contractEndDate`
- `birthday`, `sex`, `age`
- `quitReason`, `quitReasonType`, `quitType`

---

## 员工信息字段总览

| 含义 | 字段名 | Gateway 搜索 | OpenAPI 详情 | 备注 |
|------|--------|:-----------:|:-----------:|------|
| 姓名 | `staffName` | ✅ | ✅ | |
| 工号 | `staffNo` | ✅ | ✅ | |
| 手机号 | `mobileNo` | ✅ | ✅ | |
| 部门 | `departmentName` | ✅ | ✅ | |
| 部门全路径 | `fullDepartmentName` | ❌ | ✅ | |
| 职位 | `positionName` | ✅ | ✅ | |
| 员工类型 | `staffType` | ✅ | ✅ | FULLTIME/PARTTIME 等 |
| 入职日期 | `enrollInDate` | ✅ | ✅ | |
| 员工状态 | `staffStatus` | ✅ | ✅ | IN_SERVICE/QUIT |
| 头像ID | `staffImageId` | ✅ | ✅ | 空=未上传 |
| 试用期状态 | `probationStatus` | ✅ | ✅ | PASSED/ONPROBATION |
| 试用期结束日 | `probationEndDate` | ✅ | ✅ | |
| 转正日期 | `positiveDate` | ✅ | ✅ | |
| 最后工作日 | `lastWorkDay` | ✅ | ✅ | 离职花名册中可用 |
| 离职日期 | `confirmQuitDate` | ❌（待验证） | ✅ | 不要用于司龄计算 |
| 身份证号 | `idCardNo` | ❌ | ✅ | 仅 OpenAPI |
| 合同信息 | 合同相关字段 | ❌ | ✅ | 仅 OpenAPI |

---

## 枚举值速查

### 员工模块

| 字段 | 值 | 含义 |
|------|----|------|
| `staffStatus` | `IN_SERVICE` / `QUIT` | 在职 / 离职 |
| `probationStatus` | `PASSED` / `ONPROBATION` | 已转正 / 试用期 |
| `staffType` | `FULLTIME` / `PARTTIME` / `INTERSHIP` / `EXPATRIATE` / `TEMPORARY` / `REHIRE_RETIREMENT` | 全职 / 兼职 / 实习 / 外派 / 临时工 / 退休返聘 |
| `contractType` | `LABOR_CONTRACT` / `SERVICE_CONTRACT` / `TRAINING_CONTRACT` / `NO_LIMIT_CONTRACT` / `OTHER_CONTRACT` | 劳动合同 / 劳务合同 / 实习合同 / 无固定期限 / 其他 |

### 考勤模块

| 字段 | 值 | 含义 |
|------|----|------|
| 打卡来源 `source` | `MACHINE` / `NORMAL` / `APPEAL` / `TEAM_SIGN` / `OUT_SIGN` / `HR_OPERATION` / `HR_JUDGE` / `OLD_RECORD` / `OVERTIME` / `HR_APPEAL` / `HR_APPEAL_IMPORT` / `APP` / `WECHAT` / `DINGDING` / `OPEN_API` / `FEISHU` / `FANWEI` / `YUNZHIJIA` / `CIMOS` / `WPSOA` | 20种打卡来源（实际由 source + sourceDescription 双层描述） |
| `signType` (日报) | `正常` / `异常` | 出勤状态 |
| 考勤周期月份 | `THIS_MONTH` / `LAST_MONTH` / `NEXT_MONTH` | 周期开始/结束月份 |
| `periodEndDay` | `END_OF_MONTH` | 周期结束为月底（特殊值） |
| 自定义字段 `valueType` | `NUMBER` / `TEXT` | 数值型 / 文本型 |
| 自定义字段 `roundingMode` (8种) | `ROUND_UP` / `ROUND_DOWN` / `AN_INTEGER` / `CARRY_INTEGER` / `ROUND_KEEP_TWO` / `DISCARD_KEEP_TWO` / `ROUND` / `CARRY_DECIMALS` | 圆整方式 |
| 自定义字段 `numberSetting` (3种) | `GREATER_OR_EQUAL` / `LESS_OR_EQUAL` / `BETWEEN` | 数字验证设置 |
| 加班补偿类型 | `TRANSFER_TO_REST` / `TRANSFER_TO_SALARY` | 转调休 / 转薪资 |

### 审批模块

| 字段 | 值 | 含义 |
|------|----|------|
| 流程状态 `status` (5种) | `PASS` / `DENIED` / `ABANDONED` / `WITHDRAW_DENIED` / `WITHDRAW` | 已通过/已驳回/已作废/已通过(撤回被驳回)/已撤销 |
| 审批执行类型 (3种) | `APPROVE` / `REJECT` / `BACK` | 同意 / 驳回 / 退回（暂仅支持退回发起人） |

#### modelShowType（37 种审批类型）

| 模块 | 类型码（17种考勤 + 7种薪资福利 + 7种组织人事 + 6种招聘 + 1种自定义） |
|------|--------|
| **考勤(17)** | `FIELD_WORK` 外出, `MELT_FIELD_WORK` 销外出, `APPEAL` 补卡, `OUT_SIGN` 外勤打卡, `EVECTION` 出差, `MELT_EVECTION` 销出差, `OVER_TIME` 加班, `COMBINATION_OVERTIME` 组合加班, `SHIFT_ADJUSTMENT` 调班, `LEAVE_ADJUST` 请假-调休, `LEAVE_ADJUST_GROUP` 组合请假-调休, `SECONDMENT` 借调, `VACATION` 休假大类, `MELT_VACATION` 销假, `ATT_ADD_POSITION` 新增岗位, `ATT_CHANGE_POSITION` 变更岗位, `ATT_REQUIREMENT_CHANGE` 需求变更 |
| **薪资福利(7)** | `PAYROLL`, `BENEFIT`, `PAYROLL_CANCEL`, `BENEFIT_CANCEL`, `SINGLE_SALARY_ADJUST`, `BATCH_SALARY_ADJUST`, `ADJUST_REGULAR_SALARY` |
| **组织人事(7)** | `ENTRANCE`, `QUIT`, `POSITIVE`, `TRANSFER`, `RENEW_CONTRACT_APPROVAL`, `BLACKLIST`, `HEADCOUNT_APPROVE` |
| **招聘(6)** | `RECRUIT_SINGLE`, `RECRUIT_BATCH`, `OFFER_APPROVE`, `BATCH_OFFER_APPROVE`, `IVVA_RECRUIT_SINGLE`, `IVVA_OFFER_APPROVE` |
| **自定义(1)** | `USER_CUSTOMIZATION` |

#### suiteType（57 种审批单据套件类型）

| 模块 | 类型码 |
|------|--------|
| **考勤假期(31)** | `FIELD_WORK`, `MELT_FIELD_WORK`, `APPEAL`, `OUT_SIGN`, `EVECTION`, `MELT_EVECTION`, `OVER_TIME`, `COMBINATION_OVERTIME`, `SHIFT_ADJUSTMENT`, `LEAVE_ADJUST`, `LEAVE_ADJUST_GROUP`, `SECONDMENT`, `MELT_VACATION`, `ATT_ADD_POSITION`, `ATT_CHANGE_POSITION`, `ATT_REQUIREMENT_CHANGE`, `AFFAIR_LEAVE` 事假, `ANNUAL_LEAVE` 年假, `SICK_LEAVE` 病假, `MARITAL_LEAVE` 婚假, `MATERNITY_LEAVE` 产假, `HOME_LEAVE` 探亲假, `PRENATAL_CHECK_UP` 产检假, `PATERNITY_LEAVE` 陪产假, `LACTATION_LEAVE` 哺乳假, `ADJUST_REST` 调休, `FUNERAL_LEAVE` 丧假, `OTHER_VACATION` 其他假期, `USER_DEFINED_VACATION` 自定义假期, `PARENTAL_LEAVE` 育儿假, `SABBATICAL_LEAVE` 公休 |
| **薪资福利(7)** | 同上 modelShowType 的 7 种 |
| **组织人事(7)** | 同上 modelShowType 的 7 种 |
| **招聘(6)** | 同上 modelShowType 的 6 种 |

### OA 回调

| 字段 | 值 | 含义 |
|------|----|------|
| 回调响应 `code` | 0 / -1 / -2 | OK / INFO / ERROR |

---

## API 接口模式总结

### 分页规范

| 模式 | 举例 | 说明 |
|------|------|------|
| **page=0 起始**（多数） | #5 Gateway, #77~#101 考勤, #106 以外审批 | 分页从0开始，page=0为第一页 |
| **page=1 起始** | #106 审批已完结单据 | 分页从1开始 |
| **无分页（GET返回数组）** | #14, #19~#21, #23~#24, #73~#75, #78, #79, #81, #84, #89, #92, #95, #96, #102 | 一次性返回全部数据 |
| **非分页平铺数组** | #92 排班V4, #89 补卡原因, #100 日报自定义字段值 | data 为平铺数组（无 totalPages） |

### 请求体格式

| 格式 | 接口 | 示例 |
|------|------|------|
| JSON 对象 `{}` | 大多数 POST 接口 | `{"staffIds": [...], "periodSettingId": "..."} ` |
| JSON 数组 `[]` | #97, #98, #99（考勤周期三接口） | `["uuid1", "uuid2"]` 直接传 UUID 列表 |
| GET + Query | #1, #39, #44, #47 等员工查询 | `?staffStatus=IN_SERVICE&pageNo=1` |
| GET + Path | #2, #40 | `/{staffId}/detail`, `/{entryFormId}/entryInfo` |
| GET + Query + Path | #52 | `/{staffId}?dimensionOrganizationId=xxx` |
| OA回调 | #103, #104 | URL由第三方运营配置 |

### 鉴权特例

| 模式 | 接口 |
|------|------|
| 标准 Bearer Token | 大多数 OpenAPI |
| **Bearer + JWT 双鉴权** | **#108 根据标记码变更流程实例数据**（需联系实施经理申请 SecretKey） |
| OA 回调 | #103, #104（无 Bearer，URL 由运营配置） |

### 方法分布

| 方法 | 数量 | 说明 |
|------|------|------|
| POST | ~68+ | 绝对多数 |
| GET | ~38 | 无参或多用于简单查询 |
| PUT | **1** | #59 员工薪资调整（唯一 PUT） |

---

## 架构决策参考

| 需求 | 推荐方案 | 不推荐 |
|------|---------|--------|
| 基础花名册查询 | Gateway 搜索接口（纯前端 Cookie） | OpenAPI（需 FaaS 中转） |
| 需要试用期字段 | Gateway 搜索接口（已验证可用） | 不需要走 OpenAPI |
| 需要身份证号、合同信息 | OpenAPI（需后端 FaaS 中转） | Gateway（不返回这些字段） |
| 批量员工详情 | Gateway 详情接口 或 OpenAPI 并发拉取 | 逐个串行调 |
| 查考勤日报/月报 | OpenAPI `tm/v4/daily/reports` / `tm/v3/period/monthly/reports` | Gateway 不提供 |
| 查已完结审批单据 | OpenAPI `workflow/v1/process/finish/page` | Gateway 不提供 |
| 修改审批状态 | OpenAPI `workflow/update/process/status`（仅三方推送流程） | Gateway 不提供 |
| 更新审批表单数据 | OpenAPI `workflow/v1/form/update/instance`（需 JWT） | 无替代方案 |
