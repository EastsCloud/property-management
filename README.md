
# 物业管理系统（Flask + SQLAlchemy）

包含模块：业主信息、收费管理（收费项目/账单/缴费）、设备管理（台账/维护计划）、工单管理、社区服务（公告）。

## 快速开始
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# 初始化数据库并写入演示数据
flask --app app.py init-db
flask --app app.py run
```
打开浏览器访问 http://127.0.0.1:5000
