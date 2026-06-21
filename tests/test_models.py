from datetime import datetime
from models import (
    TechPoint, StageProgress, StageDocument,
    Member, CapabilityScore, Issue, Policy,
)


def test_create_tech_point(db):
    tp = TechPoint(name="低剂量CT去噪", direction="CT重建", owner="张三")
    db.session.add(tp)
    db.session.commit()
    assert tp.id is not None
    assert tp.current_stage == 1
    assert tp.status == "进行中"
    assert tp.created_at is not None


def test_tech_point_stage_progress_relation(db):
    tp = TechPoint(name="MRI伪影校正", direction="MRI")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求导入")
    db.session.add(sp)
    db.session.commit()
    assert len(tp.stage_progresses) == 1
    assert tp.stage_progresses[0].sub_step == "需求导入"


def test_stage_document_relation(db):
    tp = TechPoint(name="DR结节检测", direction="DR")
    db.session.add(tp)
    db.session.commit()
    sp = StageProgress(tech_point_id=tp.id, stage=1, sub_step="需求评审")
    db.session.add(sp)
    db.session.commit()
    doc = StageDocument(
        stage_progress_id=sp.id, doc_type="会议纪要",
        file_path="uploads/x.pdf", original_name="纪要.pdf",
    )
    db.session.add(doc)
    db.session.commit()
    assert len(sp.documents) == 1
    assert sp.documents[0].original_name == "纪要.pdf"


def test_member_capability_scores(db):
    m = Member(name="张三", group="CT重建组", level="A")
    db.session.add(m)
    db.session.commit()
    db.session.add(CapabilityScore(member_id=m.id, dimension="算法能力", score=9))
    db.session.commit()
    assert len(m.capability_scores) == 1
    assert m.capability_scores[0].score == 9


def test_issue_policy_relation(db):
    p = Policy(title="文档评审制度", version="1.0")
    db.session.add(p)
    db.session.commit()
    i = Issue(title="评审不及时", category="流程问题", severity="高",
              linked_policy_id=p.id)
    db.session.add(i)
    db.session.commit()
    assert len(p.issues) == 1
    assert p.issues[0].title == "评审不及时"
    assert i.policy.title == "文档评审制度"


from blueprints.business.process_template import STANDARD_PROCESS, GATE_STEPS


def test_standard_process_has_four_stages():
    assert len(STANDARD_PROCESS) == 4
    assert [s["stage"] for s in STANDARD_PROCESS] == [1, 2, 3, 4]


def test_standard_process_substeps_complete():
    assert "需求评审" in STANDARD_PROCESS[0]["steps"]
    assert "功能构思评审" in STANDARD_PROCESS[1]["steps"]
    assert "TRL6预研验收" in STANDARD_PROCESS[2]["steps"]
    assert "TRL7验收" in STANDARD_PROCESS[3]["steps"]


def test_gate_steps_cover_three_reviews():
    assert "需求评审" in GATE_STEPS
    assert "功能构思评审" in GATE_STEPS
    assert "TRL6预研验收" in GATE_STEPS
