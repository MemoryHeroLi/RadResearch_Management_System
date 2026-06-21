# 放射影像算法研究部管理系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建一个本地单用户 Web 应用，作为放射影像算法研究部经理的日常管理抓手，覆盖业务管理（TRL 流程跟踪）、团队管理（人员能力雷达图）、流程制度（问题记录与制度文档）三大模块。

**架构：** Flask + Jinja2 服务端渲染 + SQLAlchemy ORM + SQLite 单文件数据库。四个 Blueprint 模块（dashboard/business/team/process）独立挂载，Bootstrap 5 + Chart.js 经 CDN 引入。本地 `python start.py` 启动，浏览器访问 `localhost:5000`。

**技术栈：** Python 3.12 / Flask 2.3.3 / Flask-SQLAlchemy 3.0.5 / SQLite / Bootstrap 5 / Chart.js / pytest 8.3.4

**运行环境：** 所有 Python 命令使用 `"D:\ProgramData\anaconda3\envs\app\python.exe"`（conda app 环境），**不要**用 `conda activate`。

---

## 文件结构

### 配置与入口
- `start.py` — 应用入口，创建 app、注册蓝图、初始化数据库、启动开发服务器
- `config.py` — 配置类（数据库 URI、上传目录、密钥）
- `extensions.py` — `db = SQLAlchemy()` 实例，供模型与蓝图共享
- `requirements.txt` — 依赖清单

### 数据层
- `models.py` — 全部 6 个数据模型（TechPoint / StageProgress / StageDocument / Member / CapabilityScore / Issue / Policy）
- `blueprints/business/process_template.py` — 标准流程模板常量（4 阶段子步骤定义）

### 蓝图（路由层）
- `blueprints/dashboard/__init__.py` + `routes.py` — 仪表盘
- `blueprints/business/__init__.py` + `routes.py` — 业务管理
- `blueprints/team/__init__.py` + `routes.py` — 团队管理
- `blueprints/process/__init__.py` + `routes.py` — 流程制度

### 模板（视图层）
- `templates/base.html` — 基础布局（Bootstrap 壳 + 顶部导航栏）
- `templates/dashboard/index.html` — 仪表盘
- `templates/business/{list,form,kanban}.html` — 业务管理三页
- `templates/business/_substep.html` — 子步骤卡片局部模板（被 kanban 引用）
- `templates/team/{list,form,radar}.html` — 团队管理三页
- `templates/process/{issue_list,issue_form,policy_list,policy_form}.html` — 流程制度四页

### 静态与上传
- `static/style.css` — 少量自定义样式（看板列、雷达图容器）
- `uploads/` — 文档上传目录（运行时自动创建）

### 测试
- `tests/conftest.py` — pytest 夹具（内存数据库 app）
- `tests/test_models.py` — 模型与流程模板测试
- `tests/test_business.py` — 业务管理路由测试
- `tests/test_team.py` — 团队管理路由测试
- `tests/test_process.py` — 流程制度路由测试

---

## 任务 1：项目脚手架与配置

**文件：**
- 创建：`requirements.txt`
- 创建：`config.py`
- 创建：`extensions.py`
- 创建：`tests/conftest.py`

- [ ] **步骤 1：编写 requirements.txt**

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
pytest==8.3.4
```

- [ ] **步骤 2：编写 config.py**

```python
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "rad-research-dev-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "rad_research.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
```

- [ ] **步骤 3：编写 extensions.py**

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

- [ ] **步骤 4：编写 tests/conftest.py（测试夹具）**

```python
import pytest
from extensions import db as _db


@pytest.fixture()
def app():
    """内存数据库的测试 app"""
    from flask import Flask

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["UPLOAD_FOLDER"] = "/tmp/rad_test_uploads"

    _db.init_app(app)

    # 注册全部模型（让 create_all 建表）
    import models  # noqa: F401

    with app.app_context():
        _db.create_all()

    # 注册蓝图（在各自任务中创建后取消注释；本任务先注册一个空路由避免报错）
    @app.route("/")
    def _index():
        return "ok"

    yield app

    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    """在 app_context 中提供可用的 db session"""
    with app.app_context():
        yield _db
```

- [ ] **步骤 5：验证夹具可用**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/conftest.py --collect-only -q`
预期：无错误，收集通过（即使无测试用例）。

- [ ] **步骤 6：Commit**

```bash
git add requirements.txt config.py extensions.py tests/conftest.py
git commit -m "chore: 项目脚手架与测试夹具"
```

---

## 任务 2：数据模型

**文件：**
- 创建：`models.py`
- 创建：`tests/test_models.py`

- [ ] **步骤 1：编写失败测试 tests/test_models.py**

```python
from datetime import datetime
from models import (
    TechPoint, StageProgress, StageDocument,
    Member, CapabilityScore, Issue, Policy,
)


def test_create_tech_point(db):
    tp = TechPoint(name="低剂量CT去噪", direction="CT重建", owner="张三")
    db.session.add(tp)
    db.session.commit()
    assert tp.id is not None
    assert tp.current_stage == 1
    assert tp.status == "进行中"
    assert tp.created_at is not None


def test_tech_point_stage_progress_relation(db):
    tp = TechPoint(name="MRI伪影校正", direction="MRI")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求导入")
    db.session.add(sp)
    db.session.commit()
    assert tp.stage_progresses.count() == 1
    assert tp.stage_progresses[0].sub_step == "需求导入"


def test_stage_document_relation(db):
    tp = TechPoint(name="DR结节检测", direction="DR")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求评审")
    db.session.add(sp)
    db.session.commit()
    doc = StageDocument(
        stage_progress_id=sp.id, doc_type="会议纪要",
        file_path="uploads/x.pdf", original_name="纪要.pdf",
    )
    db.session.add(doc)
    db.session.commit()
    assert sp.documents.count() == 1
    assert sp.documents[0].original_name == "纪要.pdf"


def test_member_capability_scores(db):
    m = Member(name="张三", group="CT重建组", level="A")
    db.session.add(m)
    db.session.commit()
    db.session.add(CapabilityScore(member_id=m.id, dimension="算法能力", score=9))
    db.session.commit()
    assert m.capability_scores.count() == 1
    assert m.capability_scores[0].score == 9


def test_issue_policy_relation(db):
    p = Policy(title="文档评审制度", version="1.0")
    db.session.add(p)
    db.session.commit()
    i = Issue(title="评审不及时", category="流程问题", severity="高",
              linked_policy_id=p.id)
    db.session.add(i)
    db.session.commit()
    assert p.issues.count() == 1
    assert p.issues[0].title == "评审不及时"
    assert i.policy.title == "文档评审制度"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_models.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'models'`

- [ ] **步骤 3：编写 models.py**

```python
from datetime import datetime, date

from extensions import db


class TechPoint(db.Model):
    """技术点"""
    __tablename__ = "tech_point"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    direction = db.Column(db.String(50), nullable=False)
    current_stage = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="进行中")
    owner = db.Column(db.String(50))
    description = db.Column(db.Text)
    source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class StageProgress(db.Model):
    """阶段进展——每个阶段下的子步骤"""
    __tablename__ = "stage_progress"
    id = db.Column(db.Integer, primary_key=True)
    tech_point_id = db.Column(
        db.Integer, db.ForeignKey("tech_point.id"), nullable=False
    )
    stage = db.Column(db.Integer, nullable=False)
    sub_step = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    tech_point = db.relationship("TechPoint", backref="stage_progresses")


class StageDocument(db.Model):
    """阶段文档——子步骤关联的文档/材料"""
    __tablename__ = "stage_document"
    id = db.Column(db.Integer, primary_key=True)
    stage_progress_id = db.Column(
        db.Integer, db.ForeignKey("stage_progress.id"), nullable=False
    )
    doc_type = db.Column(db.String(50))
    file_path = db.Column(db.String(500))
    original_name = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    stage_progress = db.relationship("StageProgress", backref="documents")


class Member(db.Model):
    """团队成员"""
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    group = db.Column(db.String(50))
    title = db.Column(db.String(50))
    level = db.Column(db.String(10))
    skills = db.Column(db.String(500))
    responsible_for = db.Column(db.String(500))
    joined_at = db.Column(db.Date)


class CapabilityScore(db.Model):
    """能力评分——5个评估维度"""
    __tablename__ = "capability_score"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(
        db.Integer, db.ForeignKey("member.id"), nullable=False
    )
    dimension = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)
    member = db.relationship("Member", backref="capability_scores")


class Policy(db.Model):
    """流程制度"""
    __tablename__ = "policy"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(20), default="1.0")
    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)


class Issue(db.Model):
    """问题记录"""
    __tablename__ = "issue"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(20))
    severity = db.Column(db.String(10))
    status = db.Column(db.String(20), default="待处理")
    linked_policy_id = db.Column(
        db.Integer, db.ForeignKey("policy.id"), nullable=True
    )
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    policy = db.relationship("Policy", backref="issues")
```

- [ ] **步骤 4：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_models.py -v`
预期：PASS（5 个测试全过）。

- [ ] **步骤 5：Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: 数据模型（6张表）"
```

---

## 任务 3：标准流程模板

**文件：**
- 创建：`blueprints/business/process_template.py`
- 创建：`blueprints/__init__.py`（空包文件）
- 创建：`blueprints/business/__init__.py`（空包文件）
- 创建：`tests/test_models.py`（追加测试）

- [ ] **步骤 1：编写失败测试（追加到 tests/test_models.py 末尾）**

