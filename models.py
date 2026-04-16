from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    unit = db.Column(db.String(120))   # 房产信息（楼栋/单元/门牌）
    area = db.Column(db.Float)   # 房屋面积（平方米）
    unit_type = db.Column(db.String(50))   # 房型（一室一厅、两室一厅等）
    vehicles = db.Column(db.Text)   # JSON: [{"plate":"沪A12345","model":"Tesla 3"}]
    vehicle_count = db.Column(db.Integer, default=0)   # 车辆数量
    parking_spots = db.Column(db.String(255))   # 车位编号，多个用逗号分隔
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='owner', lazy=True)
    payments = db.relationship('Payment', backref='owner', lazy=True)
    workorders = db.relationship('WorkOrder', backref='requester', lazy=True)

class ChargeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)   # 物业费/停车费/水费/电费...
    billing_cycle = db.Column(db.String(20), default="月")   # 计费周期（日/周/月/季/年）
    unit = db.Column(db.String(20), default="月")   # 计费单位（保留兼容）
    price = db.Column(db.Float, default=0.0)   # 单价
    link_to = db.Column(db.String(20))   # 关联业主信息：area(面积)/vehicles(车辆数)/none(无)
    description = db.Column(db.String(255))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    charge_type_id = db.Column(db.Integer, db.ForeignKey('charge_type.id'))
    billing_cycle = db.Column(db.String(20), default="月")   # 计费周期
    quantity = db.Column(db.Float)   # 计费数量（房屋面积或车辆数）
    price = db.Column(db.Float)   # 单价
    amount = db.Column(db.Float, nullable=False)   # 费用金额（月）
    unpaid_amount = db.Column(db.Float, default=0.0)   # 未付金额
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="未支付")   # 未支付/已支付/逾期
    description = db.Column(db.String(255))

    charge_type = db.relationship('ChargeType')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), default="线上")
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(255))

    invoice = db.relationship('Invoice')

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    equipment_type = db.Column(db.String(50))   # 设备类型：电梯/空调/水管/燃气等
    model = db.Column(db.String(120))   # 设备型号
    location = db.Column(db.String(255))
    serial = db.Column(db.String(120))
    status = db.Column(db.String(50), default="正常")   # 正常/维护/停用
    install_date = db.Column(db.Date)
    usage_years = db.Column(db.Float)   # 设备使用时间（年）

    plans = db.relationship('MaintenancePlan', backref='equipment', lazy=True)
    workorders = db.relationship('WorkOrder', backref='equipment', lazy=True)
    maintenance_records = db.relationship('MaintenanceRecord', backref='equipment', lazy=True)

class MaintenancePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    frequency = db.Column(db.String(50), default="每季度")
    next_date = db.Column(db.Date)
    notes = db.Column(db.String(255))

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), default="维修")   # 维修/投诉/保洁/其他
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="新建")   # 新建/处理中/已完成/已关闭
    priority = db.Column(db.String(20), default="中")   # 低/中/高
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)   # 派单时间
    completed_at = db.Column(db.DateTime)   # 结束时间
    closed_at = db.Column(db.DateTime)
    assignee = db.Column(db.String(120))   # 负责人
    repairer = db.Column(db.String(120))   # 维修人
    satisfaction = db.Column(db.String(20))   # 是否满意：满意/不满意/未评价

    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    repair_date = db.Column(db.Date, nullable=False)   # 维修时间
    main_issue = db.Column(db.Text)   # 主要问题
    repair_cost = db.Column(db.Float, default=0.0)   # 维修费用
    is_fixed = db.Column(db.Boolean, default=True)   # 是否修复
    is_replaced = db.Column(db.Boolean, default=False)   # 是否更换
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    send_email = db.Column(db.Boolean, default=False)
