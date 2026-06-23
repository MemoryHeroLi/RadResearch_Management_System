# 三个页面功能增强 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现三个独立功能增强 — 业务管理负责人下拉限制、团队管理成员详情模态框、流程制度搜索栏 AJAX 自动刷新

**架构：** 三个需求互不依赖，可独立实现。需求1修改路由+模板，需求2修改模板+CSS+JS，需求3修改路由+模板+JS。全部在后端使用 Flask/Jinja2，前端使用原生 JS，无额外依赖。

**技术栈：** Flask 2.3.3 + Jinja2 + 原生 JavaScript + Chart.js 4.4.0（已引入）

---

### 任务 1：业务管理 — 负责人字段改为 Member 下拉选择

**文件：**
- 修改：`blueprints/business/routes.py:38-64`（new_tech_point）和 `blueprints/business/routes.py:104-117`（edit_tech_point）
- 修改：`templates/business/form.html:34-37`（负责人字段）
- 修改：`tests/test_business.py`（追加测试）

- [ ] **步骤 1：编写失败测试 — 新建表单包含 members 下拉**

```python
def test_new_tech_point_form_has_member_select(client, db):
    """新建技术点表单的负责人字段应显示 Member 表中的成员"""
    from models import Member
    db.session.add(Member(name="张三", group="放射图像研究组"))
    db.session.add(Member(name="李四", group="放射系统功能组"))
    db.session.commit()

    resp = client.get("/business/new")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 应包含 <select name="owner">
    assert 'name="owner"' in html
    assert '<select' in html
    # 应包含两位成员
    assert "张三" in html
    assert "李四" in html
    # 不应是 input
    assert '<input type="text" name="owner"' not in html


def test_edit_tech_point_form_has_member_select(client, db):
    """编辑技术点表单的负责人字段应显示已选中的负责人"""
    from models import TechPoint, Member
    db.session.add(Member(name="王五", group="放射智能定量组"))
    db.session.commit()
    tp = TechPoint(name="测试技术点", direction="放射图像研究", owner="王五")
    db.session.add(tp)
    db.session.commit()

    resp = client.get(f"/business/{tp.id}/edit")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 应包含 select + 选中王五
    assert 'name="owner"' in html
    assert "王五" in html
```

- [ ] **步骤 2：运行测试验证失败**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_new_tech_point_form_has_member_select tests/test_business.py::test_edit_tech_point_form_has_member_select -v
```
预期：FAIL，因为模板尚未修改

- [ ] **步骤 3：修改路由 — 传入 members 到模板**

修改 `blueprints/business/routes.py`，在两个 GET 处理器中查询 Member 并传入模板。

在文件顶部 import 区域，`from models import TechPoint, StageProgress` 改为：

```python
from models import TechPoint, StageProgress, Member
```

`new_tech_point` GET 分支（第 64 行）改为：

```python
    members = Member.query.order_by(Member.name).all()
    return render_template("business/form.html", point=None, stages=STANDARD_PROCESS, directions=DIRECTIONS, members=members)
```

`edit_tech_point` GET 分支（第 117 行）改为：

```python
    members = Member.query.order_by(Member.name).all()
    return render_template("business/form.html", point=tp, stages=STANDARD_PROCESS, directions=DIRECTIONS, members=members)
```

- [ ] **步骤 4：修改模板 — 替换 input 为 select**

修改 `templates/business/form.html`，将第 34-37 行：

```html
    <div class="form-group">
        <label class="form-label">负责人</label>
        <input type="text" name="owner" class="form-input" value="{{ point.owner if point else '' }}">
    </div>
```

替换为：

```html
    <div class="form-group">
        <label class="form-label">负责人</label>
        <select name="owner" class="form-select">
            <option value="">-- 请选择负责人 --</option>
            {% for m in members %}
            <option value="{{ m.name }}" {% if point and point.owner == m.name %}selected{% endif %}>{{ m.name }}</option>
            {% endfor %}
        </select>
    </div>
```

- [ ] **步骤 5：运行测试验证通过**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_new_tech_point_form_has_member_select tests/test_business.py::test_edit_tech_point_form_has_member_select -v
```
预期：2 PASS

