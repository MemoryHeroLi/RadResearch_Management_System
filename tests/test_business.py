def test_list_tech_points_empty(client, db):
    resp = client.get("/business")
    assert resp.status_code == 200
    assert "技术点".encode() in resp.data


def test_create_tech_point_auto_generates_stage_progress(client, db):
    resp = client.post("/business/new", data={
        "name": "低剂量CT去噪",
        "direction": "放射图像研究",
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
    db.session.add(TechPoint(name="A", direction="放射图像研究", current_stage=1, status="进行中"))
    db.session.add(TechPoint(name="B", direction="放射智能定量", current_stage=3, status="进行中"))
    db.session.commit()
    resp = client.get("/business?stage=3")
    assert b"B" in resp.data
    assert b"A" not in resp.data


def test_view_tech_point_kanban(client, db):
    from models import TechPoint
    tp = TechPoint(name="看板测试", direction="放射图像研究", current_stage=1)
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
    tp = TechPoint(name="切换测试", direction="放射图像研究")
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
    tp = TechPoint(name="上传测试", direction="放射图像研究")
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


def test_delete_document(client, db, app):
    from models import TechPoint, StageProgress, StageDocument
    import os
    tp = TechPoint(name="删除测试", direction="放射图像研究")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求评审")
    db.session.add(sp)
    db.session.commit()

    # 上传文件
    data = {
        "file": (io.BytesIO(b"content to delete"), "delete_me.pdf"),
        "doc_type": "测试",
    }
    resp = client.post(
        f"/business/stage/{sp.id}/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = StageDocument.query.first()
    assert doc is not None

    # 确认磁盘文件存在
    upload_dir = app.config["UPLOAD_FOLDER"]
    disk_path = os.path.join(upload_dir, doc.file_path)
    assert os.path.exists(disk_path)

    # 删除
    resp = client.post(f"/business/doc/{doc.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert StageDocument.query.count() == 0
    assert not os.path.exists(disk_path)


def test_delete_tech_point(client, db, app):
    """创建含子步骤和文档的技术点，输入正确名称后删除"""
    from models import TechPoint, StageProgress, StageDocument
    import os

    tp = TechPoint(name="待删除项目", direction="放射图像研究")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求导入")
    db.session.add(sp)
    db.session.flush()

    # 上传一个文档
    data = {
        "file": (io.BytesIO(b"tp attachment"), "tp_doc.pdf"),
        "doc_type": "测试",
    }
    resp = client.post(
        f"/business/stage/{sp.id}/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = StageDocument.query.first()
    assert doc is not None
    upload_dir = app.config["UPLOAD_FOLDER"]
    disk_path = os.path.join(upload_dir, doc.file_path)
    assert os.path.exists(disk_path)

    # 输入正确名称删除
    resp = client.post(f"/business/{tp.id}/delete", data={
        "confirm_name": "待删除项目",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert TechPoint.query.count() == 0
    assert StageProgress.query.filter_by(tech_point_id=tp.id).count() == 0
    assert StageDocument.query.count() == 0
    assert not os.path.exists(disk_path)


def test_delete_tech_point_rejects_wrong_name(client, db):
    """输入错误名称时拒绝删除"""
    from models import TechPoint
    tp = TechPoint(name="保留项目", direction="放射图像研究")
    db.session.add(tp)
    db.session.commit()

    resp = client.post(f"/business/{tp.id}/delete", data={
        "confirm_name": "错误名称",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert TechPoint.query.filter_by(name="保留项目").first() is not None


def test_new_tech_point_form_has_member_select(client, db):
    """新建技术点表单的负责人字段应显示 Member 表中的成员"""
    from models import Member
    db.session.add(Member(name="张三", group="放射图像研究组"))
    db.session.add(Member(name="李四", group="放射系统功能组"))
    db.session.commit()

    resp = client.get("/business/new")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 应包含 <select name="owner">
    assert 'name="owner"' in html
    assert '<select' in html
    # 应包含两位成员
    assert "张三" in html
    assert "李四" in html
    # 不应是 input
    assert '<input type="text" name="owner"' not in html


def test_edit_tech_point_form_has_member_select(client, db):
    """编辑技术点表单的负责人字段应显示已选中的负责人"""
    from models import TechPoint, Member
    db.session.add(Member(name="王五", group="放射智能定量组"))
    db.session.commit()
    tp = TechPoint(name="测试技术点", direction="放射图像研究", owner="王五")
    db.session.add(tp)
    db.session.commit()

    resp = client.get(f"/business/{tp.id}/edit")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 应包含 select + 选中王五
    assert 'name="owner"' in html
    assert "王五" in html
    # 不应是 input
    assert '<input type="text" name="owner"' not in html


def test_member_card_has_data_attributes(client, db):
    """成员卡片应包含完整的 data-member-* 属性，且模态框结构存在"""
    from models import Member
    db.session.add(Member(
        name="张三", employee_id="E001", rank="P7",
        group="放射图像研究组", title="工程师", level="A",
        skills="Python,C++", responsible_for="CT图像重建",
    ))
    db.session.commit()

    resp = client.get("/team/")
    assert resp.status_code == 200
    html = resp.data.decode()
    # 模态框结构应存在
    assert 'id="member-modal"' in html
    assert 'class="modal-overlay"' in html
    # 方案D Profile 风格元素
    assert 'id="modal-avatar"' in html
    assert 'class="profile-top"' in html
    assert 'class="level-badge"' in html
    assert 'id="radarChart"' in html
    # 卡片应包含 data 属性
    assert 'data-member-name="张三"' in html
    assert 'data-member-employee-id="E001"' in html
    assert 'data-member-group="放射图像研究组"' in html
    # 卡片应有点击处理
    assert "onclick=\"openMemberModal(this)\"" in html


def test_list_issues_ajax_returns_table_fragment(client, db):
    """AJAX 请求应只返回表格 HTML 片段，不含完整页面结构"""
    from models import Issue
    db.session.add(Issue(title="测试问题", category="流程问题", severity="高", status="待处理"))
    db.session.add(Issue(title="已关闭问题", category="质量问题", severity="中", status="已关闭"))
    db.session.commit()

    # 不带 AJAX 头的普通请求应返回完整页面
    resp = client.get("/process/issues")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "流程制度" in html  # 页面标题

    # 带 AJAX 头的请求应只返回表格片段
    resp_ajax = client.get("/process/issues", headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp_ajax.status_code == 200
    html_ajax = resp_ajax.data.decode()
    # 片段不应包含完整页面结构
    assert "流程制度" not in html_ajax  # 不应有页面标题
    assert "<table" in html_ajax or "empty-state" in html_ajax  # 表格或空状态


def test_list_issues_ajax_filter(client, db):
    """AJAX 筛选应返回正确的筛选结果"""
    from models import Issue
    db.session.add(Issue(title="流程问题A", category="流程问题", severity="高", status="待处理"))
    db.session.add(Issue(title="质量问题B", category="质量问题", severity="中", status="待处理"))
    db.session.commit()

    resp = client.get("/process/issues?category=流程问题",
                      headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "流程问题A" in html
    assert "质量问题B" not in html


def test_list_members_ajax_returns_fragment(client, db):
    """团队管理 AJAX 请求应只返回成员列表片段，不含完整页面结构"""
    from models import Member
    db.session.add(Member(name="张三", group="放射图像研究组", level="A"))
    db.session.add(Member(name="李四", group="放射系统功能组", level="B"))
    db.session.commit()

    # 普通请求应返回完整页面
    resp = client.get("/team/")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "团队管理" in html

    # AJAX 请求应只返回成员列表片段
    resp_ajax = client.get("/team/", headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp_ajax.status_code == 200
    html_ajax = resp_ajax.data.decode()
    assert "团队管理" not in html_ajax
    assert "member-grid" in html_ajax or "empty-state" in html_ajax


def test_list_members_ajax_filter(client, db):
    """团队管理 AJAX 筛选应返回正确的筛选结果"""
    from models import Member
    db.session.add(Member(name="张三", group="放射图像研究组", level="A"))
    db.session.add(Member(name="李四", group="放射系统功能组", level="B"))
    db.session.commit()

    resp = client.get("/team/?group=放射图像研究组",
                      headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "张三" in html
    assert "李四" not in html


def test_list_tech_points_ajax_returns_fragment(client, db):
    """业务管理 AJAX 请求应只返回列表片段，不含完整页面结构"""
    from models import TechPoint
    db.session.add(TechPoint(name="测试A", direction="放射图像研究", current_stage=1, status="进行中"))
    db.session.add(TechPoint(name="测试B", direction="放射智能定量", current_stage=3, status="进行中"))
    db.session.commit()

    # 普通请求应返回完整页面
    resp = client.get("/business/")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "业务管理" in html

    # AJAX 请求应只返回列表片段
    resp_ajax = client.get("/business/", headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp_ajax.status_code == 200
    html_ajax = resp_ajax.data.decode()
    assert "业务管理" not in html_ajax
    assert ("data-table" in html_ajax) or ("empty-state" in html_ajax)


def test_list_tech_points_ajax_filter(client, db):
    """业务管理 AJAX 筛选应返回正确的筛选结果"""
    from models import TechPoint
    db.session.add(TechPoint(name="测试A", direction="放射图像研究", current_stage=1, status="进行中"))
    db.session.add(TechPoint(name="测试B", direction="放射智能定量", current_stage=3, status="进行中"))
    db.session.commit()

    resp = client.get("/business/?stage=3",
                      headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "测试B" in html
    assert "测试A" not in html
