# 三个页面功能增强 — 设计文档

**日期:** 2026-06-24
**范围:** 业务管理、团队管理、流程制度 三个模块的功能增强

---

## 1. 业务管理 — 负责人下拉限制

### 现状
`templates/business/form.html:36` 负责人字段为 `<input type="text">`，用户可任意输入。

### 目标
负责人只能从团队管理已录入的 `Member` 中选择，确保数据一致性。

### 设计

**路由层** (`blueprints/business/routes.py`):
- `new_tech_point` (GET): 传入 `members = Member.query.order_by(Member.name).all()` 到模板
- `edit_tech_point` (GET): 同上
- 两个 POST 处理器保持不变（`request.form.get("owner", "")` 接收 `<select>` 的 value）

**模板层** (`templates/business/form.html`):
- 将第 36 行的 `<input type="text" name="owner">` 替换为:
```html
<select name="owner" class="form-select">
    <option value="">-- 请选择负责人 --</option>
    {% for m in members %}
    <option value="{{ m.name }}" {% if point and point.owner == m.name %}selected{% endif %}>{{ m.name }}</option>
    {% endfor %}
</select>
```

**数据流:**
```
Member.query.all() → 路由 → 模板 <select> → POST form["owner"] → TechPoint.owner
```

### 验证方式
- 测试：新建/编辑技术点时，验证下拉列表只包含 Member 表中存在的姓名
- 测试：提交表单时验证 owner 值正确保存

---

## 2. 团队管理 — 成员详情模态框

### 现状
`templates/team/list.html` 成员卡片只显示摘要信息（姓名、评级、组别、技能标签），点击跳转到雷达图页面或编辑页。

### 目标
点击成员卡片后，在当前页面弹出模态框展示该成员的全部字段信息。

### 设计

**数据传递方式:** 使用 `data-*` 属性内嵌在卡片上，避免额外 AJAX 请求。

**模板层** (`templates/team/list.html`):
- 在每张 `.member-card` 上添加 `data-member-*` 属性，存储完整字段
- 添加 `onclick` 触发模态框显示
- 在页面底部添加模态框 HTML 结构（遮罩 + 弹窗）

模态框展示字段:
| 字段 | 来源 |
|------|------|
| 姓名 | `m.name` |
| 头像字母 | `m.name[0]` |
| 工号 | `m.employee_id` |
| 职级 | `m.rank` |
| 组别 | `m.group` |
| 职称 | `m.title` |
| 评级 | `m.level` |
| 技能 | `m.skills` |
| 负责方向 | `m.responsible_for` |
| 入职日期 | `m.joined_at` |
| 能力评分 | `m.capability_scores` (各维度 + 分值) |

**CSS** (`static/style.css`):
- 新增 `.modal-overlay` — 全屏半透明遮罩，z-index 200
- 新增 `.modal-dialog` — 居中弹窗，max-width 480px，白色背景 + 圆角 + 阴影
- 新增 `.modal-header` / `.modal-body` / `.modal-close` 样式
- 新增 `.modal-detail-row` — 详情行（标签 + 值）
- 新增 `.modal-scores` — 能力评分列表

**JS** (内嵌在 `{% block scripts %}`):
- `openMemberModal(el)` — 从 `el.dataset` 读取所有字段，填充模态框内容，显示
- `closeMemberModal()` — 隐藏模态框
- 点击遮罩层也可关闭

### 验证方式
- 测试：验证列表中每张卡片都包含完整的 `data-member-*` 属性
- 测试：验证模态框 HTML 结构存在于页面中
- 手动：点击卡片 → 模态框弹出 → 信息完整 → 关闭

---

## 3. 流程制度 — 搜索栏自动刷新（AJAX）

### 现状
`templates/process/issue_list.html:17-27` 用户选择分类/状态后需点击"筛选"按钮提交表单。

### 目标
选择 `<select>` 后自动触发 AJAX 请求，无刷新更新表格区域。

### 设计

**路由层** (`blueprints/process/routes.py`):
- 修改 `list_issues`: 当请求头包含 `X-Requested-With: XMLHttpRequest` 时，只渲染表格片段 HTML 并返回，不返回完整页面
- 新增辅助函数 `_render_issue_table(issues)` 提取表格渲染逻辑，避免重复

**模板层** (`templates/process/issue_list.html`):
- 将 `<table class="data-table">` 包裹在 `<div id="issue-table-container">` 中，方便 JS 替换
- 将 `<button>筛选</button>` 移除（或隐藏，作为无 JS 降级保留）
- 在 `{% block scripts %}` 中添加 JS:
  - 监听 `select[name="category"]` 和 `select[name="status"]` 的 `change` 事件
  - 构建 URLSearchParams，fetch `/process/issues?category=...&status=...`
  - 请求头设置 `X-Requested-With: XMLHttpRequest`
  - 成功后替换 `#issue-table-container` 的 innerHTML

**降级策略:** 保留筛选按钮（CSS 隐藏），无 JS 环境下仍可通过按钮筛选。

### 验证方式
- 测试：AJAX 请求返回的响应不包含完整 HTML 结构（不含 `<html>`、`<head>`、侧边栏），只含表格片段
- 测试：响应中包含筛选后的数据
- 手动：选择下拉 → 表格自动刷新 → 数据正确

---

## 4. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `blueprints/business/routes.py` | 修改 | `new_tech_point` GET / `edit_tech_point` GET 传入 members |
| `templates/business/form.html` | 修改 | 负责人字段改为 `<select>` |
| `templates/team/list.html` | 修改 | 添加 data-* 属性 + 模态框 HTML + JS |
| `static/style.css` | 追加 | 模态框相关样式 |
| `blueprints/process/routes.py` | 修改 | AJAX 请求返回表格片段 |
| `templates/process/issue_list.html` | 修改 | 表格容器 + JS 自动筛选逻辑 |
| `tests/test_business.py` | 追加 | 三个需求的测试用例 |

---

## 5. 自检

- [x] 无占位符/TODO
- [x] 内部一致：三个需求独立，无交叉依赖
- [x] 范围可单次实现
- [x] 无模糊性：每个字段、CSS 类名、JS 函数名已明确
