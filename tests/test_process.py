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
    assert "评审不及时" in resp.data.decode()


import io


def test_upload_issue_document(client, db, app):
    from models import Issue
    i = Issue(title="测试问题", category="流程问题", severity="中")
    db.session.add(i)
    db.session.commit()

    data = {
        "file": (io.BytesIO(b"fake issue attachment"), "evidence.pdf"),
        "doc_type": "证据材料",
    }
    resp = client.post(
        f"/process/issues/{i.id}/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert resp.status_code == 200

    from models import IssueDocument
    doc = IssueDocument.query.first()
    assert doc is not None
    assert doc.original_name == "evidence.pdf"
    assert doc.issue_id == i.id
    assert doc.doc_type == "证据材料"

    # 下载
    resp = client.get(f"/process/issue_doc/{doc.id}/download")
    assert resp.status_code == 200
    assert b"fake issue attachment" in resp.data

    # 问题编辑页应显示附件
    resp = client.get(f"/process/issues/{i.id}")
    assert resp.status_code == 200


def test_delete_issue_document(client, db, app):
    from models import Issue, IssueDocument
    import os
    i = Issue(title="删除测试问题", category="流程问题", severity="中")
    db.session.add(i)
    db.session.commit()

    # 上传附件
    data = {
        "file": (io.BytesIO(b"issue content to delete"), "delete_issue.pdf"),
        "doc_type": "测试附件",
    }
    resp = client.post(
        f"/process/issues/{i.id}/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = IssueDocument.query.first()
    assert doc is not None

    # 确认磁盘文件存在
    upload_dir = app.config["UPLOAD_FOLDER"]
    disk_path = os.path.join(upload_dir, doc.file_path)
    assert os.path.exists(disk_path)

    # 删除
    resp = client.post(f"/process/issue_doc/{doc.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert IssueDocument.query.count() == 0
    assert not os.path.exists(disk_path)
