from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Owner, ChargeType, Invoice, Payment, Equipment, MaintenancePlan, WorkOrder, Announcement
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        # 种子数据
        o1 = Owner(name="张三", phone="13800001111", email="zhangsan@example.com", unit="A-2-302")
        o2 = Owner(name="李四", phone="13900002222", email="lisi@example.com", unit="B-1-101")
        ct1 = ChargeType(name="物业费", unit="月", price=2.5, description="2.5元/㎡·月")
        ct2 = ChargeType(name="停车费", unit="月", price=300)
        db.session.add_all([o1,o2,ct1,ct2])
        db.session.commit()

        # 首月账单
        for owner in Owner.query.all():
            inv = Invoice(owner_id=owner.id, charge_type_id=ct1.id, amount=500, due_date=date.today()+relativedelta(days=15), description="2025年10月物业费")
            db.session.add(inv)
        eq = Equipment(name="1号电梯", location="A座", serial="EL-001", status="正常")
        plan = MaintenancePlan(equipment=eq, frequency="每季度", next_date=date.today()+relativedelta(months=3))
        ann = Announcement(title="停水通知", content="本周三9:00-12:00小区停水，请提前蓄水。")
        db.session.add_all([eq, plan, ann])
        db.session.commit()
        print("数据库已初始化")

@app.route('/')
def dashboard():
    owners = Owner.query.count()
    unpaid = Invoice.query.filter(Invoice.status!="已支付").count()
    open_wos = WorkOrder.query.filter(WorkOrder.status!="已完成").count()
    equips = Equipment.query.count()
    latest_ann = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    recent_wos = WorkOrder.query.order_by(WorkOrder.created_at.desc()).limit(8).all()
    move_outs = Owner.query.order_by(Owner.created_at.desc()).limit(10).all()  # 占位数据
    return render_template('dashboard.html', owners=owners, unpaid=unpaid, open_wos=open_wos, equips=equips, latest_ann=latest_ann, recent_wos=recent_wos, move_outs=move_outs)

# ---- 业主 CRUD ----
@app.route('/owners')
def owners_list():
    q = request.args.get('q','').strip()
    query = Owner.query
    if q:
        like = f"%{q}%"
        query = query.filter((Owner.name.like(like)) | (Owner.phone.like(like)) | (Owner.unit.like(like)))
    owners = query.order_by(Owner.id.desc()).all()
    return render_template('owners/list.html', owners=owners, q=q)

@app.route('/owners/new', methods=['GET','POST'])
def owners_new():
    if request.method == 'POST':
        vehicles = request.form.get('vehicles_json') or "[]"
        owner = Owner(
            name=request.form['name'],
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            unit=request.form.get('unit'),
            vehicles=vehicles
        )
        db.session.add(owner)
        db.session.commit()
        flash('已创建业主', 'success')
        return redirect(url_for('owners_list'))
    return render_template('owners/new.html')

@app.route('/owners/<int:oid>', methods=['GET','POST'])
def owners_detail(oid):
    owner = Owner.query.get_or_404(oid)
    if request.method == 'POST':
        owner.name = request.form['name']
        owner.phone = request.form.get('phone')
        owner.email = request.form.get('email')
        owner.unit = request.form.get('unit')
        owner.vehicles = request.form.get('vehicles_json') or "[]"
        db.session.commit()
        flash('已保存', 'success')
        return redirect(url_for('owners_detail', oid=oid))
    invoices = Invoice.query.filter_by(owner_id=oid).all()
    payments = Payment.query.filter_by(owner_id=oid).all()
    wos = WorkOrder.query.filter_by(owner_id=oid).all()
    return render_template('owners/detail.html', owner=owner, invoices=invoices, payments=payments, wos=wos)

@app.route('/owners/<int:oid>/delete', methods=['POST'])
def owners_delete(oid):
    owner = Owner.query.get_or_404(oid)
    db.session.delete(owner)
    db.session.commit()
    flash('已删除', 'warning')
    return redirect(url_for('owners_list'))

# ---- 收费/账单 ----
@app.route('/billing/charge-types', methods=['GET','POST'])
def charge_types():
    if request.method == 'POST':
        ct = ChargeType(name=request.form['name'], unit=request.form.get('unit'), price=float(request.form.get('price') or 0), description=request.form.get('description'))
        db.session.add(ct); db.session.commit()
        return redirect(url_for('charge_types'))
    types = ChargeType.query.order_by(ChargeType.id.desc()).all()
    return render_template('billing/charge_types.html', types=types)

@app.route('/billing/invoices')
def invoices_list():
    q = request.args.get('q','').strip()
    status = request.args.get('status','')
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    invoices = query.order_by(Invoice.due_date.asc()).all()
    return render_template('billing/invoices.html', invoices=invoices, q=q, status=status)

@app.route('/billing/invoices/new', methods=['GET','POST'])
def invoices_new():
    owners = Owner.query.all()
    types = ChargeType.query.all()
    if request.method == 'POST':
        inv = Invoice(owner_id=int(request.form['owner_id']), charge_type_id=int(request.form['charge_type_id']), amount=float(request.form['amount']), due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(), description=request.form.get('description'))
        db.session.add(inv); db.session.commit()
        return redirect(url_for('invoices_list'))
    return render_template('billing/invoices_new.html', owners=owners, types=types)

