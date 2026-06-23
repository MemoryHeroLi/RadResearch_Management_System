import os
from datetime import datetime

from flask import (render_template, request, redirect, url_for, flash,
                   send_from_directory, current_app)

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

    # AJAX 请求：只返回表格片段
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("process/_issue_table.html", issues=issues)

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


@process_bp.route("/issues/<int:id>/upload", methods=["POST"])
def upload_issue_doc(id):
    from models import IssueDocument
    issue = Issue.query.get_or_404(id)
    file = request.files.get("file")
    if not file or not file.filename:
        flash("请选择文件", "danger")
        return redirect(url_for("process.edit_issue", id=issue.id))
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"issue{issue.id}_{file.filename}"
    save_path = os.path.join(upload_dir, safe_name)
    file.save(save_path)
    doc = IssueDocument(
        issue_id=issue.id,
        doc_type=request.form.get("doc_type", ""),
        file_path=safe_name,
        original_name=file.filename,
        uploaded_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.commit()
    flash(f"已上传 {file.filename}", "success")
    return redirect(url_for("process.edit_issue", id=issue.id))


@process_bp.route("/issue_doc/<int:doc_id>/download")
def download_issue_doc(doc_id):
    from models import IssueDocument
    doc = IssueDocument.query.get_or_404(doc_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir, doc.file_path, as_attachment=True,
        download_name=doc.original_name,
    )


@process_bp.route("/issue_doc/<int:doc_id>/delete", methods=["POST"])
def delete_issue_doc(doc_id):
    from models import IssueDocument
    doc = IssueDocument.query.get_or_404(doc_id)
    issue_id = doc.issue_id
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_dir, doc.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(doc)
    db.session.commit()
    flash("附件已移除", "success")
    return redirect(url_for("process.edit_issue", id=issue_id))


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