- [ ] **步骤 6：运行全部已有测试确保无回归**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v
```
预期：全部 PASS

- [ ] **步骤 7：Commit**

```bash
git add blueprints/business/routes.py templates/business/form.html tests/test_business.py
git commit -m "feat(business): 负责人字段改为从团队成员下拉选择"
```

---

### 任务 2：团队管理 — 成员详情模态框

**文件：**
- 修改：`templates/team/list.html`（data-* 属性 + 模态框 HTML + JS）
- 追加：`static/style.css`（模态框样式）
- 修改：`tests/test_business.py`（追加测试）

- [ ] **步骤 1：编写失败测试 — 模态框结构存在且卡片含 data 属性**

```python
def test_member_card_has_data_attributes(client, db):
    """成员卡片应包含完整的 data-member-* 属性"""
    from models import Member
    db.session.add(Member(
        name="张三", employee_id="E001", rank="P7",
        group="放射图像研究组", title="工程师", level="A",
        skills="Python,C++", responsible_for="CT图像重建",
    ))
    db.session.commit()

    resp = client.get("/team/")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 模态框结构应存在
    assert 'id="member-modal"' in html
    assert 'class="modal-overlay"' in html
    # 卡片应包含 data 属性
    assert 'data-member-name="张三"' in html
    assert 'data-member-employee-id="E001"' in html
    assert 'data-member-group="放射图像研究组"' in html
```

- [ ] **步骤 2：运行测试验证失败**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_member_card_has_data_attributes -v
```
预期：FAIL

- [ ] **步骤 3：修改模板 — 添加 data 属性、模态框 HTML、JS**

修改 `templates/team/list.html`，完整替换为：