```python
from blueprints.business.process_template import STANDARD_PROCESS, GATE_STEPS


def test_standard_process_has_four_stages():
    assert len(STANDARD_PROCESS) == 4
    assert [s["stage"] for s in STANDARD_PROCESS] == [1, 2, 3, 4]


def test_standard_process_substeps_complete():
    # 阶段1
    assert "需求评审" in STANDARD_PROCESS[0]["steps"]
    # 阶段2
    assert "功能构思评审" in STANDARD_PROCESS[1]["steps"]
    # 阶段3
    assert "TRL6预研验收" in STANDARD_PROCESS[2]["steps"]
    # 阶段4
    assert "TRL7验收" in STANDARD_PROCESS[3]["steps"]


def test_gate_steps_cover_three_reviews():
    assert "需求评审" in GATE_STEPS
    assert "功能构思评审" in GATE_STEPS
    assert "TRL6预研验收" in GATE_STEPS
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_models.py::test_standard_process_has_four_stages -v`
预期：FAIL，`ModuleNotFoundError: No module named 'blueprints'`

- [ ] **步骤 3：创建包文件**

`blueprints/__init__.py` 内容：

```python
```

`blueprints/business/__init__.py` 内容：

```python
```

- [ ] **步骤 4：编写 blueprints/business/process_template.py**

```python
"""标准预研流程模板——4个阶段、每阶段的子步骤，以及强制性评审关卡。

依据子功能模块-业务管理.md 中的研发流程定义。
"""

# 4个阶段的子步骤（顺序即执行顺序）
STANDARD_PROCESS = [
    {
        "stage": 1,
        "name": "需求收集",
        "trl": "TRL2",
        "steps": ["需求导入", "需求评审"],
    },
    {
        "stage": 2,
        "name": "功能构思",
        "trl": "TRL3",
        "steps": [
            "临床调研", "痛点分析", "需求提炼", "竞品分析",
            "方案构思", "可行性分析", "功能构思评审",
        ],
    },
    {
        "stage": 3,
        "name": "方案预研",
        "trl": "TRL6",
        "steps": [
            "技术调研", "方案设计及评审", "任务分解", "子任务开发",
            "仿真验证", "TRL6预研验收", "文档撰写", "文档评审",
        ],
    },
    {
        "stage": 4,
        "name": "版本开发",
        "trl": "TRL7",
        "steps": [
            "方案澄清", "功能开发", "功能测试",
            "临床验证", "TRL7验收",
        ],
    },
]

# 强制性评审关卡——必须通过才能进入下一阶段
GATE_STEPS = {"需求评审", "功能构思评审", "TRL6预研验收"}

STAGE_NAMES = {s["stage"]: s["name"] for s in STANDARD_PROCESS}
STAGE_TRL = {s["stage"]: s["trl"] for s in STANDARD_PROCESS}
```

- [ ] **步骤 5：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_models.py -v`
预期：PASS（全部 8 个测试通过）。

- [ ] **步骤 6：Commit**

```bash
git add blueprints/__init__.py blueprints/business/__init__.py blueprints/business/process_template.py tests/test_models.py
git commit -m "feat: 标准预研流程模板"
```

---

## 任务 4：应用入口与基础布局

**文件：**
- 创建：`start.py`
- 创建：`templates/base.html`
- 创建：`static/style.css`

- [ ] **步骤 1：编写 start.py**

```python
import os

from flask import Flask

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # 导入模型以让 create_all 可见
    import models  # noqa: F401

    # 注册蓝图（在各任务中逐步引入；先注册 dashboard）
    from blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from blueprints.business import business_bp
    app.register_blueprint(business_bp)

    from blueprints.team import team_bp
    app.register_blueprint(team_bp)

    from blueprints.process import process_bp
    app.register_blueprint(process_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

> 注：此文件在任务 4 中会因蓝图未定义而无法运行——这是预期的。蓝图在任务 5-9 中创建。任务 4 仅验证 base 模板渲染。我们用一个临时最小验证：先创建 4 个蓝图的占位 `__init__.py`（含空蓝图），任务 5 起逐个填充。

为避免 start.py 在任务 4 即失败，先创建各蓝图占位：

`blueprints/dashboard/__init__.py`：

```python
from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)
```

`blueprints/team/__init__.py`：

```python
from flask import Blueprint

team_bp = Blueprint("team", __name__)
```

`blueprints/process/__init__.py`：

```python
from flask import Blueprint

process_bp = Blueprint("process", __name__)
```

`blueprints/business/__init__.py`（覆盖任务3的空文件）：

```python
from flask import Blueprint

business_bp = Blueprint("business", __name__)
```

- [ ] **步骤 2：编写 templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}放射影像算法研究部管理系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark" style="background-color:#0d6efd;">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard.index') }}">🔬 放射影像算法研究部管理系统</a>
            <div class="navbar-nav">
                <a class="nav-link {% if request.blueprint == 'dashboard' %}active{% endif %}"
                   href="{{ url_for('dashboard.index') }}">仪表盘</a>
                <a class="nav-link {% if request.blueprint == 'business' %}active{% endif %}"
                   href="{{ url_for('business.list_tech_points') }}">业务管理</a>
                <a class="nav-link {% if request.blueprint == 'team' %}active{% endif %}"
                   href="{{ url_for('team.list_members') }}">团队管理</a>
                <a class="nav-link {% if request.blueprint == 'process' %}active{% endif %}"
                   href="{{ url_for('process.list_issues') }}">流程制度</a>
            </div>
        </div>
    </nav>
    <div class="container py-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **步骤 3：编写 static/style.css**

```css
/* 看板列 */
.kanban-board {
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    padding-bottom: 1rem;
}
.kanban-column {
    min-width: 260px;
    flex-shrink: 0;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.75rem;
}
.kanban-column.current {
    border: 2px solid #0d6efd;
    background: #f0f7ff;
}
.kanban-column.locked {
    opacity: 0.5;
}
.substep-card {
    background: #fff;
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}
.substep-card.completed {
    border-left: 3px solid #198754;
}
.substep-card.pending {
    border-left: 3px solid #ffc107;
}
.substep-card.todo {
    border-left: 3px solid #dee2e6;
}
.gate-badge {
    background: #dc3545;
    color: #fff;
    font-size: 0.65rem;
    padding: 1px 5px;
    border-radius: 8px;
    margin-left: 4px;
}
/* 雷达图容器 */
.radar-container {
    max-width: 400px;
    margin: 0 auto;
}
```

- [ ] **步骤 4：验证应用可启动（手动）**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -c "import start; print('OK', start.app.url_map)"`
预期：输出包含 `OK` 与路由表，无异常（蓝图已占位，dashboard.index 等端点尚不存在会先报错——见任务 5 创建。此处仅验证 import 不抛 ImportError/语法错）。

> 如果 `url_for('dashboard.index')` 因端点未定义导致 map 构建报错，可接受——任务 5 会补齐。本步只确认 `start.py` 能被 Python 解析、蓝图能注册。

- [ ] **步骤 5：Commit**

```bash
git add start.py templates/base.html static/style.css blueprints/dashboard/__init__.py blueprints/team/__init__.py blueprints/process/__init__.py blueprints/business/__init__.py
git commit -m "feat: 应用入口与基础布局"
```

---

## 任务 5：仪表盘蓝图

**文件：**
- 创建：`blueprints/dashboard/routes.py`
- 修改：`blueprints/dashboard/__init__.py`（注册路由模块）
- 创建：`templates/dashboard/index.html`
- 创建：`tests/test_dashboard.py`

- [ ] **步骤 1：编写失败测试 tests/test_dashboard.py**

```python
def test_dashboard_index_renders(client, db):
    import models  # noqa: F401
    resp = client.get("/")
    assert resp.status_code == 200
    assert "放射影像算法研究部".encode() in resp.data
    assert "技术点总数".encode() in resp.data


def test_dashboard_shows_counts(client, db):
    from models import TechPoint, Issue
    db.session.add(TechPoint(name="测试点", direction="CT重建", status="进行中"))
    db.session.add(Issue(title="问题1", status="待处理"))
    db.session.commit()
    resp = client.get("/")
    assert resp.status_code == 200
    # 统计卡片应显示数字（HTML 中含 "1" 在统计位置）
    assert b"1" in resp.data
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_dashboard.py -v`
预期：FAIL（404 或端点不存在）。

- [ ] **步骤 3：修改 conftest 让测试 app 注册全部蓝图**

将 `tests/conftest.py` 中 `app` 夹具替换为复用 `start.create_app`，但强制内存数据库。修改 `tests/conftest.py` 顶部 import 与 `app` 夹具：

```python
import pytest
import os


@pytest.fixture()
def app(tmp_path):
    """内存数据库的测试 app，复用生产工厂但覆盖配置"""
    from start import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 重建表到内存库
    from extensions import db as _db
    with app.app_context():
        _db.drop_all()
        _db.create_all()

    yield app

    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        from extensions import db as _db
        yield _db
```

> 这样 conftest 会依赖 `start.create_app` 与所有蓝图。在任务 5 完成前测试会因蓝图路由未完成而失败——这正是 TDD 的红灯。任务 5-9 逐步让它们转绿。

- [ ] **步骤 4：编写 blueprints/dashboard/routes.py**

```python
from flask import render_template
from sqlalchemy import func

from blueprints.dashboard import dashboard_bp
from extensions import db
from models import TechPoint, Issue, Member, Policy


