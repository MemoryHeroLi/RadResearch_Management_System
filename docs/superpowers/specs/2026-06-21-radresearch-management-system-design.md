# 放射影像算法研究部管理系统 — 设计规格

> 日期: 2026-06-21 | 状态: 设计完成，待实现

## 1. 项目概述

### 1.1 背景

公司从事放射影像产品研发，放射影像算法研究部负责高级功能和图像的预研与产品化。部门经理（新任）需要一个管理系统作为日常管理的"抓手"。

### 1.2 使用对象

**仅部门经理本人**（单用户系统），无需权限控制和用户认证。

### 1.3 核心目标

- 跟踪部门所有预研技术点从 TRL2 到 TRL7 的完整研发流程
- 盘点团队 ~20 人 / 4 个技术组的能力分布
- 记录日常问题并建立流程制度

## 2. 技术方案

| 项 | 选择 | 理由 |
|----|------|------|
| **Web 框架** | Flask 2.x + Jinja2 | 轻量、适合单人系统、零前端构建 |
| **数据库** | SQLite（单文件 `rad_research.db`） | 零配置、本地运行、数据在用户电脑上 |
| **ORM** | SQLAlchemy | Flask 生态标配，模型清晰 |
| **CSS 框架** | Bootstrap 5（CDN） | 简洁实用风，组件丰富，无需构建 |
| **图表** | Chart.js（CDN） | 雷达图、进度图 |
| **部署** | `python start.py`，浏览器访问 `localhost:5000` | 本地单机运行 |

## 3. 项目结构

```
rad_research/
├── start.py                  # 应用入口
├── config.py                 # 配置（数据库路径、上传目录等）
├── extensions.py             # Flask 扩展初始化（SQLAlchemy）
├── models.py                 # 所有数据模型（6个表）
├── blueprints/
│   ├── dashboard/            # 仪表盘（首页）
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── business/             # 业务管理
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── team/                 # 团队管理
│   │   ├── __init__.py
│   │   └── routes.py
│   └── process/              # 流程制度
│       ├── __init__.py
│       └── routes.py
├── templates/
│   ├── base.html             # 基础布局（导航栏、Bootstrap 壳）
│   ├── dashboard/
│   │   └── index.html        # 仪表盘首页
│   ├── business/
│   │   ├── list.html         # 技术点列表
│   │   ├── kanban.html       # 技术点看板详情
│   │   └── form.html         # 新增/编辑技术点
│   ├── team/
│   │   ├── list.html         # 成员列表
│   │   └── radar.html        # 成员雷达图详情
│   └── process/
│       ├── issue_list.html   # 问题列表
│       ├── issue_form.html   # 新增/编辑问题
│       ├── policy_list.html  # 制度列表
│       └── policy_form.html  # 新建/编辑制度
├── static/
│   └── style.css             # 少量自定义样式
└── uploads/                  # 文档上传目录
```

## 4. 数据模型

### 4.1 业务管理（3个表）

```python
class TechPoint(db.Model):
    """技术点"""
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)           # 技术点名称
    direction = Column(String(50), nullable=False)        # 技术方向: CT重建/MRI/DR/超声
    current_stage = Column(Integer, default=1)            # 当前阶段: 1-4
    status = Column(String(20), default='进行中')          # 进行中/已完成/暂停
    owner = Column(String(50))                             # 负责人
    description = Column(Text)                             # 详细描述
    source = Column(Text)                                  # 需求来源
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StageProgress(db.Model):
    """阶段进展——每个阶段下的子步骤"""
    id = Column(Integer, primary_key=True)
    tech_point_id = Column(Integer, ForeignKey('tech_point.id'), nullable=False)
    stage = Column(Integer, nullable=False)               # 阶段编号: 1-4
    sub_step = Column(String(200), nullable=False)         # 子步骤名称
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    notes = Column(Text)
    tech_point = relationship('TechPoint', backref='stage_progresses')

class StageDocument(db.Model):
    """阶段文档——子步骤关联的文档/材料"""
    id = Column(Integer, primary_key=True)
    stage_progress_id = Column(Integer, ForeignKey('stage_progress.id'), nullable=False)
    doc_type = Column(String(50))                          # 评审材料/会议纪要/PPT/其他
    file_path = Column(String(500))                        # 上传文件路径
    original_name = Column(String(200))                    # 原始文件名
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    stage_progress = relationship('StageProgress', backref='documents')
```

### 4.2 团队管理（2个表）

```python
class Member(db.Model):
    """团队成员"""
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    group = Column(String(50))                              # CT重建组/MRI组/DR组/超声组
    title = Column(String(50))                              # 职位
    level = Column(String(10))                              # A/B/C/D
    skills = Column(String(500))                            # 技能标签（逗号分隔）
    responsible_for = Column(String(500))                   # 负责的技术点
    joined_at = Column(Date)

class CapabilityScore(db.Model):
    """能力评分——5个评估维度"""
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    dimension = Column(String(50), nullable=False)          # 算法能力/工程能力/临床理解/创新研究/沟通协作
    score = Column(Integer, nullable=False)                 # 1-10
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    member = relationship('Member', backref='capability_scores')
```