```html
{% extends "base.html" %}
{% block title %}团队管理{% endblock %}
{% block content %}
<div class="page-header-row">
    <div>
        <h1>团队成员</h1>
        <p>管理研究团队人员与能力评估</p>
    </div>
    <a href="{{ url_for('team.new_member') }}" class="btn btn-primary">+ 添加成员</a>
</div>

<form method="get" class="filter-bar">
    <select name="group" class="form-select">
        <option value="">全部组</option>
        {% for g in groups %}<option value="{{ g }}" {% if filters.group == g %}selected{% endif %}>{{ g }}</option>{% endfor %}
    </select>
    <select name="level" class="form-select">
        <option value="">全部评级</option>
        {% for l in levels %}<option value="{{ l }}" {% if filters.level == l %}selected{% endif %}>{{ l }}级</option>{% endfor %}
    </select>
    <button class="btn btn-outline btn-sm">筛选</button>
</form>

{% if members %}
<div class="member-grid">
    {% for m in members %}
    <div class="member-card"
         onclick="openMemberModal(this)"
         data-member-name="{{ m.name }}"
         data-member-employee-id="{{ m.employee_id or '' }}"
         data-member-rank="{{ m.rank or '' }}"
         data-member-group="{{ m.group or '' }}"
         data-member-title="{{ m.title or '' }}"
         data-member-level="{{ m.level or '' }}"
         data-member-skills="{{ m.skills or '' }}"
         data-member-responsible-for="{{ m.responsible_for or '' }}"
         data-member-joined-at="{{ m.joined_at.strftime('%Y-%m-%d') if m.joined_at else '' }}"
         data-member-avatar-color="{{ ['#0891B2','#7C3AED','#059669','#D97706','#0284C7','#DC2626','#475569','#BE185D'][loop.index0 % 8] }}"
         data-member-scores="{{ m.capability_scores | map(attribute='dimension') | join(',') }}"
         data-member-score-values="{{ m.capability_scores | map(attribute='score') | join(',') }}"
         style="cursor:pointer">
        <div class="member-header">
            <div class="member-avatar" style="background:{{ ['#0891B2','#7C3AED','#059669','#D97706','#0284C7','#DC2626','#475569','#BE185D'][loop.index0 % 8] }};">{{ m.name[0] }}</div>
            <div class="member-name">{{ m.name }}</div>
            <span class="member-level {{ m.level | lower if m.level else 'b' }}">{{ m.level }}级</span>
        </div>
        <div class="text-sm text-muted mb-2">
            {{ m.group or '-' }} · {{ m.title or '-' }}
            {% if m.title == '技术经理' %}<span class="manager-badge">技术经理</span>{% endif %}
            {% if m.employee_id %}<br>工号: {{ m.employee_id }}{% endif %}
            {% if m.rank %} · 职级: {{ m.rank }}{% endif %}
        </div>
        {% if m.skills %}
        <div class="member-tags">
            {% for sk in m.skills.split(',') %}
            <span class="badge badge-info">{{ sk.strip() }}</span>
            {% endfor %}
        </div>
        {% endif %}
        {% if m.responsible_for %}
        <div class="member-footer">负责: {{ m.responsible_for }}</div>
        {% endif %}
        <a href="{{ url_for('team.view_member', id=m.id) }}" class="btn btn-outline btn-sm mt-3" onclick="event.stopPropagation()">查看雷达图 →</a>
        <a href="{{ url_for('team.edit_member', id=m.id) }}" class="btn btn-outline btn-sm mt-3" onclick="event.stopPropagation()">编辑</a>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="empty-state">
    <div class="empty-icon">👥</div>
    <div class="empty-text">暂无成员</div>
    <div class="empty-action"><a href="{{ url_for('team.new_member') }}" class="btn btn-primary">添加第一位成员</a></div>
</div>
{% endif %}

<!-- 成员详情模态框 -->
<div id="member-modal" class="modal-overlay" style="display:none;" onclick="closeMemberModal(event)">
    <div class="modal-dialog" onclick="event.stopPropagation()">
        <div class="modal-header">
            <div class="flex-center gap-3">
                <div id="modal-avatar" class="member-avatar" style="width:48px;height:48px;font-size:18px;"></div>
                <div>
                    <h2 id="modal-name" style="font-size:18px;margin:0;"></h2>
                    <span id="modal-level-badge" style="font-size:12px;"></span>
                </div>
            </div>
            <button class="modal-close" onclick="document.getElementById('member-modal').style.display='none'">&times;</button>
        </div>
        <div class="modal-body">
            <div class="modal-detail-row"><span class="modal-detail-label">工号</span><span id="modal-employee-id">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">职级</span><span id="modal-rank">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">组别</span><span id="modal-group">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">职称</span><span id="modal-title">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">评级</span><span id="modal-level">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">技能</span><span id="modal-skills">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">负责方向</span><span id="modal-responsible">-</span></div>
            <div class="modal-detail-row"><span class="modal-detail-label">入职日期</span><span id="modal-joined">-</span></div>
            <div class="modal-detail-row" style="border-top:1px solid var(--color-border);padding-top:12px;margin-top:8px;">
                <span class="modal-detail-label" style="font-weight:700;">能力评分</span>
            </div>
            <div id="modal-scores" class="modal-scores"></div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function openMemberModal(el) {
    var d = el.dataset;
    document.getElementById('modal-avatar').textContent = d.memberName[0];
    document.getElementById('modal-avatar').style.background = d.memberAvatarColor;
    document.getElementById('modal-name').textContent = d.memberName;
    document.getElementById('modal-level-badge').textContent = (d.memberLevel || '') + '级';
    document.getElementById('modal-employee-id').textContent = d.memberEmployeeId || '-';
    document.getElementById('modal-rank').textContent = d.memberRank || '-';
    document.getElementById('modal-group').textContent = d.memberGroup || '-';
    document.getElementById('modal-title').textContent = d.memberTitle || '-';
    document.getElementById('modal-level').textContent = (d.memberLevel || '') + '级';
    document.getElementById('modal-skills').textContent = d.memberSkills || '-';
    document.getElementById('modal-responsible').textContent = d.memberResponsibleFor || '-';
    document.getElementById('modal-joined').textContent = d.memberJoinedAt || '-';

    var dims = (d.memberScores || '').split(',').filter(Boolean);
    var vals = (d.memberScoreValues || '').split(',').filter(Boolean);
    var html = '';
    if (dims.length > 0) {
        for (var i = 0; i < dims.length; i++) {
            html += '<div class="modal-score-row"><span>' + dims[i] + '</span><span class="modal-score-val">' + vals[i] + '</span></div>';
        }
    } else {
        html = '<span class="text-muted text-sm">暂无评分</span>';
    }
    document.getElementById('modal-scores').innerHTML = html;
    document.getElementById('member-modal').style.display = 'flex';
}

function closeMemberModal(e) {
    if (e.target === document.getElementById('member-modal')) {
        document.getElementById('member-modal').style.display = 'none';
    }
}
</script>
{% endblock %}
```

- [ ] **步骤 4：追加 CSS 模态框样式**

在 `static/style.css` 末尾（第 648 行 `}` 之前）追加：

```css
/* ── Modal ── */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,.45);
  z-index: 200;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.modal-dialog {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  max-width: 480px; width: 100%;
  max-height: 85vh; overflow-y: auto;
}
.modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--color-border);
}
.modal-header h2 { font-size: 18px; font-weight: 700; }
.modal-close {
  background: none; border: none;
  font-size: 24px; color: var(--color-fg-muted); cursor: pointer;
  line-height: 1; padding: 0 4px;
  transition: color var(--transition-fast);
}
.modal-close:hover { color: var(--color-fg); }
.modal-body { padding: 16px 24px 24px; }
.modal-detail-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--color-border);
  font-size: 14px;
}
.modal-detail-label {
  font-weight: 600; color: var(--color-fg-secondary);
  min-width: 80px;
}
.modal-scores { margin-top: 8px; }
.modal-score-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 12px; background: var(--color-muted);
  border-radius: var(--radius-sm); margin-bottom: 4px;
  font-size: 13px;
}
.modal-score-val {
  font-weight: 700; color: var(--color-primary);
}
```

