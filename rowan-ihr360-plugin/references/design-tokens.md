# Design Tokens — CSS 变量与 UI 模式

Rowan 所有 iHR360 插件共享的设计系统。基于官方 `ihr360-html-page-builder` 的设计规范，经过实战验证。

---

## CSS 变量定义

```css
:root {
  /* ===== 主色调 ===== */
  --primary-50:  #e8f8f6;   /* 主色浅底（选中态、高亮背景） */
  --primary-400: #50cabc;   /* 渐变起点 */
  --primary-500: #15B8A6;   /* 主色（按钮、链接、强调） */
  --primary-700: #0d9488;   /* 主色深（hover 态） */

  /* ===== 中性色 ===== */
  --neutral-100: #f5f6f7;   /* 表头背景、hover 态 */
  --neutral-200: #eff0f2;   /* 边框、分隔线 */
  --neutral-500: #8e929b;   /* 辅助文字、占位符 */
  --neutral-600: #616670;   /* 正文文字 */
  --neutral-800: #262626;   /* 标题文字 */

  /* ===== 背景 ===== */
  --bg-page:     #f9fafb;   /* 页面背景 */
  --bg-card:     #ffffff;   /* 卡片背景 */

  /* ===== 圆角 ===== */
  --radius-control: 4px;    /* 按钮、输入框圆角 */
  --radius-card:    8px;    /* 卡片圆角 */

  /* ===== 阴影 ===== */
  --card-shadow: 1px 1px 4px 4px rgba(83,84,85,0.02);

  /* ===== 间距 ===== */
  --space-16: 16px;         /* 基础间距（卡片 padding） */

  /* ===== Shell 尺寸（非插件内使用，仅参考） ===== */
  --topbar-height: 48px;
  --menu-width: 220px;
  --menu-item-height: 40px;
  --titlebar-height: 32px;
}
```

---

## 字体栈

```css
font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
```

- 优先使用苹方（macOS）
- 回退微软雅黑（Windows）
- 不依赖海外 CDN 加载字体

---

## 文字规格

| 用途 | 字号 | 字重 | 颜色 | 行高 |
|------|------|------|------|------|
| 页面标题 | 16px | 600 | `--neutral-800` | 24px |
| 卡片标题 | 16px | 600 | `--neutral-800` | 24px |
| 正文 | 14px | 400 | `--neutral-600` | 22px |
| 辅助文字 | 12px | 400 | `--neutral-500` | 18px |
| 指标数值 | 24px | 600 | `--neutral-800` | 32px |

---

## 按钮规格

```css
.button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;                    /* 固定高度 */
  padding: 0 12px;
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-control);  /* 4px */
  background: #ffffff;
  color: var(--neutral-600);
  font-size: 14px;
  cursor: pointer;
}

.button-primary {
  border-color: var(--primary-500);
  background: var(--primary-500);
  color: #ffffff;
}

.button-primary:hover {
  background: var(--primary-700);
}

.button-secondary:hover {
  background: var(--neutral-100);
}
```

---

## 卡片模式

```css
.card {
  padding: var(--space-16);        /* 16px */
  border-radius: var(--radius-card); /* 8px */
  background: var(--bg-card);      /* #ffffff */
  box-shadow: var(--card-shadow);
}
```

**规则**：
- 每个业务模块必须包裹在白色卡片中
- 不要把表格、表单、操作区直接放在页面背景上
- 卡片之间使用 `gap: 16px` 分隔

---

## 统计指标卡片

```css
.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-16);
}

.metric {
  padding: var(--space-16);
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-card);
  background: #ffffff;
}

.metric-label {
  color: var(--neutral-500);
  font-size: 12px;
}

.metric-value {
  margin-top: 8px;
  color: var(--neutral-800);
  font-size: 24px;
  font-weight: 600;
}
```

---

## 表格模式

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  padding: 10px 12px;
  background: var(--neutral-100);
  color: var(--neutral-600);
  font-weight: 500;
  text-align: left;
  border-bottom: 1px solid var(--neutral-200);
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--neutral-200);
  color: var(--neutral-600);
}

.data-table tr:hover td {
  background: var(--neutral-100);
}
```

---

## 空态模式

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px var(--space-16);
  color: var(--neutral-500);
  font-size: 14px;
}
```

---

## Loading 动画

大数量场景：弹跳猫咪 GIF + 进度条

```html
<div class="loading-container">
  <img src="https://plugin.ihr360.com/system/dancingkitty.gif"
       alt="加载中" class="loading-gif" />
  <div class="progress-bar">
    <div class="progress-fill" id="progressFill"></div>
  </div>
  <div class="loading-text" id="loadingText">正在加载... 1/10 页</div>
</div>
```

---

## 响应式

```css
@media (max-width: 768px) {
  .metrics {
    grid-template-columns: 1fr;
  }

  .page-head {
    flex-direction: column;
  }

  .data-table {
    display: block;
    overflow-x: auto;
  }
}
```
