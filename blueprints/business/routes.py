import os
from datetime import datetime

from flask import (render_template, request, redirect, url_for, flash,
                   send_from_directory, current_app)

from blueprints.business import business_bp
from blueprints.business.process_template import STANDARD_PROCESS, STAGE_NAMES
from extensions import db
from models import TechPoint, StageProgress

DIRECTIONS = ["放射系统功能", "放射图像研究", "放射智能定量", "放射智能应用"]


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
    return render_template("business/form.html", point=None, stages=STANDARD_PROCESS, directions=DIRECTIONS)


@business_bp.route("/<int:id>")
def view_tech_point(id):
    from blueprints.business.process_template import (
        STANDARD_PROCESS, GATE_STEPS,
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


@business_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_tech_point(id):
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
    return render_template("business/form.html", point=tp, stages=STANDARD_PROCESS, directions=DIRECTIONS)


@business_bp.route("/stage/<int:sp_id>/toggle", methods=["POST"])
def toggle_substep(sp_id):
    from datetime import datetime
    sp = StageProgress.query.get_or_404(sp_id)
    sp.is_completed = not sp.is_completed
    sp.completed_at = datetime.utcnow() if sp.is_completed else None
    db.session.commit()
    flash(f"子步骤「{sp.sub_step}」已{'完成' if sp.is_completed else '取消完成'}", "info")
    return redirect(url_for("business.view_tech_point", id=sp.tech_point_id))


@business_bp.route("/stage/<int:sp_id>/upload", methods=["POST"])
def upload_doc(sp_id):
    from models import StageDocument
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


@business_bp.route("/doc/<int:doc_id>/delete", methods=["POST"])
def delete_doc(doc_id):
    from models import StageDocument
    doc = StageDocument.query.get_or_404(doc_id)
    tp_id = doc.stage_progress.tech_point_id
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_dir, doc.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(doc)
    db.session.commit()
    flash("文件已移除", "success")
    return redirect(url_for("business.view_tech_point", id=tp_id))
