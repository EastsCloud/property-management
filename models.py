
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    unit = db.Column(db.String(120))  # 房产信息（楼栋/单元/门牌）
    vehicles = db.Column(db.Text)   # JSON: [{"plate":"沪A12345","model":"Tesla 3"}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='owner', lazy=True)
    payments = db.relationship('Payment', backref='owner', lazy=True)
    workorders = db.relationship('WorkOrder', backref='requester', lazy=True)

class ChargeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # 物业费/停车费/水费/电费...
    unit = db.Column(db.String(20), default="月")     # 计费单位
    price = db.Column(db.Float, default=0.0)          # 单价
    description = db.Column(db.String(255))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    charge_type_id = db.Column(db.Integer, db.ForeignKey('charge_type.id'))
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="未支付")  # 未支付/已支付/逾期
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
    location = db.Column(db.String(255))
    serial = db.Column(db.String(120))
    status = db.Column(db.String(50), default="正常")  # 正常/维护/停用
    install_date = db.Column(db.Date)

    plans = db.relationship('MaintenancePlan', backref='equipment', lazy=True)
    workorders = db.relationship('WorkOrder', backref='equipment', lazy=True)

class MaintenancePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    frequency = db.Column(db.String(50), default="每季度")
    next_date = db.Column(db.Date)
    notes = db.Column(db.String(255))

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), default="维修")      # 维修/投诉/保洁/其他
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="新建")    # 新建/处理中/已完成/已关闭
    priority = db.Column(db.String(20), default="中")    # 低/中/高
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)

    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    assignee = db.Column(db.String(120))  # 负责人

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    send_email = db.Column(db.Boolean, default=False)