- [ ] **步骤 5：运行测试验证通过**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_member_card_has_data_attributes -v
```
预期：PASS

- [ ] **步骤 6：运行全部已有测试确保无回归**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v
```
预期：全部 PASS

- [ ] **步骤 7：Commit**

```bash
git add templates/team/list.html static/style.css tests/test_business.py
git commit -m "feat(team): 成员卡片点击弹出详情模态框"
```

---

### 任务 3：流程制度 — 搜索栏选择后 AJAX 自动刷新

**文件：**
- 修改：`blueprints/process/routes.py:16-30`（list_issues）
- 修改：`templates/process/issue_list.html`（表格容器 + JS）
- 修改：`tests/test_business.py`（追加测试）

- [ ] **步骤 1：编写失败测试 — AJAX 请求返回表格片段**

```python
def test_list_issues_ajax_returns_table_fragment(client, db):
    """AJAX 请求应只返回表格 HTML 片段，不含完整页面结构"""
    from models import Issue
    db.session.add(Issue(title="测试问题", category="流程问题", severity="高", status="待处理"))
    db.session.add(Issue(title="已关闭问题", category="质量问题", severity="中", status="已关闭"))
    db.session.commit()

    # 不带 AJAX 头的普通请求应返回完整页面
    resp = client.get("/process/issues")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "流程制度" in html  # 页面标题

    # 带 AJAX 头的请求应只返回表格片段
    resp_ajax = client.get("/process/issues", headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp_ajax.status_code == 200
    html_ajax = resp_ajax.data.decode()
    # 片段不应包含完整页面结构
    assert "流程制度" not in html_ajax  # 不应有页面标题
    assert "<table" in html_ajax or "empty-state" in html_ajax  # 表格或空状态


def test_list_issues_ajax_filter(client, db):
    """AJAX 筛选应返回正确的筛选结果"""
    from models import Issue
    db.session.add(Issue(title="流程问题A", category="流程问题", severity="高", status="待处理"))
    db.session.add(Issue(title="质量问题B", category="质量问题", severity="中", status="待处理"))
    db.session.commit()

    resp = client.get("/process/issues?category=流程问题",
                      headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "流程问题A" in html
    assert "质量问题B" not in html
```

- [ ] **步骤 2：运行测试验证失败**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_list_issues_ajax_returns_table_fragment tests/test_business.py::test_list_issues_ajax_filter -v
```
预期：FAIL

- [ ] **步骤 3：修改路由 — AJAX 请求返回表格片段**

修改 `blueprints/process/routes.py` 中的 `list_issues` 函数（第 16-30 行）：

```python
@process_bp.route("/issues")
def list_issues():
    category = request.args.get("category")
    status = request.args.get("status")
    query = Issue.query
    if category:
        query = query.filter(Issue.category == category)
    if status:
        query = query.filter(Issue.status == status)
    issues = query.order_by(Issue.created_at.desc()).all()

    # AJAX 请求：只返回表格片段
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "process/_issue_table.html", issues=issues,
        )

    return render_template(
        "process/issue_list.html", issues=issues,
        categories=ISSUE_CATEGORIES, statuses=ISSUE_STATUSES,
        filters={"category": category, "status": status},
    )
```

- [ ] **步骤 4：创建表格片段模板**

创建新文件 `templates/process/_issue_table.html`：

```html
{% if issues %}
<table class="data-table">
    <thead>
        <tr>
            <th>问题描述</th>
            <th>分类</th>
            <th>严重度</th>
            <th>关联制度</th>
            <th>状态</th>
            <th></th>
        </tr>
    </thead>
    <tbody>
        {% for i in issues %}
        <tr>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}">{{ i.title }}</a></td>
            <td><span class="badge badge-warning">{{ i.category }}</span></td>
            <td><span class="severity-{{ 'high' if i.severity == '高' else 'medium' if i.severity == '中' else 'low' }}">● {{ i.severity }}</span></td>
            <td>{% if i.policy %}<a href="{{ url_for('process.edit_policy', id=i.policy.id) }}" class="text-sm">{{ i.policy.title }}</a>{% else %}<span class="text-muted text-sm">-</span>{% endif %}</td>
            <td><span class="badge {{ 'badge-success' if i.status == '已建制度' else 'badge-secondary' if i.status == '已关闭' else 'badge-warning' }}">{{ i.status }}</span></td>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}" class="btn btn-outline btn-sm">编辑</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="empty-state">
    <div class="empty-icon">📋</div>
    <div class="empty-text">暂无问题记录</div>
