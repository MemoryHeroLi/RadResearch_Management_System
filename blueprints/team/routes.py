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
    m = Member.query.get_or_404(id)
    scores = {s.dimension: s.score for s in m.capability_scores}
    return render_template(
        "team/radar.html", member=m,
        dimensions=CAPABILITY_DIMENSIONS,
        scores=scores,
        editing=False,
        chart_labels=CAPABILITY_DIMENSIONS,
        chart_values=[scores.get(d, 0) for d in CAPABILITY_DIMENSIONS],
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
