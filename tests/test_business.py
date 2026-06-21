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
    assert b"\xe9\x9c\x80\xe6\xb1\x82\xe5\xaf\xbc\xe5\x85\xa5".decode() in resp.data.decode()  # 需求导入
    # 阶段名应出现
    assert "需求收集".encode() in resp.data
    # 阶段4未解锁时应显示锁定提示
    assert "未解锁".encode() in resp.data


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