</div>
{% endif %}
```

- [ ] **步骤 5：修改模板 — 添加容器 + JS 自动筛选**

修改 `templates/process/issue_list.html`，将表格部分包裹在容器中，移除筛选按钮（降级保留为隐藏），添加 JS。

完整替换 `templates/process/issue_list.html`：

```html
{% extends "base.html" %}
{% block title %}流程制度 — 问题记录{% endblock %}
{% block content %}
<div class="page-header-row">
    <div>
        <h1>流程制度</h1>
        <p>问题记录与制度文档管理</p>
    </div>
    <a href="{{ url_for('process.new_issue') }}" class="btn btn-primary">+ 记录问题</a>
</div>

<div class="tabs">
    <a href="{{ url_for('process.list_issues') }}" class="active">问题记录</a>
    <a href="{{ url_for('process.list_policies') }}">制度文档</a>
</div>

<form method="get" class="filter-bar" id="filter-form">
    <select name="category" class="form-select">
        <option value="">全部分类</option>
        {% for c in categories %}<option value="{{ c }}" {% if filters.category == c %}selected{% endif %}>{{ c }}</option>{% endfor %}
    </select>
    <select name="status" class="form-select">
        <option value="">全部状态</option>
        {% for s in statuses %}<option value="{{ s }}" {% if filters.status == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
    </select>
    <button type="submit" class="btn btn-outline btn-sm" id="filter-btn">筛选</button>
</form>

<div id="issue-table-container">
{% if issues %}
<table class="data-table">
    <thead>
        <tr>
            <th>问题描述</th>
            <th>分类</th>
            <th>严重度</th>
            <th>关联制度</th>
            <th>状态</th>
            <th></th>
        </tr>
    </thead>
    <tbody>
        {% for i in issues %}
        <tr>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}">{{ i.title }}</a></td>
            <td><span class="badge badge-warning">{{ i.category }}</span></td>
            <td><span class="severity-{{ 'high' if i.severity == '高' else 'medium' if i.severity == '中' else 'low' }}">● {{ i.severity }}</span></td>
            <td>{% if i.policy %}<a href="{{ url_for('process.edit_policy', id=i.policy.id) }}" class="text-sm">{{ i.policy.title }}</a>{% else %}<span class="text-muted text-sm">-</span>{% endif %}</td>
            <td><span class="badge {{ 'badge-success' if i.status == '已建制度' else 'badge-secondary' if i.status == '已关闭' else 'badge-warning' }}">{{ i.status }}</span></td>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}" class="btn btn-outline btn-sm">编辑</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="empty-state">
    <div class="empty-icon">📋</div>
    <div class="empty-text">暂无问题记录</div>
</div>
{% endif %}
</div>
{% endblock %}

{% block scripts %}
<script>
(function() {
    var categorySelect = document.querySelector('#filter-form select[name="category"]');
    var statusSelect = document.querySelector('#filter-form select[name="status"]');
    var container = document.getElementById('issue-table-container');

    function doFilter() {
        var params = new URLSearchParams();
        if (categorySelect.value) params.set('category', categorySelect.value);
        if (statusSelect.value) params.set('status', statusSelect.value);

        fetch('/process/issues?' + params.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(r) { return r.text(); })
        .then(function(html) {
            container.innerHTML = html;
        });
    }

    categorySelect.addEventListener('change', doFilter);
    statusSelect.addEventListener('change', doFilter);
})();
</script>
{% endblock %}
```

- [ ] **步骤 6：运行测试验证通过**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_list_issues_ajax_returns_table_fragment tests/test_business.py::test_list_issues_ajax_filter -v
```
预期：2 PASS

- [ ] **步骤 7：运行全部已有测试确保无回归**

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v
```
预期：全部 PASS

- [ ] **步骤 8：Commit**

```bash
git add blueprints/process/routes.py templates/process/issue_list.html templates/process/_issue_table.html tests/test_business.py
git commit -m "feat(process): 搜索栏选择类别/状态后 AJAX 自动刷新"
```

---

## 自检

- [x] 规格覆盖度：三个需求各对应一个任务，每个任务有完整的步骤
- [x] 无占位符/TODO：所有步骤都有实际代码
- [x] 类型一致性：Member 模型字段名与模板 data 属性名一一对应；Issue 模型字段名与表格渲染一致
- [x] 三个任务独立，可任意顺序执行
