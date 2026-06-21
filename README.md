# 放射影像算法研究部管理系统

本地单用户 Web 应用，作为放射影像算法研究部经理的日常管理抓手。

## 运行

```bash
# 必须使用 conda app 环境的 python
"D:\ProgramData\anaconda3\envs\app\python.exe" start.py
```

浏览器打开 http://localhost:5000

## 首次体验（填充示例数据）

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" seed.py
```

## 测试

```bash
"D:\ProgramData\anaconda3\envs\app\python.exe" -m pytest tests/ -v
```

## 功能模块

- **仪表盘**：统计卡片 + 最近技术点 + 待处理问题
- **业务管理**：技术点按 TRL2-TRL7 标准流程跟踪，看板视图含阶段评审关卡
- **团队管理**：成员列表 + 5维度能力雷达图（Chart.js）
- **流程制度**：问题记录与制度文档双向关联

## 数据

SQLite 数据库文件 `rad_research.db` 位于项目根目录，上传文档存于 `uploads/`。
