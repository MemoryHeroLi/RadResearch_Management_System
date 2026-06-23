from flask import render_template, request, redirect, url_for, flash

from blueprints.team import team_bp
from extensions import db
from models import Member, CapabilityDimension

GROUPS = ["放射系统功能组", "放射图像研究组", "放射智能定量组", "放射智能应用组"]
TITLES = ["工程师", "技术经理"]
LEVELS = ["A", "B", "C", "D"]


def get_dimensions():
    """从数据库读取当前所有能力维度"""
    return CapabilityDimension.query.order_by(CapabilityDimension.id).all()


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

    # AJAX 请求：只返回成员列表片段
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("team/_member_grid.html", members=members,
                               groups=GROUPS, levels=LEVELS, titles=TITLES)

    return render_template(
        "team/list.html", members=members,
        groups=GROUPS, levels=LEVELS, titles=TITLES,
        filters={"group": group, "level": level},
    )


@team_bp.route("/new", methods=["GET", "POST"])
def new_member():
    if request.method == "POST":
        from datetime import date
        joined = request.form.get("joined_at") or None
        m = Member(
            name=request.form["name"],
            employee_id=request.form.get("employee_id", ""),
            rank=request.form.get("rank", ""),
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
    return render_template("team/form.html", member=None, groups=GROUPS, levels=LEVELS, titles=TITLES)


@team_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_member(id):
    m = Member.query.get_or_404(id)
    if request.method == "POST":
        from datetime import date
        m.name = request.form["name"]
        m.employee_id = request.form.get("employee_id", "")
        m.rank = request.form.get("rank", "")
        m.group = request.form.get("group", "")
        m.title = request.form.get("title", "")
        m.level = request.form.get("level", "")
        m.skills = request.form.get("skills", "")
        m.responsible_for = request.form.get("responsible_for", "")
        joined = request.form.get("joined_at") or None
        m.joined_at = date.fromisoformat(joined) if joined else None
        db.session.commit()
        flash("成员已更新", "success")
        return redirect(url_for("team.view_member", id=m.id))
    return render_template("team/form.html", member=m, groups=GROUPS, levels=LEVELS, titles=TITLES)


@team_bp.route("/<int:id>")
def view_member(id):
    m = Member.query.get_or_404(id)
    dims = get_dimensions()
    dim_names = [d.name for d in dims]
    scores = {s.dimension: s.score for s in m.capability_scores}
    return render_template(
        "team/radar.html", member=m,
        dimensions=dims,
        scores=scores,
        editing=False,
        chart_labels=dim_names,
        chart_values=[scores.get(d, 0) for d in dim_names],
    )


@team_bp.route("/<int:id>/score", methods=["GET", "POST"])
def edit_score(id):
    from models import CapabilityScore
    m = Member.query.get_or_404(id)
    dims = get_dimensions()
    dim_names = [d.name for d in dims]
    if request.method == "POST":
        for d in dim_names:
            val = request.form.get(d, type=int)
            existing = CapabilityScore.query.filter_by(member_id=m.id, dimension=d).first()
            if val is not None:
                if existing:
                    existing.score = val
                else:
                    db.session.add(CapabilityScore(member_id=m.id, dimension=d, score=val))
        db.session.commit()
        flash("能力评分已更新", "success")
        return redirect(url_for("team.view_member", id=m.id))
    scores = {s.dimension: s.score for s in m.capability_scores}
    return render_template(
        "team/radar.html", member=m,
        dimensions=dims,
        scores=scores,
        editing=True,
        chart_labels=dim_names,
        chart_values=[scores.get(d, 0) for d in dim_names],
    )


@team_bp.route("/dimensions", methods=["GET"])
def manage_dimensions():
    """独立维度管理页面"""
    dims = CapabilityDimension.query.order_by(CapabilityDimension.id).all()
    return render_template("team/dimensions.html", dimensions=dims)


@team_bp.route("/dimensions/add", methods=["POST"])
def add_dimension():
    name = request.form.get("name", "").strip()
    if not name:
        flash("维度名称不能为空", "danger")
        return redirect(url_for("team.manage_dimensions"))
    if CapabilityDimension.query.filter_by(name=name).first():
        flash(f"维度「{name}」已存在", "warning")
        return redirect(url_for("team.manage_dimensions"))
    db.session.add(CapabilityDimension(name=name))
    db.session.commit()
    flash(f"维度「{name}」已添加", "success")
    return redirect(url_for("team.manage_dimensions"))


@team_bp.route("/dimensions/<int:dim_id>/delete", methods=["POST"])
def delete_dimension(dim_id):
    from models import CapabilityScore
    dim = CapabilityDimension.query.get_or_404(dim_id)
    confirm_name = request.form.get("confirm_name", "").strip()
    if confirm_name != dim.name:
        flash(f"输入的维度名称不匹配，未删除", "danger")
        return redirect(url_for("team.manage_dimensions"))
    # 删除所有成员该维度的评分
    CapabilityScore.query.filter_by(dimension=dim.name).delete()
    db.session.delete(dim)
    db.session.commit()
    flash(f"维度「{dim.name}」已删除", "success")
    return redirect(url_for("team.manage_dimensions"))