@dashboard_bp.route("/")
def index():
    tech_point_total = db.session.query(func.count(TechPoint.id)).scalar() or 0
    in_progress = (
        db.session.query(func.count(TechPoint.id))
        .filter(TechPoint.status == "进行中")
        .scalar() or 0
    )
    member_total = db.session.query(func.count(Member.id)).scalar() or 0
    pending_issues = (
        db.session.query(func.count(Issue.id))
        .filter(Issue.status == "待处理")
        .scalar() or 0
    )
    recent_points = (
        TechPoint.query.order_by(TechPoint.updated_at.desc()).limit(5).all()
    )
    pending_issue_list = (
        Issue.query.filter(Issue.status == "待处理")
        .order_by(Issue.created_at.desc()).all()
    )
    return render_template(
        "dashboard/index.html",
        tech_point_total=tech_point_total,
        in_progress=in_progress,
        member_total=member_total,
        pending_issues=pending_issues,
        recent_points=recent_points,
        pending_issue_list=pending_issue_list,
    )
```

- [ ] **步骤 5：修改 blueprints/dashboard/__init__.py 注册路由**

```python
from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)

from blueprints.dashboard import routes  # noqa: E402,F401
```

- [ ] **步骤 6：编写 templates/dashboard/index.html**

```html
{% extends "base.html" %}
{% block title %}仪表盘{% endblock %}
{% block content %}
<h2 class="mb-4">管理总览</h2>
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <div class="small">技术点总数</div>
                <div class="display-6">{{ tech_point_total }}</div>
                <div class="small">进行中: {{ in_progress }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-success">
            <div class="card-body">
                <div class="small">进行中预研</div>
                <div class="display-6">{{ in_progress }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <div class="small">团队人数</div>
                <div class="display-6">{{ member_total }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-danger">
            <div class="card-body">
                <div class="small">待处理问题</div>
                <div class="display-6">{{ pending_issues }}</div>
            </div>
        </div>
    </div>
</div>
<div class="row g-3">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">最近更新的技术点</div>
            <ul class="list-group list-group-flush">
                {% for p in recent_points %}
                <li class="list-group-item d-flex justify-content-between">
                    <a href="{{ url_for('business.view_tech_point', id=p.id) }}">{{ p.name }}</a>
                    <span class="text-muted small">阶段{{ p.current_stage }} · {{ p.updated_at.strftime('%Y-%m-%d') if p.updated_at else '' }}</span>
                </li>
                {% else %}
                <li class="list-group-item text-muted">暂无技术点</li>
                {% endfor %}
            </ul>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">待处理问题</div>
            <ul class="list-group list-group-flush">
                {% for i in pending_issue_list %}
                <li class="list-group-item">
                    <span class="text-{{ 'danger' if i.severity == '高' else 'warning' if i.severity == '中' else 'secondary' }}">●</span>
                    {{ i.title }}
                </li>
                {% else %}
                <li class="list-group-item text-muted">暂无待处理问题</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **步骤 7：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_dashboard.py -v`
预期：PASS（2 个测试通过）。注意：此时 conftest 已依赖全部蓝图，business/team/process 蓝图尚无路由——需确认其余蓝图 `__init__.py` 已能 import（任务 4 已建占位）。

- [ ] **步骤 8：Commit**

```bash
git add blueprints/dashboard/ templates/dashboard/ tests/test_dashboard.py tests/conftest.py
git commit -m "feat: 仪表盘首页与统计卡片"
```

---

## 任务 6：业务管理——技术点列表与新增

**文件：**
- 创建：`blueprints/business/routes.py`
- 修改：`blueprints/business/__init__.py`（注册路由）
- 创建：`templates/business/list.html`
- 创建：`templates/business/form.html`
- 创建：`tests/test_business.py`

- [ ] **步骤 1：编写失败测试 tests/test_business.py**

```python
def test_list_tech_points_empty(client, db):
    resp = client.get("/business")
    assert resp.status_code == 200
    assert "技术点".encode() in resp.data


def test_create_tech_point_auto_generates_stage_progress(client, db):
    resp = client.post("/business/new", data={
        "name": "低剂量CT去噪",
        "direction": "CT重建",
        "owner": "张三",
        "status": "进行中",
        "source": "临床反馈",
        "description": "测试描述",
    }, follow_redirects=True)
    assert resp.status_code == 200

    from models import TechPoint, StageProgress
    tp = TechPoint.query.first()
    assert tp is not None
    assert tp.name == "低剂量CT去噪"
    # 标准流程模板共 2+7+8+5 = 22 个子步骤
    assert StageProgress.query.count() == 22
    # 所有子步骤 stage 覆盖 1-4
    stages = {sp.stage for sp in StageProgress.query.all()}
    assert stages == {1, 2, 3, 4}


def test_filter_tech_points_by_stage(client, db):
    from models import TechPoint
    db.session.add(TechPoint(name="A", direction="CT重建", current_stage=1, status="进行中"))
    db.session.add(TechPoint(name="B", direction="MRI", current_stage=3, status="进行中"))
    db.session.commit()
    resp = client.get("/business?stage=3")
    assert b"B" in resp.data
    assert b"A" not in resp.data
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v`
预期：FAIL（404，路由未定义）。

- [ ] **步骤 3：编写 blueprints/business/routes.py（列表 + 新增）**

```python
from flask import render_template, request, redirect, url_for, flash

from blueprints.business import business_bp
from blueprints.business.process_template import STANDARD_PROCESS, STAGE_NAMES
from extensions import db
from models import TechPoint, StageProgress


@business_bp.route("/")
def list_tech_points():
    stage = request.args.get("stage", type=int)
    status = request.args.get("status")
    q = request.args.get("q", "").strip()

    query = TechPoint.query
    if stage:
        query = query.filter(TechPoint.current_stage == stage)
    if status:
        query = query.filter(TechPoint.status == status)
    if q:
        query = query.filter(TechPoint.name.contains(q))
    points = query.order_by(TechPoint.updated_at.desc()).all()
    return render_template(
        "business/list.html",
        points=points,
        stages=STANDARD_PROCESS,
        stage_names=STAGE_NAMES,
        filters={"stage": stage, "status": status, "q": q},
    )


@business_bp.route("/new", methods=["GET", "POST"])
def new_tech_point():
    if request.method == "POST":
        tp = TechPoint(
            name=request.form["name"],
            direction=request.form["direction"],
            owner=request.form.get("owner", ""),
            status=request.form.get("status", "进行中"),
            source=request.form.get("source", ""),
            description=request.form.get("description", ""),
            current_stage=1,
        )
        db.session.add(tp)
        db.session.flush()  # 取得 tp.id
        # 按标准流程模板创建全部子步骤
        for stage_def in STANDARD_PROCESS:
            for step in stage_def["steps"]:
                db.session.add(StageProgress(
                    tech_point_id=tp.id,
                    stage=stage_def["stage"],
                    sub_step=step,
                    is_completed=False,
                ))
        db.session.commit()
        flash("技术点已创建", "success")
        return redirect(url_for("business.view_tech_point", id=tp.id))
    return render_template("business/form.html", point=None, stages=STANDARD_PROCESS)


@business_bp.route("/<int:id>")
def view_tech_point(id):
    # 任务 7 实现
    from models import TechPoint
    tp = TechPoint.query.get_or_404(id)
    return render_template("business/kanban.html", point=tp)


@business_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_tech_point(id):
    from models import TechPoint
    tp = TechPoint.query.get_or_404(id)
    if request.method == "POST":
        tp.name = request.form["name"]
        tp.direction = request.form["direction"]
        tp.owner = request.form.get("owner", "")
        tp.status = request.form.get("status", tp.status)
        tp.source = request.form.get("source", "")
        tp.description = request.form.get("description", "")
        db.session.commit()
        flash("技术点已更新", "success")
        return redirect(url_for("business.view_tech_point", id=tp.id))
    return render_template("business/form.html", point=tp, stages=STANDARD_PROCESS)
```

- [ ] **步骤 4：修改 blueprints/business/__init__.py 注册路由**

```python
from flask import Blueprint

business_bp = Blueprint("business", __name__)

from blueprints.business import routes  # noqa: E402,F401
```

- [ ] **步骤 5：编写 templates/business/list.html**

```html
{% extends "base.html" %}
{% block title %}业务管理{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>技术点列表</h2>
    <a href="{{ url_for('business.new_tech_point') }}" class="btn btn-primary">+ 新增技术点</a>
</div>
<form method="get" class="row g-2 mb-3">
    <div class="col-auto">
        <select name="stage" class="form-select form-select-sm">
            <option value="">全部阶段</option>
            {% for s in stages %}
            <option value="{{ s.stage }}" {% if filters.stage == s.stage %}selected{% endif %}>{{ s.stage }}-{{ s.name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="col-auto">
        <select name="status" class="form-select form-select-sm">
            <option value="">全部状态</option>
            {% for st in ['进行中', '已完成', '暂停'] %}
            <option value="{{ st }}" {% if filters.status == st %}selected{% endif %}>{{ st }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="col-auto">
        <input type="text" name="q" class="form-control form-control-sm" placeholder="搜索技术点..." value="{{ filters.q }}">
    </div>
    <div class="col-auto">
        <button class="btn btn-outline-primary btn-sm">筛选</button>
    </div>
</form>
<table class="table table-hover align-middle">
    <thead class="table-light">
        <tr>
            <th>技术点名称</th><th>技术方向</th><th>当前阶段</th>
            <th>状态</th><th>负责人</th><th>更新时间</th><th></th>
        </tr>
    </thead>
    <tbody>
        {% for p in points %}
        <tr>
            <td><a href="{{ url_for('business.view_tech_point', id=p.id) }}">{{ p.name }}</a></td>
            <td><span class="badge bg-info text-dark">{{ p.direction }}</span></td>
            <td><span class="badge bg-warning text-dark">阶段{{ p.current_stage }}</span></td>
            <td>
                <span class="badge bg-{{ 'success' if p.status == '已完成' else 'warning' if p.status == '进行中' else 'secondary' }}">{{ p.status }}</span>
            </td>
            <td>{{ p.owner or '-' }}</td>
            <td class="text-muted small">{{ p.updated_at.strftime('%Y-%m-%d') if p.updated_at else '' }}</td>
            <td><a href="{{ url_for('business.edit_tech_point', id=p.id) }}" class="btn btn-sm btn-outline-secondary">编辑</a></td>
        </tr>
        {% else %}
        <tr><td colspan="7" class="text-center text-muted py-4">暂无技术点，点击右上角新增</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

- [ ] **步骤 6：编写 templates/business/form.html**

```html
{% extends "base.html" %}
{% block title %}{{ '编辑' if point else '新增' }}技术点{% endblock %}
{% block content %}
<h2 class="mb-4">{{ '编辑' if point else '新增' }}技术点</h2>
<form method="post">
    <div class="mb-3">
        <label class="form-label">技术点名称 *</label>
        <input type="text" name="name" class="form-control" required value="{{ point.name if point else '' }}">
    </div>
    <div class="row mb-3">
        <div class="col">
            <label class="form-label">技术方向 *</label>
            <select name="direction" class="form-select" required>
                {% for d in ['CT重建', 'MRI', 'DR', '超声'] %}
                <option value="{{ d }}" {% if point and point.direction == d %}selected{% endif %}>{{ d }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col">
            <label class="form-label">状态</label>
            <select name="status" class="form-select">
                {% for st in ['进行中', '已完成', '暂停'] %}
                <option value="{{ st }}" {% if point and point.status == st %}selected{% endif %}>{{ st }}</option>
                {% endfor %}
            </select>
        </div>
    </div>
    <div class="mb-3">
        <label class="form-label">负责人</label>
        <input type="text" name="owner" class="form-control" value="{{ point.owner if point else '' }}">
    </div>
    <div class="mb-3">
        <label class="form-label">需求来源</label>
        <input type="text" name="source" class="form-control" value="{{ point.source if point else '' }}">
    </div>
    <div class="mb-3">
        <label class="form-label">详细描述</label>
        <textarea name="description" class="form-control" rows="4">{{ point.description if point else '' }}</textarea>
    </div>
    <button class="btn btn-primary">保存</button>
    <a href="{{ url_for('business.list_tech_points') }}" class="btn btn-outline-secondary">取消</a>
</form>
{% if not point %}
<div class="alert alert-info mt-3 small">
    新建后将按标准预研流程自动生成 4 个阶段、共 22 个子步骤的跟踪记录。
</div>
{% endif %}
{% endblock %}
```

- [ ] **步骤 7：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v`
预期：PASS（3 个测试通过）。

- [ ] **步骤 8：Commit**

```bash
git add blueprints/business/ templates/business/list.html templates/business/form.html tests/test_business.py
git commit -m "feat: 业务管理技术点列表与新增（自动生成子步骤）"
```

---

## 任务 7：业务管理——看板详情与阶段关卡

**文件：**
- 修改：`blueprints/business/routes.py`（`view_tech_point` 完善）
- 创建：`templates/business/kanban.html`
- 创建：`templates/business/_substep.html`
- 追加：`tests/test_business.py`

- [ ] **步骤 1：追加失败测试到 tests/test_business.py**

```python
def test_view_tech_point_kanban(client, db):
    from models import TechPoint
    tp = TechPoint(name="看板测试", direction="CT重建", current_stage=1)
    db.session.add(tp)
    db.session.flush()
    from blueprints.business.process_template import STANDARD_PROCESS
    from models import StageProgress
    for s in STANDARD_PROCESS:
        for step in s["steps"]:
            db.session.add(StageProgress(tech_point_id=tp.id, stage=s["stage"], sub_step=step))
    db.session.commit()
    resp = client.get(f"/business/{tp.id}")
    assert resp.status_code == 200
    assert b"需求导入" in resp.data
    assert b"TRL6" in resp.data or b"trl6" in resp.data.lower() or b"\xe9\xa2\x84\xe7\xa0\x94".encode() in resp.data  # 阶段名
    # 阶段4未解锁时应显示锁定提示
    assert "未解锁".encode() in resp.data or "locked".encode() in resp.data


def test_toggle_substep_completion(client, db):
    from models import TechPoint, StageProgress
    tp = TechPoint(name="切换测试", direction="CT重建")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求导入")
    db.session.add(sp)
    db.session.commit()
    resp = client.post(f"/business/stage/{sp.id}/toggle", follow_redirects=True)
    assert resp.status_code == 200
    db.session.refresh(sp)
    assert sp.is_completed is True
    assert sp.completed_at is not None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v`
预期：FAIL（看板模板未完善、toggle 路由不存在）。

- [ ] **步骤 3：修改 blueprints/business/routes.py——完善 view_tech_point 并新增 toggle 路由**

替换 `view_tech_point` 函数为：

```python
@business_bp.route("/<int:id>")
def view_tech_point(id):
    from models import TechPoint, StageProgress
    from blueprints.business.process_template import (
        STANDARD_PROCESS, GATE_STEPS, STAGE_NAMES, STAGE_TRL,
    )
    tp = TechPoint.query.get_or_404(id)
    # 计算每阶段完成情况与关卡通过情况
    stages_info = []
    unlocked = True  # 第一阶段默认解锁
    for sdef in STANDARD_PROCESS:
        substeps = (
            StageProgress.query
            .filter_by(tech_point_id=tp.id, stage=sdef["stage"])
            .order_by(StageProgress.id).all()
        )
        gate_passed = all(
            sp.is_completed for sp in substeps if sp.sub_step in GATE_STEPS
        )
        all_done = bool(substeps) and all(sp.is_completed for sp in substeps)
        stages_info.append({
            "stage": sdef["stage"],
            "name": sdef["name"],
            "trl": sdef["trl"],
            "substeps": substeps,
            "unlocked": unlocked,
            "gate_passed": gate_passed,
            "all_done": all_done,
        })
        # 下一阶段解锁条件：本阶段评审关卡已通过
        unlocked = unlocked and gate_passed
    return render_template(
        "business/kanban.html",
        point=tp,
        stages_info=stages_info,
        gate_steps=GATE_STEPS,
    )
```

在 `routes.py` 末尾新增 toggle 路由：

```python
@business_bp.route("/stage/<int:sp_id>/toggle", methods=["POST"])
def toggle_substep(sp_id):
    from models import StageProgress
    from datetime import datetime
    sp = StageProgress.query.get_or_404(sp_id)
    sp.is_completed = not sp.is_completed
    sp.completed_at = datetime.utcnow() if sp.is_completed else None
    db.session.commit()
    flash(f"子步骤「{sp.sub_step}」已{'完成' if sp.is_completed else '取消完成'}", "info")
    return redirect(url_for("business.view_tech_point", id=sp.tech_point_id))
```

- [ ] **步骤 4：编写 templates/business/_substep.html（子步骤局部模板）**

```html
<div class="substep-card {{ 'completed' if sp.is_completed else 'todo' }}">
    <div class="d-flex justify-content-between align-items-start">
        <div>
            <strong>{{ sp.sub_step }}</strong>
            {% if sp.sub_step in gate_steps %}<span class="gate-badge">关卡</span>{% endif %}
            {% if sp.is_completed %}
            <div class="text-muted small">完成于 {{ sp.completed_at.strftime('%Y-%m-%d') if sp.completed_at else '' }}</div>
            {% endif %}
            {% if sp.notes %}<div class="small mt-1">{{ sp.notes }}</div>{% endif %}
            {% for doc in sp.documents %}
            <div class="small"><a href="{{ url_for('business.download_doc', doc_id=doc.id) }}">📎 {{ doc.original_name }}</a></div>
            {% endfor %}
        </div>
        <form method="post" action="{{ url_for('business.toggle_substep', sp_id=sp.id) }}">
            <input type="checkbox" class="form-check-input" onchange="this.form.submit()" {% if sp.is_completed %}checked{% endif %}>
        </form>
    </div>
    <form method="post" action="{{ url_for('business.upload_doc', sp_id=sp.id) }}" enctype="multipart/form-data" class="mt-2">
        <div class="input-group input-group-sm">
            <input type="file" name="file" class="form-control" required>
            <input type="text" name="doc_type" class="form-control" placeholder="类型(评审材料/会议纪要/PPT)" style="max-width:140px">
            <button class="btn btn-outline-primary">上传</button>
        </div>
    </form>
</div>
```

- [ ] **步骤 5：编写 templates/business/kanban.html**

```html
{% extends "base.html" %}
{% block title %}{{ point.name }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <div>
        <h2>{{ point.name }}
            <span class="badge bg-info text-dark">{{ point.direction }}</span>
            <span class="badge bg-{{ 'success' if point.status == '已完成' else 'warning' if point.status == '进行中' else 'secondary' }}">{{ point.status }}</span>
        </h2>
        <div class="text-muted small">负责人: {{ point.owner or '-' }} · 当前阶段: {{ point.current_stage }}</div>
    </div>
    <a href="{{ url_for('business.edit_tech_point', id=point.id) }}" class="btn btn-outline-secondary btn-sm">编辑</a>
</div>

<div class="kanban-board">
    {% for si in stages_info %}
    <div class="kanban-column {{ 'current' if si.stage == point.current_stage else '' }} {{ 'locked' if not si.unlocked else '' }}">
        <h6 class="mb-2">{{ si.stage }}. {{ si.name }}
            <span class="badge bg-secondary">{{ si.trl }}</span>
        </h6>
        {% if si.gate_passed %}<span class="badge bg-success mb-2">关卡已通过</span>{% endif %}
        {% if not si.unlocked and si.stage != 1 %}
        <div class="alert alert-warning small p-2 mb-2">未解锁：需上一阶段评审关卡通过</div>
        {% endif %}
        {% for sp in si.substeps %}
        {% include "business/_substep.html" %}
        {% endfor %}
    </div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **步骤 6：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v`
预期：PASS（全部 5 个测试通过）。

- [ ] **步骤 7：Commit**

```bash
git add blueprints/business/routes.py templates/business/kanban.html templates/business/_substep.html tests/test_business.py
git commit -m "feat: 技术点看板详情与阶段关卡控制"
```

---

## 任务 8：业务管理——文档上传与下载

**文件：**
- 修改：`blueprints/business/routes.py`（新增 upload/download 路由）
- 追加：`tests/test_business.py`

- [ ] **步骤 1：追加失败测试到 tests/test_business.py**

```python
import io


def test_upload_and_download_document(client, db, app):
    from models import TechPoint, StageProgress
    tp = TechPoint(name="上传测试", direction="CT重建")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求评审")
    db.session.add(sp)
    db.session.commit()

    data = {
        "file": (io.BytesIO(b"fake pdf content"), "review.pdf"),
        "doc_type": "会议纪要",
    }
    resp = client.post(
        f"/business/stage/{sp.id}/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert resp.status_code == 200

    from models import StageDocument
    doc = StageDocument.query.first()
    assert doc is not None
    assert doc.original_name == "review.pdf"
    assert doc.stage_progress_id == sp.id

    # 下载
    resp = client.get(f"/business/doc/{doc.id}/download")
    assert resp.status_code == 200
    assert b"fake pdf content" in resp.data
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py::test_upload_and_download_document -v`
预期：FAIL（路由不存在）。

- [ ] **步骤 3：修改 blueprints/business/routes.py——新增 upload/download**

在 `routes.py` 顶部 import 区追加：

```python
import os
from flask import send_from_directory
from datetime import datetime
```

在文件末尾追加：

```python
@business_bp.route("/stage/<int:sp_id>/upload", methods=["POST"])
def upload_doc(sp_id):
    from models import StageProgress, StageDocument
    sp = StageProgress.query.get_or_404(sp_id)
    file = request.files.get("file")
    if not file or not file.filename:
        flash("请选择文件", "danger")
        return redirect(url_for("business.view_tech_point", id=sp.tech_point_id))
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    # 用 sp_id + 原始名避免冲突
    safe_name = f"sp{sp_id}_{file.filename}"
    save_path = os.path.join(upload_dir, safe_name)
    file.save(save_path)
    doc = StageDocument(
        stage_progress_id=sp.id,
        doc_type=request.form.get("doc_type", ""),
        file_path=safe_name,
        original_name=file.filename,
        uploaded_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.commit()
    flash(f"已上传 {file.filename}", "success")
    return redirect(url_for("business.view_tech_point", id=sp.tech_point_id))


@business_bp.route("/doc/<int:doc_id>/download")
def download_doc(doc_id):
    from models import StageDocument
    doc = StageDocument.query.get_or_404(doc_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir, doc.file_path, as_attachment=True,
        download_name=doc.original_name,
    )
```

并在 `routes.py` 顶部 import 中加入 `current_app`：

```python
from flask import (render_template, request, redirect, url_for, flash,
                   send_from_directory, current_app)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_business.py -v`
预期：PASS（全部 6 个测试通过）。

- [ ] **步骤 5：Commit**

```bash
git add blueprints/business/routes.py tests/test_business.py
git commit -m "feat: 子步骤文档上传与下载"
```

---

## 任务 9：团队管理——成员列表与新增

**文件：**
- 创建：`blueprints/team/routes.py`
- 修改：`blueprints/team/__init__.py`
- 创建：`templates/team/list.html`
- 创建：`templates/team/form.html`
- 创建：`tests/test_team.py`

- [ ] **步骤 1：编写失败测试 tests/test_team.py**

```python
def test_list_members_empty(client, db):
    resp = client.get("/team")
    assert resp.status_code == 200
    assert "成员".encode() in resp.data


def test_create_member(client, db):
    resp = client.post("/team/new", data={
        "name": "张三",
        "group": "CT重建组",
        "title": "高级算法工程师",
        "level": "A",
        "skills": "CT重建,深度学习",
        "responsible_for": "低剂量CT去噪",
        "joined_at": "2023-03-01",
    }, follow_redirects=True)
    assert resp.status_code == 200
    from models import Member
    m = Member.query.first()
    assert m.name == "张三"
    assert m.level == "A"


def test_filter_members_by_group(client, db):
    from models import Member
    db.session.add(Member(name="张三", group="CT重建组", level="A"))
    db.session.add(Member(name="李四", group="MRI组", level="B"))
    db.session.commit()
    resp = client.get("/team?group=CT重建组")
    assert b"\xe5\xbc\xa0\xe4\xb8\x89".decode() in resp.data.decode()  # 张三
    assert b"\xe6\x9d\x8e\xe5\x9b\x9b".decode() not in resp.data.decode()  # 李四
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_team.py -v`
预期：FAIL（404）。

- [ ] **步骤 3：编写 blueprints/team/routes.py**

```python
from flask import render_template, request, redirect, url_for, flash

from blueprints.team import team_bp
from extensions import db
from models import Member

GROUPS = ["CT重建组", "MRI组", "DR组", "超声组"]
LEVELS = ["A", "B", "C", "D"]
CAPABILITY_DIMENSIONS = ["算法能力", "工程能力", "临床理解", "创新研究", "沟通协作"]


@team_bp.route("/")
def list_members():
    group = request.args.get("group")
    level = request.args.get("level")
    query = Member.query
    if group:
        query = query.filter(Member.group == group)
    if level:
        query = query.filter(Member.level == level)
    members = query.order_by(Member.group, Member.name).all()
    return render_template(
        "team/list.html", members=members,
        groups=GROUPS, levels=LEVELS,
        filters={"group": group, "level": level},
    )


@team_bp.route("/new", methods=["GET", "POST"])
def new_member():
    if request.method == "POST":
        from datetime import date
        joined = request.form.get("joined_at") or None
        m = Member(
            name=request.form["name"],
            group=request.form.get("group", ""),
            title=request.form.get("title", ""),
            level=request.form.get("level", ""),
            skills=request.form.get("skills", ""),
            responsible_for=request.form.get("responsible_for", ""),
            joined_at=date.fromisoformat(joined) if joined else None,
        )
        db.session.add(m)
        db.session.commit()
        flash("成员已添加", "success")
        return redirect(url_for("team.view_member", id=m.id))
    return render_template("team/form.html", member=None, groups=GROUPS, levels=LEVELS)


@team_bp.route("/<int:id>")
def view_member(id):
    from models import CapabilityScore
    m = Member.query.get_or_404(id)
    scores = {s.dimension: s for s in m.capability_scores}
    return render_template(
        "team/radar.html", member=m,
        dimensions=CAPABILITY_DIMENSIONS,
        scores=scores,
        chart_labels=CAPABILITY_DIMENSIONS,
        chart_values=[scores[d].score if d in scores else 0 for d in CAPABILITY_DIMENSIONS],
    )


@team_bp.route("/<int:id>/score", methods=["GET", "POST"])
def edit_score(id):
    from models import CapabilityScore
    m = Member.query.get_or_404(id)
    if request.method == "POST":
        for dim in CAPABILITY_DIMENSIONS:
            val = request.form.get(dim, type=int)
            existing = CapabilityScore.query.filter_by(member_id=m.id, dimension=dim).first()
            if val is not None:
                if existing:
                    existing.score = val
                else:
                    db.session.add(CapabilityScore(member_id=m.id, dimension=dim, score=val))
        db.session.commit()
        flash("能力评分已更新", "success")
        return redirect(url_for("team.view_member", id=m.id))
    scores = {s.dimension: s.score for s in m.capability_scores}
    return render_template(
        "team/radar.html", member=m,
        dimensions=CAPABILITY_DIMENSIONS,
        scores=scores,
        editing=True,
        chart_labels=CAPABILITY_DIMENSIONS,
        chart_values=[scores.get(d, 0) for d in CAPABILITY_DIMENSIONS],
    )
```

- [ ] **步骤 4：修改 blueprints/team/__init__.py**

```python
from flask import Blueprint

team_bp = Blueprint("team", __name__)

from blueprints.team import routes  # noqa: E402,F401
```

- [ ] **步骤 5：编写 templates/team/list.html**

```html
{% extends "base.html" %}
{% block title %}团队管理{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>团队成员</h2>
    <a href="{{ url_for('team.new_member') }}" class="btn btn-primary">+ 添加成员</a>
</div>
<form method="get" class="row g-2 mb-3">
    <div class="col-auto">
        <select name="group" class="form-select form-select-sm">
            <option value="">全部组</option>
            {% for g in groups %}<option value="{{ g }}" {% if filters.group == g %}selected{% endif %}>{{ g }}</option>{% endfor %}
        </select>
    </div>
    <div class="col-auto">
        <select name="level" class="form-select form-select-sm">
            <option value="">全部评级</option>
            {% for l in levels %}<option value="{{ l }}" {% if filters.level == l %}selected{% endif %}>{{ l }}级</option>{% endfor %}
        </select>
    </div>
    <div class="col-auto"><button class="btn btn-outline-primary btn-sm">筛选</button></div>
</form>
<div class="row g-3">
    {% for m in members %}
    <div class="col-md-6 col-lg-4">
        <div class="card h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h6 class="card-title mb-0">{{ m.name }}</h6>
                        <div class="text-muted small">{{ m.group or '-' }} · {{ m.title or '-' }}</div>
                    </div>
                    <span class="badge bg-{{ 'success' if m.level == 'A' else 'warning' if m.level == 'B' else 'secondary' }}">{{ m.level }}级</span>
                </div>
                {% if m.skills %}
                <div class="mt-2">
                    {% for sk in m.skills.split(',') %}
                    <span class="badge bg-info text-dark">{{ sk.strip() }}</span>
                    {% endfor %}
                </div>
                {% endif %}
                {% if m.responsible_for %}<div class="small text-muted mt-2">负责: {{ m.responsible_for }}</div>{% endif %}
                <a href="{{ url_for('team.view_member', id=m.id) }}" class="btn btn-sm btn-outline-primary mt-2">查看雷达图</a>
            </div>
        </div>
    </div>
    {% else %}
    <div class="col-12 text-center text-muted py-4">暂无成员</div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **步骤 6：编写 templates/team/form.html**

```html
{% extends "base.html" %}
{% block title %}{{ '编辑' if member else '添加' }}成员{% endblock %}
{% block content %}
<h2 class="mb-4">{{ '编辑' if member else '添加' }}成员</h2>
<form method="post">
    <div class="mb-3">
        <label class="form-label">姓名 *</label>
        <input type="text" name="name" class="form-control" required value="{{ member.name if member else '' }}">
    </div>
    <div class="row mb-3">
        <div class="col">
            <label class="form-label">所属组</label>
            <select name="group" class="form-select">
                <option value="">-</option>
                {% for g in groups %}<option value="{{ g }}" {% if member and member.group == g %}selected{% endif %}>{{ g }}</option>{% endfor %}
            </select>
        </div>
        <div class="col">
            <label class="form-label">评级</label>
            <select name="level" class="form-select">
                {% for l in levels %}<option value="{{ l }}" {% if member and member.level == l %}selected{% endif %}>{{ l }}级</option>{% endfor %}
            </select>
        </div>
    </div>
    <div class="mb-3"><label class="form-label">职位</label><input type="text" name="title" class="form-control" value="{{ member.title if member else '' }}"></div>
    <div class="mb-3"><label class="form-label">技能标签（逗号分隔）</label><input type="text" name="skills" class="form-control" value="{{ member.skills if member else '' }}"></div>
    <div class="mb-3"><label class="form-label">负责的技术点</label><input type="text" name="responsible_for" class="form-control" value="{{ member.responsible_for if member else '' }}"></div>
    <div class="mb-3"><label class="form-label">入职日期</label><input type="date" name="joined_at" class="form-control" value="{{ member.joined_at.strftime('%Y-%m-%d') if member and member.joined_at else '' }}"></div>
    <button class="btn btn-primary">保存</button>
    <a href="{{ url_for('team.list_members') }}" class="btn btn-outline-secondary">取消</a>
</form>
{% endblock %}
```

- [ ] **步骤 7：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_team.py -v`
预期：PASS（3 个测试通过）。

- [ ] **步骤 8：Commit**

```bash
git add blueprints/team/ templates/team/list.html templates/team/form.html tests/test_team.py
git commit -m "feat: 团队管理成员列表与新增"
```

---

## 任务 10：团队管理——雷达图详情与能力评分

**文件：**
- 创建：`templates/team/radar.html`
- 追加：`tests/test_team.py`

- [ ] **步骤 1：追加失败测试到 tests/test_team.py**

```python
def test_view_member_radar(client, db):
    from models import Member
    m = Member(name="张三", group="CT重建组", level="A")
    db.session.add(m)
    db.session.commit()
    resp = client.get(f"/team/{m.id}")
    assert resp.status_code == 200
    assert "雷达图".encode() in resp.data or "chart".encode() in resp.data.lower()
    assert b"算法能力" in resp.data


def test_edit_member_score(client, db):
    from models import Member, CapabilityScore
    m = Member(name="李四", group="MRI组", level="B")
    db.session.add(m)
    db.session.commit()
    resp = client.post(f"/team/{m.id}/score", data={
        "算法能力": "8", "工程能力": "7", "临床理解": "6",
        "创新研究": "5", "沟通协作": "9",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert CapabilityScore.query.filter_by(member_id=m.id).count() == 5
    s = CapabilityScore.query.filter_by(member_id=m.id, dimension="算法能力").first()
    assert s.score == 8
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_team.py -v`
预期：FAIL（radar.html 不存在）。

- [ ] **步骤 3：编写 templates/team/radar.html**

```html
{% extends "base.html" %}
{% block title %}{{ member.name }}{% endblock %}
{% block content %}
<div class="row">
    <div class="col-md-5">
        <h2>{{ member.name }}
            <span class="badge bg-{{ 'success' if member.level == 'A' else 'warning' if member.level == 'B' else 'secondary' }}">{{ member.level }}级</span>
        </h2>
        <div class="text-muted mb-2">{{ member.group or '-' }} · {{ member.title or '-' }}</div>
        {% if member.skills %}
        <div class="mb-2">
            {% for sk in member.skills.split(',') %}<span class="badge bg-info text-dark">{{ sk.strip() }}</span>{% endfor %}
        </div>
        {% endif %}
        {% if member.responsible_for %}<div class="small">负责: {{ member.responsible_for }}</div>{% endif %}

        <h6 class="mt-4 mb-2">能力评分</h6>
        <form method="post">
            {% for dim in dimensions %}
            <div class="mb-2">
                <label class="form-label small mb-1">{{ dim }}</label>
                <input type="range" class="form-range" name="{{ dim }}" min="0" max="10"
                       value="{{ scores[dim] if scores is mapping and dim in scores else (scores[dim] if scores and dim in scores else 0) }}"
                       oninput="this.nextElementSibling.textContent=this.value">
                <span class="small text-muted">
                    {{ scores[dim] if scores is mapping and dim in scores else (scores[dim] if scores and dim in scores else 0) }}
                </span>
            </div>
            {% endfor %}
            <button class="btn btn-primary btn-sm">保存评分</button>
        </form>
    </div>
    <div class="col-md-7">
        <div class="radar-container">
            <canvas id="radarChart"></canvas>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('radarChart');
new Chart(ctx, {
    type: 'radar',
    data: {
        labels: {{ chart_labels | tojson }},
        datasets: [{
            label: '能力评估',
            data: {{ chart_values | tojson }},
            fill: true,
            backgroundColor: 'rgba(13,110,253,0.2)',
            borderColor: 'rgb(13,110,253)',
            pointBackgroundColor: 'rgb(13,110,253)',
        }]
    },
    options: {
        scales: { r: { beginAtZero: true, max: 10, suggestedMin: 0 } }
    }
});
</script>
{% endblock %}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_team.py -v`
预期：PASS（全部 5 个测试通过）。

- [ ] **步骤 5：Commit**

```bash
git add templates/team/radar.html tests/test_team.py
git commit -m "feat: 成员能力雷达图与评分"
```

---

## 任务 11：流程制度——问题记录

**文件：**
- 创建：`blueprints/process/routes.py`
- 修改：`blueprints/process/__init__.py`
- 创建：`templates/process/issue_list.html`
- 创建：`templates/process/issue_form.html`
- 创建：`tests/test_process.py`

- [ ] **步骤 1：编写失败测试 tests/test_process.py**

```python
def test_list_issues_empty(client, db):
    resp = client.get("/process/issues")
    assert resp.status_code == 200
    assert "问题".encode() in resp.data


def test_create_issue(client, db):
    resp = client.post("/process/issues/new", data={
        "title": "文档评审不及时",
        "category": "流程问题",
        "severity": "高",
        "status": "待处理",
        "description": "导致方案预研返工",
    }, follow_redirects=True)
    assert resp.status_code == 200
    from models import Issue
    i = Issue.query.first()
    assert i.title == "文档评审不及时"
    assert i.status == "待处理"


def test_edit_issue_link_policy(client, db):
    from models import Issue, Policy
    p = Policy(title="评审制度", version="1.0")
    db.session.add(p)
    db.session.commit()
    i = Issue(title="问题1", category="流程问题", severity="高")
    db.session.add(i)
    db.session.commit()
    resp = client.post(f"/process/issues/{i.id}", data={
        "title": "问题1",
        "category": "流程问题",
        "severity": "高",
        "status": "已建制度",
        "linked_policy_id": str(p.id),
        "description": "已解决",
    }, follow_redirects=True)
    assert resp.status_code == 200
    db.session.refresh(i)
    assert i.linked_policy_id == p.id
    assert i.status == "已建制度"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_process.py -v`
预期：FAIL（404）。

- [ ] **步骤 3：编写 blueprints/process/routes.py**

```python
from flask import render_template, request, redirect, url_for, flash

from blueprints.process import process_bp
from extensions import db
from models import Issue, Policy

ISSUE_CATEGORIES = ["流程问题", "质量问题", "协作问题", "其他"]
SEVERITIES = ["高", "中", "低"]
ISSUE_STATUSES = ["待处理", "已建制度", "已关闭"]


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
    return render_template(
        "process/issue_list.html", issues=issues,
        categories=ISSUE_CATEGORIES, statuses=ISSUE_STATUSES,
        filters={"category": category, "status": status},
    )


@process_bp.route("/issues/new", methods=["GET", "POST"])
def new_issue():
    if request.method == "POST":
        i = Issue(
            title=request.form["title"],
            category=request.form.get("category", ""),
            severity=request.form.get("severity", "中"),
            status=request.form.get("status", "待处理"),
            description=request.form.get("description", ""),
            linked_policy_id=request.form.get("linked_policy_id", type=int),
        )
        db.session.add(i)
        db.session.commit()
        flash("问题已记录", "success")
        return redirect(url_for("process.list_issues"))
    policies = Policy.query.order_by(Policy.title).all()
    return render_template(
        "process/issue_form.html", issue=None,
        categories=ISSUE_CATEGORIES, severities=SEVERITIES,
        statuses=ISSUE_STATUSES, policies=policies,
    )


@process_bp.route("/issues/<int:id>", methods=["GET", "POST"])
def edit_issue(id):
    i = Issue.query.get_or_404(id)
    if request.method == "POST":
        i.title = request.form["title"]
        i.category = request.form.get("category", "")
        i.severity = request.form.get("severity", "中")
        i.status = request.form.get("status", "待处理")
        i.description = request.form.get("description", "")
        i.linked_policy_id = request.form.get("linked_policy_id", type=int)
        db.session.commit()
        flash("问题已更新", "success")
        return redirect(url_for("process.list_issues"))
    policies = Policy.query.order_by(Policy.title).all()
    return render_template(
        "process/issue_form.html", issue=i,
        categories=ISSUE_CATEGORIES, severities=SEVERITIES,
        statuses=ISSUE_STATUSES, policies=policies,
    )


@process_bp.route("/policies")
def list_policies():
    policies = Policy.query.order_by(Policy.published_at.desc()).all()
    return render_template("process/policy_list.html", policies=policies)


@process_bp.route("/policies/new", methods=["GET", "POST"])
def new_policy():
    if request.method == "POST":
        p = Policy(
            title=request.form["title"],
            version=request.form.get("version", "1.0"),
            content=request.form.get("content", ""),
        )
        db.session.add(p)
        db.session.commit()
        flash("制度已发布", "success")
        return redirect(url_for("process.list_policies"))
    return render_template("process/policy_form.html", policy=None)


@process_bp.route("/policies/<int:id>", methods=["GET", "POST"])
def edit_policy(id):
    p = Policy.query.get_or_404(id)
    if request.method == "POST":
        p.title = request.form["title"]
        p.version = request.form.get("version", "1.0")
        p.content = request.form.get("content", "")
        db.session.commit()
        flash("制度已更新", "success")
        return redirect(url_for("process.list_policies"))
    return render_template("process/policy_form.html", policy=p)
```

- [ ] **步骤 4：修改 blueprints/process/__init__.py**

```python
from flask import Blueprint

process_bp = Blueprint("process", __name__)

from blueprints.process import routes  # noqa: E402,F401
```

- [ ] **步骤 5：编写 templates/process/issue_list.html**

```html
{% extends "base.html" %}
{% block title %}流程制度 — 问题记录{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <div>
        <ul class="nav nav-tabs">
            <li class="nav-item"><a class="nav-link active" href="{{ url_for('process.list_issues') }}">问题记录</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('process.list_policies') }}">制度文档</a></li>
        </ul>
    </div>
    <a href="{{ url_for('process.new_issue') }}" class="btn btn-primary">+ 记录问题</a>
</div>
<form method="get" class="row g-2 mb-3">
    <div class="col-auto">
        <select name="category" class="form-select form-select-sm">
            <option value="">全部分类</option>
            {% for c in categories %}<option value="{{ c }}" {% if filters.category == c %}selected{% endif %}>{{ c }}</option>{% endfor %}
        </select>
    </div>
    <div class="col-auto">
        <select name="status" class="form-select form-select-sm">
            <option value="">全部状态</option>
            {% for s in statuses %}<option value="{{ s }}" {% if filters.status == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
        </select>
    </div>
    <div class="col-auto"><button class="btn btn-outline-primary btn-sm">筛选</button></div>
</form>
<table class="table table-hover align-middle">
    <thead class="table-light">
        <tr><th>问题描述</th><th>分类</th><th>严重度</th><th>关联制度</th><th>状态</th><th></th></tr>
    </thead>
    <tbody>
        {% for i in issues %}
        <tr>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}">{{ i.title }}</a></td>
            <td><span class="badge bg-warning text-dark">{{ i.category }}</span></td>
            <td><span class="text-{{ 'danger' if i.severity == '高' else 'warning' if i.severity == '中' else 'secondary' }}">● {{ i.severity }}</span></td>
            <td>{% if i.policy %}<a href="{{ url_for('process.edit_policy', id=i.policy.id) }}">{{ i.policy.title }}</a>{% else %}-{% endif %}</td>
            <td><span class="badge bg-{{ 'success' if i.status == '已建制度' else 'secondary' if i.status == '已关闭' else 'warning' }}">{{ i.status }}</span></td>
            <td><a href="{{ url_for('process.edit_issue', id=i.id) }}" class="btn btn-sm btn-outline-secondary">编辑</a></td>
        </tr>
        {% else %}
        <tr><td colspan="6" class="text-center text-muted py-4">暂无问题记录</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

- [ ] **步骤 6：编写 templates/process/issue_form.html**

```html
{% extends "base.html" %}
{% block title %}{{ '编辑' if issue else '记录' }}问题{% endblock %}
{% block content %}
<h2 class="mb-4">{{ '编辑' if issue else '记录' }}问题</h2>
<form method="post">
    <div class="mb-3"><label class="form-label">问题描述 *</label><input type="text" name="title" class="form-control" required value="{{ issue.title if issue else '' }}"></div>
    <div class="row mb-3">
        <div class="col">
            <label class="form-label">分类</label>
            <select name="category" class="form-select">
                {% for c in categories %}<option value="{{ c }}" {% if issue and issue.category == c %}selected{% endif %}>{{ c }}</option>{% endfor %}
            </select>
        </div>
        <div class="col">
            <label class="form-label">严重度</label>
            <select name="severity" class="form-select">
                {% for s in severities %}<option value="{{ s }}" {% if issue and issue.severity == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
            </select>
        </div>
        <div class="col">
            <label class="form-label">状态</label>
            <select name="status" class="form-select">
                {% for s in statuses %}<option value="{{ s }}" {% if issue and issue.status == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
            </select>
        </div>
    </div>
    <div class="mb-3">
        <label class="form-label">关联制度</label>
        <select name="linked_policy_id" class="form-select">
            <option value="">无</option>
            {% for p in policies %}<option value="{{ p.id }}" {% if issue and issue.linked_policy_id == p.id %}selected{% endif %}>{{ p.title }}</option>{% endfor %}
        </select>
    </div>
    <div class="mb-3"><label class="form-label">详细描述</label><textarea name="description" class="form-control" rows="4">{{ issue.description if issue else '' }}</textarea></div>
    <button class="btn btn-primary">保存</button>
    <a href="{{ url_for('process.list_issues') }}" class="btn btn-outline-secondary">取消</a>
</form>
{% endblock %}
```

- [ ] **步骤 7：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_process.py -v`
预期：PASS（3 个测试通过）。

- [ ] **步骤 8：Commit**

```bash
git add blueprints/process/ templates/process/issue_list.html templates/process/issue_form.html tests/test_process.py
git commit -m "feat: 流程制度问题记录与制度关联"
```

---

## 任务 12：流程制度——制度文档库

**文件：**
- 创建：`templates/process/policy_list.html`
- 创建：`templates/process/policy_form.html`
- 追加：`tests/test_process.py`

- [ ] **步骤 1：追加失败测试到 tests/test_process.py**

```python
def test_list_policies_empty(client, db):
    resp = client.get("/process/policies")
    assert resp.status_code == 200
    assert "制度".encode() in resp.data


def test_create_policy_and_view_linked_issues(client, db):
    from models import Issue
    resp = client.post("/process/policies/new", data={
        "title": "文档评审制度",
        "version": "1.0",
        "content": "所有评审文档需在评审后3个工作日内归档...",
    }, follow_redirects=True)
    assert resp.status_code == 200
    from models import Policy
    p = Policy.query.first()
    assert p.title == "文档评审制度"

    # 关联一个问题，验证制度详情页展示
    i = Issue(title="评审不及时", category="流程问题", linked_policy_id=p.id)
    db.session.add(i)
    db.session.commit()
    resp = client.get(f"/process/policies/{p.id}")
    assert resp.status_code == 200
    assert b"\xe8\xaf\x84\xe5\xae\xa1\xe4\xb8\x8d\xe5\x8f\x8a\xe6\x97\xb6".decode() in resp.data.decode()  # 评审不及时
```

- [ ] **步骤 2：运行测试验证失败**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_process.py::test_create_policy_and_view_linked_issues -v`
预期：FAIL（policy_form.html 不存在）。

- [ ] **步骤 3：编写 templates/process/policy_list.html**

```html
{% extends "base.html" %}
{% block title %}流程制度 — 制度文档{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <ul class="nav nav-tabs">
        <li class="nav-item"><a class="nav-link" href="{{ url_for('process.list_issues') }}">问题记录</a></li>
        <li class="nav-item"><a class="nav-link active" href="{{ url_for('process.list_policies') }}">制度文档</a></li>
    </ul>
    <a href="{{ url_for('process.new_policy') }}" class="btn btn-primary">+ 新建制度</a>
</div>
<div class="list-group">
    {% for p in policies %}
    <a href="{{ url_for('process.edit_policy', id=p.id) }}" class="list-group-item list-group-item-action">
        <div class="d-flex justify-content-between">
            <div>
                <h6 class="mb-1">📄 {{ p.title }}</h6>
                <div class="small text-muted">v{{ p.version }} · 发布于 {{ p.published_at.strftime('%Y-%m-%d') if p.published_at else '' }} · 关联问题: {{ p.issues.count() }}个</div>
            </div>
            <span class="badge bg-primary rounded-pill">{{ p.issues.count() }}</span>
        </div>
    </a>
    {% else %}
    <div class="list-group-item text-center text-muted py-4">暂无制度文档</div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **步骤 4：编写 templates/process/policy_form.html**

```html
{% extends "base.html" %}
{% block title %}{{ '编辑' if policy else '新建' }}制度{% endblock %}
{% block content %}
<h2 class="mb-4">{{ '编辑' if policy else '新建' }}制度</h2>
<form method="post">
    <div class="row mb-3">
        <div class="col-8"><label class="form-label">制度名称 *</label><input type="text" name="title" class="form-control" required value="{{ policy.title if policy else '' }}"></div>
        <div class="col-4"><label class="form-label">版本</label><input type="text" name="version" class="form-control" value="{{ policy.version if policy else '1.0' }}"></div>
    </div>
    <div class="mb-3"><label class="form-label">制度内容</label><textarea name="content" class="form-control" rows="10">{{ policy.content if policy else '' }}</textarea></div>
    <button class="btn btn-primary">保存</button>
    <a href="{{ url_for('process.list_policies') }}" class="btn btn-outline-secondary">取消</a>
</form>

{% if policy %}
<div class="mt-4">
    <h6>关联问题（{{ policy.issues.count() }}）</h6>
    <ul class="list-group">
        {% for i in policy.issues %}
        <li class="list-group-item d-flex justify-content-between">
            <a href="{{ url_for('process.edit_issue', id=i.id) }}">{{ i.title }}</a>
            <span class="badge bg-{{ 'success' if i.status == '已建制度' else 'warning' }}">{{ i.status }}</span>
        </li>
        {% else %}
        <li class="list-group-item text-muted small">暂无关联问题</li>
        {% endfor %}
    </ul>
</div>
{% endif %}
{% endblock %}
```

- [ ] **步骤 5：运行测试验证通过**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/test_process.py -v`
预期：PASS（全部 5 个测试通过）。

- [ ] **步骤 6：Commit**

```bash
git add templates/process/policy_list.html templates/process/policy_form.html tests/test_process.py
git commit -m "feat: 制度文档库与关联问题展示"
```

---

## 任务 13：全量验证与种子数据

**文件：**
- 创建：`seed.py`（可选种子数据脚本）
- 创建：`README.md`（运行说明）

- [ ] **步骤 1：运行全部测试**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/ -v`
预期：全部测试 PASS（models 8 + dashboard 2 + business 6 + team 5 + process 5 = 26 个）。

- [ ] **步骤 2：手动启动应用验证**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" start.py`
预期：控制台输出 `Running on http://127.0.0.1:5000`，浏览器打开后：
- 仪表盘显示统计为 0
- 业务管理可新增技术点，新增后看板显示 4 阶段 22 子步骤
- 团队管理可添加成员并查看雷达图
- 流程制度可记录问题、新建制度并双向关联

按 Ctrl+C 停止。

- [ ] **步骤 3：编写 seed.py（示例数据，便于首次体验）**

```python
"""种子数据脚本：填充示例数据便于首次体验。
运行：python seed.py
"""
from datetime import date

from start import app
from extensions import db
from models import (
    TechPoint, StageProgress, Member, CapabilityScore, Issue, Policy,
)
from blueprints.business.process_template import STANDARD_PROCESS


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 技术点 + 标准流程子步骤
        samples = [
            ("低剂量CT去噪算法", "CT重建", "张三"),
            ("MRI运动伪影校正", "MRI", "李四"),
            ("DR胸部结节检测", "DR", "王五"),
        ]
        for name, direction, owner in samples:
            tp = TechPoint(name=name, direction=direction, owner=owner, current_stage=1)
            db.session.add(tp)
            db.session.flush()
            for sdef in STANDARD_PROCESS:
                for step in sdef["steps"]:
                    db.session.add(StageProgress(
                        tech_point_id=tp.id, stage=sdef["stage"], sub_step=step,
                    ))
        db.session.commit()

        # 成员 + 能力评分
        dims = ["算法能力", "工程能力", "临床理解", "创新研究", "沟通协作"]
        members = [
            ("张三", "CT重建组", "高级算法工程师", "A", [9, 8, 7, 6, 8]),
            ("李四", "MRI组", "算法工程师", "B", [7, 7, 6, 5, 7]),
        ]
        for name, group, title, level, scores in members:
            m = Member(name=name, group=group, title=title, level=level,
                       skills=",".join(dims[:2]), responsible_for=name,
                       joined_at=date(2023, 3, 1))
            db.session.add(m)
            db.session.flush()
            for d, sc in zip(dims, scores):
                db.session.add(CapabilityScore(member_id=m.id, dimension=d, score=sc))
        db.session.commit()

        # 制度 + 问题
        p = Policy(title="文档评审制度", version="1.0",
                   content="评审后3个工作日内归档评审材料与会议纪要。")
        db.session.add(p)
        db.session.flush()
        db.session.add(Issue(
            title="预研文档评审不及时", category="流程问题", severity="高",
            status="已建制度", linked_policy_id=p.id,
            description="导致方案预研阶段反复返工。",
        ))
        db.session.add(Issue(
            title="跨组评审缺少统一评分标准", category="流程问题", severity="中",
            status="待处理",
        ))
        db.session.commit()
        print("种子数据已填充：3个技术点、2个成员、1个制度、2个问题。")


if __name__ == "__main__":
    seed()
```

- [ ] **步骤 4：编写 README.md**

```markdown
# 放射影像算法研究部管理系统

本地单用户 Web 应用，作为放射影像算法研究部经理的日常管理抓手。

## 运行

```bash
# 必须使用 conda app 环境的 python
"D:\ProgramData\anaconda3\envs\app\python.exe" start.py
```

浏览器打开 http://localhost:5000

## 首次体验（填充示例数据）

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" seed.py
```

## 测试

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/ -v
```

## 功能模块

- **仪表盘**：统计卡片 + 最近技术点 + 待处理问题
- **业务管理**：技术点按 TRL2-TRL7 标准流程跟踪，看板视图含阶段评审关卡
- **团队管理**：成员列表 + 5维度能力雷达图（Chart.js）
- **流程制度**：问题记录与制度文档双向关联

## 数据

SQLite 数据库文件 `rad_research.db` 位于项目根目录，上传文档存于 `uploads/`。
```

- [ ] **步骤 5：填充种子数据并再次启动验证**

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" seed.py`
预期：输出"种子数据已填充..."。

运行：`"D:\ProgramData\anaconda3\envs\app\python.exe" start.py`
预期：浏览器中仪表盘显示技术点 3、成员 2、待处理问题 1，各模块数据可见。Ctrl+C 停止。

- [ ] **步骤 6：Commit**

```bash
git add seed.py README.md
git commit -m "feat: 种子数据脚本与运行说明"
```

---

## 自检结果

**1. 规格覆盖度：**
- ✅ 业务管理（TRL流程跟踪、4阶段看板、子步骤、文档上传、评审关卡）→ 任务 3,6,7,8
- ✅ 团队管理（人员盘点、能力雷达图、5维度评分）→ 任务 9,10
- ✅ 流程制度（问题记录、制度文档、双向关联）→ 任务 11,12
- ✅ 仪表盘（统计卡片、最近更新、待处理问题）→ 任务 5
- ✅ 6个数据模型 → 任务 2
- ✅ 标准流程模板（4阶段22子步骤、3个关卡）→ 任务 3
- ✅ 导航结构（顶部4入口）→ 任务 4
- ✅ Bootstrap + Chart.js CDN → 任务 4,10
- ✅ `python start.py` 启动 → 任务 4,13

**2. 占位符扫描：** 无 TODO/待定，每步含完整代码与命令。

**3. 类型一致性：** 模型属性名（`stage_progresses`/`documents`/`capability_scores`/`issues`/`policy`）在测试与路由中一致；模板变量（`stages_info`/`chart_values`/`filters`）在路由与模板中对应；路由端点名（`business.view_tech_point`/`team.view_member`/`process.list_issues`/`process.list_policies`）在 base.html 与各处引用一致。

**已知约束：**
- 测试中 `conftest.py` 复用 `start.create_app()`，故任务 4 之前测试无法运行——这是按依赖顺序编排的结果（任务 4 后 conftest 可用，任务 5 起测试转绿）。
- 任务 4 步骤 4 的验证为 import 级别，因 dashboard.index 等端点在任务 5 才定义；属预期。

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-06-21-radresearch-management-system.md`。两种执行方式：

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

选哪种方式？