@app.route('/billing/payments', methods=['GET','POST'])
def payments_list():
    if request.method == 'POST':
        p = Payment(owner_id=int(request.form['owner_id']), invoice_id=int(request.form['invoice_id']) if request.form.get('invoice_id') else None, amount=float(request.form['amount']), method=request.form.get('method'), note=request.form.get('note'))
        inv_id = request.form.get('invoice_id')
        if inv_id:
            inv = Invoice.query.get(int(inv_id))
            if inv and p.amount >= inv.amount:
                inv.status = "已支付"
        db.session.add(p); db.session.commit()
        return redirect(url_for('payments_list'))
    owners = Owner.query.all()
    invoices = Invoice.query.filter(Invoice.status!="已支付").all()
    payments = Payment.query.order_by(Payment.paid_at.desc()).all()
    return render_template('billing/payments.html', payments=payments, owners=owners, invoices=invoices)

# ---- 设备/维护 ----
@app.route('/equipment')
def equipment_list():
    q = request.args.get('q','').strip()
    query = Equipment.query
    if q:
        like = f"%{q}%"
        query = query.filter((Equipment.name.like(like)) | (Equipment.location.like(like)) | (Equipment.serial.like(like)))
    items = query.order_by(Equipment.id.desc()).all()
    return render_template('equipment/list.html', items=items, q=q)

@app.route('/equipment/new', methods=['GET','POST'])
def equipment_new():
    if request.method == 'POST':
        item = Equipment(name=request.form['name'], location=request.form.get('location'), serial=request.form.get('serial'), status=request.form.get('status'), install_date=datetime.strptime(request.form['install_date'], '%Y-%m-%d').date() if request.form.get('install_date') else None)
        db.session.add(item); db.session.commit()
        return redirect(url_for('equipment_list'))
    return render_template('equipment/new.html')

@app.route('/equipment/<int:eid>', methods=['GET','POST'])
def equipment_detail(eid):
    eq = Equipment.query.get_or_404(eid)
    if request.method == 'POST':
        eq.name = request.form['name']
        eq.location = request.form.get('location')
        eq.serial = request.form.get('serial')
        eq.status = request.form.get('status')
        db.session.commit()
        return redirect(url_for('equipment_detail', eid=eid))
    plans = MaintenancePlan.query.filter_by(equipment_id=eid).all()
    wos = WorkOrder.query.filter_by(equipment_id=eid).all()
    return render_template('equipment/detail.html', eq=eq, plans=plans, wos=wos)

@app.route('/equipment/<int:eid>/plan/new', methods=['POST'])
def plan_new(eid):
    plan = MaintenancePlan(equipment_id=eid, frequency=request.form.get('frequency'), next_date=datetime.strptime(request.form['next_date'], '%Y-%m-%d').date() if request.form.get('next_date') else None, notes=request.form.get('notes'))
    db.session.add(plan); db.session.commit()
    return redirect(url_for('equipment_detail', eid=eid))

# ---- 工单 ----
@app.route('/workorders')
def workorders_list():
    status = request.args.get('status','')
    query = WorkOrder.query
    if status:
        query = query.filter_by(status=status)
    wos = query.order_by(WorkOrder.created_at.desc()).all()
    return render_template('workorders/list.html', wos=wos, status=status)

@app.route('/workorders/new', methods=['GET','POST'])
def workorders_new():
    owners = Owner.query.all()
    equips = Equipment.query.all()
    if request.method == 'POST':
        wo = WorkOrder(type=request.form.get('type'), description=request.form['description'], status=request.form.get('status','新建'), priority=request.form.get('priority','中'), owner_id=int(request.form['owner_id']) if request.form.get('owner_id') else None, equipment_id=int(request.form['equipment_id']) if request.form.get('equipment_id') else None, assignee=request.form.get('assignee'))
        db.session.add(wo); db.session.commit()
        return redirect(url_for('workorders_list'))
    return render_template('workorders/new.html', owners=owners, equips=equips)

@app.route('/workorders/<int:wid>', methods=['GET','POST'])
def workorders_detail(wid):
    wo = WorkOrder.query.get_or_404(wid)
    if request.method == 'POST':
        wo.status = request.form.get('status', wo.status)
        wo.priority = request.form.get('priority', wo.priority)
        wo.assignee = request.form.get('assignee')
        if wo.status == "已完成" and wo.closed_at is None:
            wo.closed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('workorders_detail', wid=wid))
    return render_template('workorders/detail.html', wo=wo)

# ---- 社区服务（公告） ----
@app.route('/announcements', methods=['GET','POST'])
def announcements():
    if request.method == 'POST':
        ann = Announcement(title=request.form['title'], content=request.form['content'], send_email=bool(request.form.get('send_email')))
        db.session.add(ann); db.session.commit()
        return redirect(url_for('announcements'))
    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements/list.html', anns=anns)

if __name__ == '__main__':
    app.run(debug=True)
