def test_list_members_empty(client, db):
    resp = client.get("/team")
    assert resp.status_code == 200
    assert "成员".encode() in resp.data


def test_create_member(client, db):
    resp = client.post("/team/new", data={
        "name": "张三",
        "group": "CT重建组",
        "title": "高级算法工程师",
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


def test_filter_members_by_group(client, db):
    from models import Member
    db.session.add(Member(name="张三", group="CT重建组", level="A"))
    db.session.add(Member(name="李四", group="MRI组", level="B"))
    db.session.commit()
    resp = client.get("/team?group=CT重建组")
    assert "张三" in resp.data.decode()
    assert "李四" not in resp.data.decode()


def test_view_member_radar(client, db):
    from models import Member
    m = Member(name="张三", group="CT重建组", level="A")
    db.session.add(m)
    db.session.commit()
    resp = client.get(f"/team/{m.id}")
    assert resp.status_code == 200
    assert "雷达图".encode() in resp.data or "chart".encode() in resp.data.lower()
    assert "算法能力".encode() in resp.data


def test_edit_member_score(client, db):
    from models import Member, CapabilityScore
    m = Member(name="李四", group="MRI组", level="B")
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
