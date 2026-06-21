def test_dashboard_index_renders(client, db):
    import models  # noqa: F401
    resp = client.get("/")
    assert resp.status_code == 200
    assert "放射影像算法研究部".encode() in resp.data
    assert "技术点总数".encode() in resp.data


def test_dashboard_shows_counts(client, db):
    from models import TechPoint, Issue
    db.session.add(TechPoint(name="测试点", direction="CT重建", status="进行中"))
    db.session.add(Issue(title="问题1", status="待处理"))
    db.session.commit()
    resp = client.get("/")
    assert resp.status_code == 200
    # 统计卡片应显示数字（HTML 中含 "1" 在统计位置）
    assert b"1" in resp.data
