"""标准预研流程模板——4个阶段、每阶段的子步骤，以及强制性评审关卡。

依据子功能模块-业务管理.md 中的研发流程定义。
"""

# 4个阶段的子步骤（顺序即执行顺序）
STANDARD_PROCESS = [
    {
        "stage": 1,
        "name": "需求收集",
        "trl": "TRL2",
        "steps": ["需求导入", "需求评审"],
    },
    {
        "stage": 2,
        "name": "功能构思",
        "trl": "TRL3",
        "steps": [
            "临床调研", "痛点分析", "需求提炼", "竞品分析",
            "方案构思", "可行性分析", "功能构思评审",
        ],
    },
    {
        "stage": 3,
        "name": "方案预研",
        "trl": "TRL6",
        "steps": [
            "技术调研", "方案设计及评审", "任务分解", "子任务开发",
            "仿真验证", "TRL6预研验收", "文档撰写", "文档评审",
        ],
    },
    {
        "stage": 4,
        "name": "版本开发",
        "trl": "TRL7",
        "steps": [
            "方案澄清", "功能开发", "功能测试",
            "临床验证", "TRL7验收",
        ],
    },
]

# 强制性评审关卡——必须通过才能进入下一阶段
GATE_STEPS = {"需求评审", "功能构思评审", "TRL6预研验收"}

STAGE_NAMES = {s["stage"]: s["name"] for s in STANDARD_PROCESS}
STAGE_TRL = {s["stage"]: s["trl"] for s in STANDARD_PROCESS}
