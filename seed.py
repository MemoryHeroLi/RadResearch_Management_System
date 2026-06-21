r"""种子数据脚本：填充示例数据便于首次体验。
运行："D:\ProgramData\anaconda3\envs\app\python.exe" seed.py
"""
from datetime import date

from start import app
from extensions import db
from models import (
    TechPoint, StageProgress, Member, CapabilityScore, CapabilityDimension,
    Issue, Policy,
)
from blueprints.business.process_template import STANDARD_PROCESS


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 技术点 + 标准流程子步骤
        samples = [
            ("低剂量CT去噪算法", "放射图像研究", "张三"),
            ("MRI运动伪影校正", "放射图像研究", "李四"),
            ("DR胸部结节检测", "放射智能应用", "王五"),
        ]
        for name, direction, owner in samples:
            tp = TechPoint(name=name, direction=direction, owner=owner, current_stage=1)
            db.session.add(tp)
            db.session.flush()
            for sdef in STANDARD_PROCESS:
                for step in sdef["steps"]:
                    db.session.add(StageProgress(
                        tech_point_id=tp.id, stage=sdef["stage"], sub_step=step,
                    ))
        db.session.commit()

        # 能力维度初始化
        dims = ["算法能力", "工程能力", "临床理解", "创新研究", "沟通协作"]
        for d in dims:
            db.session.add(CapabilityDimension(name=d))
        db.session.commit()

        # 成员 + 能力评分
        members = [
            ("张三", "放射图像研究组", "技术经理", "A", "RR001", "E7", [9, 8, 7, 6, 8]),
            ("李四", "放射图像研究组", "工程师", "B", "RR002", "E5", [7, 7, 6, 5, 7]),
        ]
        for name, group, title, level, employee_id, rank, scores in members:
            m = Member(name=name, employee_id=employee_id, rank=rank,
                       group=group, title=title, level=level,
                       skills=",".join(dims[:2]), responsible_for=name,
                       joined_at=date(2023, 3, 1))
            db.session.add(m)
            db.session.flush()
            for d, sc in zip(dims, scores):
                db.session.add(CapabilityScore(member_id=m.id, dimension=d, score=sc))
        db.session.commit()

        # 制度 + 问题
        p = Policy(title="文档评审制度", version="1.0",
                   content="评审后3个工作日内归档评审材料与会议纪要。")
        db.session.add(p)
        db.session.flush()
        db.session.add(Issue(
            title="预研文档评审不及时", category="流程问题", severity="高",
            status="已建制度", linked_policy_id=p.id,
            description="导致方案预研阶段反复返工。",
        ))
        db.session.add(Issue(
            title="跨组评审缺少统一评分标准", category="流程问题", severity="中",
            status="待处理",
        ))
        db.session.commit()
        print("种子数据已填充：3个技术点、2个成员、1个制度、2个问题。")


if __name__ == "__main__":
    seed()
