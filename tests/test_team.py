def test_list_members_empty(client, db):
    resp = client.get("/team")
    assert resp.status_code == 200
    assert "成员".encode() in resp.data


def test_create_member(client, db):
    resp = client.post("/team/new", data={
        "name": "张三",
        "employee_id": "RR001",
        "rank": "E7",
        "group": "放射图像研究组",
        "title": "技术经理",
        "level": "A",
        "skills": "CT重建,深度学习",
        "responsible_for": "低剂量CT去噪",
        "joined_at": "2023-03-01",
    }, follow_redirects=True)
    assert resp.status_code == 200
    from models import Member
    m = Member.query.first()
    assert m.name == "张三"
    assert m.level == "A"
    assert m.employee_id == "RR001"
    assert m.rank == "E7"
    assert m.title == "技术经理"


def test_filter_members_by_group(client, db):
    from models import Member
    db.session.add(Member(name="张三", group="放射图像研究组", level="A"))
    db.session.add(Member(name="李四", group="放射系统功能组", level="B"))
    db.session.commit()
    resp = client.get("/team?group=放射图像研究组")
    assert "张三" in resp.data.decode()
    assert "李四" not in resp.data.decode()


def test_view_member_radar(client, db):
    from models import Member, CapabilityDimension
    db.session.add(CapabilityDimension(name="算法能力"))
    db.session.add(CapabilityDimension(name="工程能力"))
    db.session.commit()
    m = Member(name="张三", group="放射图像研究组", level="A")
    db.session.add(m)
    db.session.commit()
    resp = client.get(f"/team/{m.id}")
    assert resp.status_code == 200
    assert "雷达图".encode() in resp.data or "chart".encode() in resp.data.lower()
    assert "算法能力".encode() in resp.data


def test_edit_member_score(client, db):
    from models import Member, CapabilityScore, CapabilityDimension
    for d in ["算法能力", "工程能力", "临床理解", "创新研究", "沟通协作"]:
        db.session.add(CapabilityDimension(name=d))
    db.session.commit()
    m = Member(name="李四", group="放射系统功能组", level="B")
    db.session.add(m)
    db.session.commit()
    resp = client.post(f"/team/{m.id}/score", data={
        "算法能力": "8", "工程能力": "7", "临床理解": "6",
        "创新研究": "5", "沟通协作": "9",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert CapabilityScore.query.filter_by(member_id=m.id).count() == 5
    s = CapabilityScore.query.filter_by(member_id=m.id, dimension="算法能力").first()
    assert s.score == 8


def test_edit_member(client, db):
    from models import Member
    m = Member(name="张三", group="放射图像研究组", title="工程师", level="A",
               employee_id="RR001", rank="E6")
    db.session.add(m)
    db.session.commit()
    resp = client.post(f"/team/{m.id}/edit", data={
        "name": "张三改",
        "employee_id": "RR001",
        "rank": "E7",
        "group": "放射智能定量组",
        "title": "技术经理",
        "level": "B",
        "skills": "Python,AI",
        "responsible_for": "新项目",
        "joined_at": "2024-01-01",
    }, follow_redirects=True)
    assert resp.status_code == 200
    db.session.refresh(m)
    assert m.name == "张三改"
    assert m.rank == "E7"
    assert m.title == "技术经理"
    assert m.group == "放射智能定量组"
    assert m.level == "B"


def test_add_dimension(client, db):
    from models import CapabilityDimension
    resp = client.post("/team/dimensions/add", data={
        "name": "领导力",
    }, follow_redirects=True)
    assert resp.status_code == 200
    dim = CapabilityDimension.query.filter_by(name="领导力").first()
    assert dim is not None


def test_manage_dimensions_page(client, db):
    from models import CapabilityDimension
    db.session.add(CapabilityDimension(name="算法能力"))
    db.session.add(CapabilityDimension(name="工程能力"))
    db.session.commit()
    resp = client.get("/team/dimensions")
    assert resp.status_code == 200
    assert "算法能力".encode() in resp.data
    assert "工程能力".encode() in resp.data
    assert "维度管理".encode() in resp.data


def test_delete_dimension(client, db):
    from models import CapabilityDimension, CapabilityScore, Member
    dim = CapabilityDimension(name="测试维度")
    db.session.add(dim)
    db.session.commit()
    m = Member(name="测试", group="放射图像研究组", level="A")
    db.session.add(m)
    db.session.commit()
    db.session.add(CapabilityScore(member_id=m.id, dimension="测试维度", score=5))
    db.session.commit()

    # 正确输入维度名称才可删除
    resp = client.post(f"/team/dimensions/{dim.id}/delete", data={
        "confirm_name": "测试维度",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert CapabilityDimension.query.filter_by(name="测试维度").first() is None
    assert CapabilityScore.query.filter_by(dimension="测试维度").count() == 0


def test_delete_dimension_rejects_wrong_name(client, db):
    from models import CapabilityDimension
    dim = CapabilityDimension(name="保留维度")
    db.session.add(dim)
    db.session.commit()

    # 输入不匹配的名称，不应删除
    resp = client.post(f"/team/dimensions/{dim.id}/delete", data={
        "confirm_name": "错误名称",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert CapabilityDimension.query.filter_by(name="保留维度").first() is not None