### 4.3 流程制度（2个表）

```python
class Issue(db.Model):
    """问题记录"""
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(20))                           # 流程问题/质量问题/协作问题/其他
    severity = Column(String(10))                           # 高/中/低
    status = Column(String(20), default='待处理')            # 待处理/已建制度/已关闭
    linked_policy_id = Column(Integer, ForeignKey('policy.id'), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    policy = relationship('Policy', backref='issues')

class Policy(db.Model):
    """流程制度"""
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    version = Column(String(20), default='1.0')
    content = Column(Text)                                   # 制度内容（富文本/纯文本）
    file_path = Column(String(500))                          # 附件路径
    published_at = Column(DateTime, default=datetime.utcnow)
```

### 4.4 实体关系图

```
TechPoint 1──N StageProgress 1──N StageDocument
Member 1──N CapabilityScore
Policy 1──N Issue
```

## 5. 页面与路由设计

### 5.1 导航结构

顶部导航栏：**仪表盘 | 业务管理 | 团队管理 | 流程制度**

### 5.2 路由表

| 路由 | 方法 | 蓝图 | 说明 |
|------|------|------|------|
| `/` | GET | dashboard | 仪表盘首页 |
| `/business` | GET | business | 技术点列表 |
| `/business/new` | GET/POST | business | 新增技术点 |
| `/business/<id>` | GET | business | 技术点看板详情 |
| `/business/<id>/edit` | GET/POST | business | 编辑技术点 |
| `/business/stage/<id>/toggle` | POST | business | 切换子步骤完成状态 |
| `/business/stage/<id>/upload` | POST | business | 上传子步骤文档 |
| `/team` | GET | team | 成员列表 |
| `/team/new` | GET/POST | team | 添加成员 |
| `/team/<id>` | GET | team | 成员雷达图详情 |
| `/team/<id>/score` | GET/POST | team | 编辑能力评分 |
| `/process/issues` | GET | process | 问题列表 |
| `/process/issues/new` | GET/POST | process | 记录问题 |
| `/process/issues/<id>` | GET/POST | process | 编辑问题 |
| `/process/policies` | GET | process | 制度列表 |
| `/process/policies/new` | GET/POST | process | 新建制度 |
| `/process/policies/<id>` | GET/POST | process | 编辑制度 |

## 6. 关键交互逻辑

### 6.1 技术点生命周期

1. 新建技术点时，自动按标准流程创建 4 个阶段的所有子步骤（预设模板）
2. 每个子步骤可独立勾选完成、添加备注、上传文档
3. 阶段评审节点（需求评审/功能构思评审/TRL6评审）是**强制性关卡**——未通过则下一阶段灰色锁定
4. 阶段4（版本开发）的子步骤独立展示：方案澄清→功能开发→功能测试→临床验证→TRL7验收

### 6.2 标准流程模板（预置子步骤）

**阶段1-需求收集：** 需求导入 → 需求评审
**阶段2-功能构思：** 临床调研 → 痛点分析 → 需求提炼 → 竞品分析 → 方案构思 → 可行性分析 → 功能构思评审
**阶段3-方案预研：** 技术调研 → 方案设计及评审 → 任务分解 → 子任务开发 → 仿真验证 → TRL6预研验收 → 文档撰写 → 文档评审
**阶段4-版本开发：** 方案澄清（系统方案+算法方案）→ 功能开发（参数提交+联调+性能验证）→ 功能测试（BUG解决）→ 临床验证 → TRL7验收

### 6.3 能力评估维度

5个固定维度，每项 1-10 分：算法能力、工程能力、临床理解、创新研究、沟通协作

### 6.4 问题→制度关联

- 问题状态：待处理 → 已建制度 → 已关闭
- 当某个问题被解决并建立制度后，通过 `linked_policy_id` 关联
- 制度详情页展示"关联问题列表"，问题详情页展示"关联制度"

## 7. 非功能需求

- **性能**：单用户本地访问，无并发压力
- **数据安全**：SQLite 文件存储在本地，用户自行备份
- **可扩展**：Flask Blueprint 模块化，后续可拆分或扩展
- **浏览器兼容**：Chrome/Edge 最新版本

## 8. 不在范围内

- 用户认证/权限系统（单用户）
- 邮件通知/消息推送
- 移动端适配
- 数据导出/导入
- 自动化测试（可在实现阶段补充）

## 9. 实现策略

- 三个阶段实现：**数据层**（models + 种子数据）→ **路由层**（routes + 模板）→ **打磨**（样式微调 + 验证）
- 每个模块独立 Blueprint，可并行或顺序开发
- 优先完成仪表盘和业务管理（核心），再做团队管理和流程制度
