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
    employee_id = db.Column(db.String(20))
    rank = db.Column(db.String(20))
    group = db.Column(db.String(50))
    title = db.Column(db.String(50))
    level = db.Column(db.String(10))
    skills = db.Column(db.String(500))
    responsible_for = db.Column(db.String(500))
    joined_at = db.Column(db.Date)


class CapabilityDimension(db.Model):
    """能力评估维度"""
    __tablename__ = "capability_dimension"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


class CapabilityScore(db.Model):
    """能力评分——按维度评分"""
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


class IssueDocument(db.Model):
    """问题附件——关联 Issue 的文档/材料"""
    __tablename__ = "issue_document"
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(
        db.Integer, db.ForeignKey("issue.id"), nullable=False
    )
    doc_type = db.Column(db.String(50))
    file_path = db.Column(db.String(500))
    original_name = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    issue = db.relationship("Issue", backref="documents")
