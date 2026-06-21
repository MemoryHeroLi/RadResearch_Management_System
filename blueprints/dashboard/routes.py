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
