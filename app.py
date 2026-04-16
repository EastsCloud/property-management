from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from config import Config
from models import db, Owner, ChargeType, Invoice, Payment, Equipment, MaintenancePlan, WorkOrder, Announcement, MaintenanceRecord
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from test_data import get_seed_data


def get_invoice_paid_map(invoice_ids=None):
    """Return {invoice_id: total_paid} using one aggregate query."""
    from sqlalchemy import func

    q = db.session.query(
        Payment.invoice_id,
        func.coalesce(func.sum(Payment.amount), 0.0).label("total_paid"),
    ).filter(Payment.invoice_id.isnot(None))
    if invoice_ids:
        q = q.filter(Payment.invoice_id.in_(list(invoice_ids)))
    q = q.group_by(Payment.invoice_id)
    return {int(iid): float(total) for iid, total in q.all()}

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# language
@app.before_request
def set_language():
    lang = request.args.get('lang')
    if lang in {'en', 'zh'}:
        session['lang'] = lang
    session.setdefault('lang', 'zh')

def render_view(template_name, **kwargs):
    tpl = f"en/{template_name}" if session.get('lang') == 'en' else template_name
    return render_template(tpl, **kwargs)

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        owners_seed, charge_types_seed, equipment_seed, announcements_seed = get_seed_data()

        owners = [
            Owner(
                name=o.name,
                phone=o.phone,
                email=o.email,
                unit=o.unit,
                area=o.area,
                unit_type=o.unit_type,
                vehicle_count=o.vehicle_count,
                parking_spots=o.parking_spots,
                vehicles=o.vehicles_json,
            )
            for o in owners_seed
        ]

        charge_types = [
            ChargeType(
                name=ct.name,
                billing_cycle=ct.billing_cycle,
                unit=ct.unit,
                price=ct.price,
                link_to=ct.link_to,
                description=ct.description,
            )
            for ct in charge_types_seed
        ]

        db.session.add_all(owners + charge_types)
        db.session.commit()

        equipment_items = [
            Equipment(
                name=eq.name,
                equipment_type=eq.equipment_type,
                location=eq.location,
                serial=eq.serial,
                status=eq.status,
                install_date=eq.install_date,
            )
            for eq in equipment_seed
        ]

        for eq in equipment_items:
            if eq.install_date:
                eq.usage_years = (date.today() - eq.install_date).days / 365.25

        plan = None
        if equipment_items:
            plan = MaintenancePlan(
                equipment=equipment_items[0],
                frequency="每季度",
                next_date=date.today() + relativedelta(months=3),
            )

        announcements = [Announcement(title=a.title, content=a.content) for a in announcements_seed]

        db.session.add_all(equipment_items + ([plan] if plan else []) + announcements)
        db.session.commit()
        print("数据库已初始化")

@app.route('/')
def dashboard():
    owners = Owner.query.count()
    unpaid = Invoice.query.filter(Invoice.status!="已支付").count()
    today = date.today()
    overdue = Invoice.query.filter(
        Invoice.status != "已支付",
        Invoice.due_date < today,
        (Invoice.unpaid_amount > 0) | (Invoice.unpaid_amount.is_(None)),
    ).count()
    open_wos = WorkOrder.query.filter(WorkOrder.status!="已完成").count()
    equips = Equipment.query.count()
    latest_ann = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    recent_wos = WorkOrder.query.order_by(WorkOrder.created_at.desc()).limit(8).all()
    move_outs = Owner.query.order_by(Owner.created_at.desc()).limit(10).all()   # placeholder
    return render_view('dashboard.html', owners=owners, unpaid=unpaid, overdue=overdue, open_wos=open_wos, equips=equips, latest_ann=latest_ann, recent_wos=recent_wos, move_outs=move_outs)

@app.route('/owners')
def owners_list():
    q = request.args.get('q','').strip()
    query = Owner.query
    if q:
        like = f"%{q}%"
        query = query.filter((Owner.name.like(like)) | (Owner.phone.like(like)) | (Owner.unit.like(like)))
    owners = query.order_by(Owner.id.desc()).all()
    return render_view('owners/list.html', owners=owners, q=q)

@app.route('/owners/new', methods=['GET','POST'])
def owners_new():
    if request.method == 'POST':
        vehicles = request.form.get('vehicles_json') or "[]"
        owner = Owner(
            name=request.form['name'],
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            unit=request.form.get('unit'),
            area=float(request.form.get('area') or 0),
            unit_type=request.form.get('unit_type'),
            vehicles=vehicles,
            vehicle_count=int(request.form.get('vehicle_count') or 0),
            parking_spots=request.form.get('parking_spots')
        )
        db.session.add(owner)
        db.session.commit()
        flash('已创建业主', 'success')
        return redirect(url_for('owners_list'))
    return render_view('owners/new.html')

@app.route('/owners/<int:oid>', methods=['GET','POST'])
def owners_detail(oid):
    owner = Owner.query.get_or_404(oid)
    if request.method == 'POST':
        owner.name = request.form['name']
        owner.phone = request.form.get('phone')
        owner.email = request.form.get('email')
        owner.unit = request.form.get('unit')
        owner.area = float(request.form.get('area') or 0)
        owner.unit_type = request.form.get('unit_type')
        owner.vehicles = request.form.get('vehicles_json') or "[]"
        owner.vehicle_count = int(request.form.get('vehicle_count') or 0)
        owner.parking_spots = request.form.get('parking_spots')
        db.session.commit()
        flash('已保存', 'success')
        return redirect(url_for('owners_detail', oid=oid))
    invoices = Invoice.query.filter_by(owner_id=oid).all()
    payments = Payment.query.filter_by(owner_id=oid).all()
    wos = WorkOrder.query.filter_by(owner_id=oid).all()
    return render_view('owners/detail.html', owner=owner, invoices=invoices, payments=payments, wos=wos)

@app.route('/owners/<int:oid>/delete', methods=['POST'])
def owners_delete(oid):
    owner = Owner.query.get_or_404(oid)
    db.session.delete(owner)
    db.session.commit()
    flash('已删除', 'warning')
    return redirect(url_for('owners_list'))

@app.route('/billing/charge-types')
def charge_types():
    types = ChargeType.query.order_by(ChargeType.id.desc()).all()
    return render_view('billing/charge_types.html', types=types)

@app.route('/billing/charge-types/new', methods=['GET','POST'])
def charge_types_new():
    if request.method == 'POST':
        ct = ChargeType(
            name=request.form['name'],
            billing_cycle=request.form.get('billing_cycle', '月'),
            unit=request.form.get('billing_cycle', '月'),
            price=float(request.form.get('price') or 0),
            link_to=request.form.get('link_to', 'none'),
            description=request.form.get('description')
        )
        db.session.add(ct); db.session.commit()
        flash('已创建收费项目', 'success')
        return redirect(url_for('charge_types'))
    return render_view('billing/charge_types_new.html')

@app.route('/billing/invoices')
def invoices_list():
    q = request.args.get('q','').strip()
    status = request.args.get('status','')
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Invoice.due_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
    invoices = pagination.items

    invoice_ids = [inv.id for inv in invoices]
    invoice_paid = get_invoice_paid_map(invoice_ids)

    today = date.today()
    overdue_count = Invoice.query.filter(
        Invoice.status != "已支付",
        Invoice.due_date < today,
        (Invoice.unpaid_amount > 0) | (Invoice.unpaid_amount.is_(None)),
    ).count()

    return render_view(
        "billing/invoices.html",
        invoices=invoices,
        q=q,
        status=status,
        invoice_paid=invoice_paid,
        pagination=pagination,
        today=today,
        overdue_count=overdue_count,
    )

@app.route('/billing/invoices/new', methods=['GET','POST'])
def invoices_new():
    owners = Owner.query.all()
    types = ChargeType.query.all()
    if request.method == 'POST':
        owner = Owner.query.get(int(request.form['owner_id']))
        charge_type = ChargeType.query.get(int(request.form['charge_type_id']))
        
        # 根据收费项目的关联类型自动计算
        if charge_type.link_to == 'area':
            quantity = owner.area or 0
        elif charge_type.link_to == 'vehicles':
            quantity = owner.vehicle_count or 0
        else:
            quantity = 1  # 其他类型默认数量为1
        
        # 单价从收费项目自动获取，但可以修改
        price = float(request.form.get('price') or charge_type.price or 0)
        amount = price * quantity
        unpaid_amount = amount
        
        inv = Invoice(
            owner_id=int(request.form['owner_id']),
            charge_type_id=int(request.form['charge_type_id']),
            billing_cycle=request.form.get('billing_cycle', charge_type.billing_cycle or '月'),
            quantity=quantity,
            price=price,
            amount=amount,
            unpaid_amount=unpaid_amount,
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(),
            description=request.form.get('description')
        )
        db.session.add(inv); db.session.commit()
        return redirect(url_for('invoices_list'))
    return render_view('billing/invoices_new.html', owners=owners, types=types)

@app.route('/billing/payments')
def payments_list():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    payments_pagination = Payment.query.order_by(Payment.paid_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    payments = payments_pagination.items

    invoice_ids = {p.invoice_id for p in payments if p.invoice_id}
    invoice_paid = get_invoice_paid_map(invoice_ids)

    return render_view(
        "billing/payments.html",
        payments=payments,
        invoice_paid=invoice_paid,
        pagination=payments_pagination,
    )

@app.route('/billing/payments/new', methods=['GET','POST'])
def payments_new():
    if request.method == 'POST':
        p = Payment(
            owner_id=int(request.form['owner_id']), 
            invoice_id=int(request.form['invoice_id']) if request.form.get('invoice_id') else None, 
            amount=float(request.form['amount']), 
            method=request.form.get('method'), 
            note=request.form.get('note')
        )
        inv_id = request.form.get('invoice_id')
        if inv_id:
            inv = Invoice.query.get(int(inv_id))
            if inv:
                from sqlalchemy import func
                existing_paid = db.session.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter(Payment.invoice_id == int(inv_id)).scalar() or 0.0
                total_paid = float(existing_paid) + float(p.amount)
                
                # 更新未付金额
                inv.unpaid_amount = max(0, inv.amount - total_paid)
                
                # 如果已缴费金额大于等于账单金额，标记为已支付
                if total_paid >= inv.amount:
                    inv.status = "已支付"
                    inv.unpaid_amount = 0
        db.session.add(p); db.session.commit()
        flash('已记录缴费', 'success')
        return redirect(url_for('payments_list'))
    
    owners = Owner.query.all()
    invoices = Invoice.query.filter(Invoice.status!="已支付").all()
    invoice_paid = get_invoice_paid_map([inv.id for inv in invoices])
    return render_view('billing/payments_new.html', owners=owners, invoices=invoices, invoice_paid=invoice_paid)

@app.route('/equipment')
def equipment_list():
    q = request.args.get('q','').strip()
    query = Equipment.query
    if q:
        like = f"%{q}%"
        query = query.filter((Equipment.name.like(like)) | (Equipment.location.like(like)) | (Equipment.serial.like(like)))
    items = query.order_by(Equipment.id.desc()).all()
    return render_view('equipment/list.html', items=items, q=q)

@app.route('/equipment/new', methods=['GET','POST'])
def equipment_new():
    if request.method == 'POST':
        install_date = datetime.strptime(request.form['install_date'], '%Y-%m-%d').date() if request.form.get('install_date') else None
        usage_years = None
        if install_date:
            from dateutil.relativedelta import relativedelta
            usage_years = (date.today() - install_date).days / 365.25
        
        item = Equipment(
            name=request.form['name'],
            equipment_type=request.form.get('equipment_type'),
            model=request.form.get('model'),
            location=request.form.get('location'),
            serial=request.form.get('serial'),
            status=request.form.get('status'),
            install_date=install_date,
            usage_years=usage_years
        )
        db.session.add(item); db.session.commit()
        return redirect(url_for('equipment_list'))
    return render_view('equipment/new.html')

@app.route('/equipment/<int:eid>', methods=['GET','POST'])
def equipment_detail(eid):
    eq = Equipment.query.get_or_404(eid)
    if request.method == 'POST':
        eq.name = request.form['name']
        eq.equipment_type = request.form.get('equipment_type')
        eq.model = request.form.get('model')
        eq.location = request.form.get('location')
        eq.serial = request.form.get('serial')
        eq.status = request.form.get('status')
        if request.form.get('install_date'):
            install_date = datetime.strptime(request.form['install_date'], '%Y-%m-%d').date()
            eq.install_date = install_date
            from dateutil.relativedelta import relativedelta
            eq.usage_years = (date.today() - install_date).days / 365.25
        db.session.commit()
        return redirect(url_for('equipment_detail', eid=eid))
    plans = MaintenancePlan.query.filter_by(equipment_id=eid).all()
    wos = WorkOrder.query.filter_by(equipment_id=eid).all()
    records = MaintenanceRecord.query.filter_by(equipment_id=eid).order_by(MaintenanceRecord.repair_date.desc()).all()
    return render_view('equipment/detail.html', eq=eq, plans=plans, wos=wos, records=records)

@app.route('/equipment/<int:eid>/plan/new', methods=['POST'])
def plan_new(eid):
    plan = MaintenancePlan(equipment_id=eid, frequency=request.form.get('frequency'), next_date=datetime.strptime(request.form['next_date'], '%Y-%m-%d').date() if request.form.get('next_date') else None, notes=request.form.get('notes'))
    db.session.add(plan); db.session.commit()
    return redirect(url_for('equipment_detail', eid=eid))

@app.route('/equipment/<int:eid>/maintenance/new', methods=['POST'])
def maintenance_record_new(eid):
    record = MaintenanceRecord(
        equipment_id=eid,
        repair_date=datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date(),
        main_issue=request.form.get('main_issue'),
        repair_cost=float(request.form.get('repair_cost') or 0),
        is_fixed=bool(request.form.get('is_fixed')),
        is_replaced=bool(request.form.get('is_replaced')),
        notes=request.form.get('notes')
    )
    db.session.add(record); db.session.commit()
    return redirect(url_for('equipment_detail', eid=eid))

@app.route('/workorders')
def workorders_list():
    status = request.args.get('status','')
    query = WorkOrder.query
    if status:
        query = query.filter_by(status=status)
    wos = query.order_by(WorkOrder.created_at.desc()).all()
    return render_view('workorders/list.html', wos=wos, status=status)

@app.route('/workorders/new', methods=['GET','POST'])
def workorders_new():
    owners = Owner.query.all()
    equips = Equipment.query.all()
    if request.method == 'POST':
        wo = WorkOrder(
            type=request.form.get('type'),
            description=request.form['description'],
            status=request.form.get('status','新建'),
            priority=request.form.get('priority','中'),
            owner_id=int(request.form['owner_id']) if request.form.get('owner_id') else None,
            equipment_id=int(request.form['equipment_id']) if request.form.get('equipment_id') else None,
            assignee=request.form.get('assignee'),
            repairer=request.form.get('repairer')
        )
        if request.form.get('assigned_at'):
            # 处理两种格式：'2025-12-03T22:07' 或 '2025-12-03 22:07'
            assigned_str = request.form['assigned_at'].replace('T', ' ')
            if len(assigned_str) == 16:  # '2025-12-03 22:07'
                wo.assigned_at = datetime.strptime(assigned_str, '%Y-%m-%d %H:%M')
            else:
                wo.assigned_at = datetime.strptime(assigned_str, '%Y-%m-%d %H:%M:%S')
        db.session.add(wo); db.session.commit()
        return redirect(url_for('workorders_list'))
    return render_view('workorders/new.html', owners=owners, equips=equips)

@app.route('/workorders/<int:wid>', methods=['GET','POST'])
def workorders_detail(wid):
    wo = WorkOrder.query.get_or_404(wid)
    if request.method == 'POST':
        wo.status = request.form.get('status', wo.status)
        wo.priority = request.form.get('priority', wo.priority)
        wo.assignee = request.form.get('assignee')
        wo.repairer = request.form.get('repairer')
        wo.satisfaction = request.form.get('satisfaction')
        
        if request.form.get('assigned_at'):
            # 处理两种格式：'2025-12-03T22:07' 或 '2025-12-03 22:07'
            assigned_str = request.form['assigned_at'].replace('T', ' ')
            if len(assigned_str) == 16:  # '2025-12-03 22:07'
                wo.assigned_at = datetime.strptime(assigned_str, '%Y-%m-%d %H:%M')
            else:
                wo.assigned_at = datetime.strptime(assigned_str, '%Y-%m-%d %H:%M:%S')
        if request.form.get('completed_at'):
            # 处理两种格式
            completed_str = request.form['completed_at'].replace('T', ' ')
            if len(completed_str) == 16:
                wo.completed_at = datetime.strptime(completed_str, '%Y-%m-%d %H:%M')
            else:
                wo.completed_at = datetime.strptime(completed_str, '%Y-%m-%d %H:%M:%S')
        
        if wo.status == "已完成" and wo.closed_at is None:
            wo.closed_at = datetime.utcnow()
            if wo.completed_at is None:
                wo.completed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('workorders_detail', wid=wid))
    return render_view('workorders/detail.html', wo=wo)

@app.route('/announcements', methods=['GET','POST'])
def announcements():
    if request.method == 'POST':
        ann = Announcement(title=request.form['title'], content=request.form['content'], send_email=bool(request.form.get('send_email')))
        db.session.add(ann); db.session.commit()
        return redirect(url_for('announcements'))
    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_view('announcements/list.html', anns=anns)

## ===== 数据分析 Analytics =====

@app.route('/analytics')
def analytics_dashboard():
    return render_view('analytics/dashboard.html')

@app.route('/api/analytics/revenue')
def api_analytics_revenue():
    """收入趋势：按月汇总已支付金额"""
    from sqlalchemy import func, extract
    results = db.session.query(
        extract('year', Payment.paid_at).label('year'),
        extract('month', Payment.paid_at).label('month'),
        func.sum(Payment.amount).label('total')
    ).group_by('year', 'month').order_by('year', 'month').all()
    labels = [f"{int(r.year)}-{int(r.month):02d}" for r in results]
    data = [round(r.total, 2) for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/invoice_status')
def api_analytics_invoice_status():
    """账单状态分布"""
    from sqlalchemy import func
    results = db.session.query(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).all()
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/charge_type_revenue')
def api_analytics_charge_type_revenue():
    """各收费项目收入对比"""
    from sqlalchemy import func
    results = db.session.query(
        ChargeType.name,
        func.sum(Invoice.amount).label('total')
    ).join(Invoice, Invoice.charge_type_id == ChargeType.id
    ).group_by(ChargeType.name).all()
    labels = [r[0] for r in results]
    data = [round(r.total, 2) for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/equipment_status')
def api_analytics_equipment_status():
    """设备状态分布"""
    from sqlalchemy import func
    results = db.session.query(Equipment.status, func.count(Equipment.id)).group_by(Equipment.status).all()
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/equipment_type')
def api_analytics_equipment_type():
    """设备类型分布"""
    from sqlalchemy import func
    results = db.session.query(Equipment.equipment_type, func.count(Equipment.id)).group_by(Equipment.equipment_type).all()
    labels = [r[0] or '未分类' for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/workorder_status')
def api_analytics_workorder_status():
    """工单状态分布"""
    from sqlalchemy import func
    results = db.session.query(WorkOrder.status, func.count(WorkOrder.id)).group_by(WorkOrder.status).all()
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/workorder_type')
def api_analytics_workorder_type():
    """工单类型分布"""
    from sqlalchemy import func
    results = db.session.query(WorkOrder.type, func.count(WorkOrder.id)).group_by(WorkOrder.type).all()
    labels = [r[0] or '未分类' for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/workorder_satisfaction')
def api_analytics_workorder_satisfaction():
    """工单满意度分布"""
    from sqlalchemy import func
    results = db.session.query(WorkOrder.satisfaction, func.count(WorkOrder.id)).filter(
        WorkOrder.satisfaction.isnot(None), WorkOrder.satisfaction != ''
    ).group_by(WorkOrder.satisfaction).all()
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/owner_area')
def api_analytics_owner_area():
    """业主房屋面积分布"""
    owners = Owner.query.all()
    buckets = {'<60㎡': 0, '60-90㎡': 0, '90-120㎡': 0, '120-150㎡': 0, '>150㎡': 0}
    for o in owners:
        a = o.area or 0
        if a < 60: buckets['<60㎡'] += 1
        elif a < 90: buckets['60-90㎡'] += 1
        elif a < 120: buckets['90-120㎡'] += 1
        elif a < 150: buckets['120-150㎡'] += 1
        else: buckets['>150㎡'] += 1
    return jsonify(labels=list(buckets.keys()), data=list(buckets.values()))

@app.route('/api/analytics/payment_method')
def api_analytics_payment_method():
    """缴费方式分布"""
    from sqlalchemy import func
    results = db.session.query(Payment.method, func.count(Payment.id)).group_by(Payment.method).all()
    labels = [r[0] or '未知' for r in results]
    data = [r[1] for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/maintenance_cost')
def api_analytics_maintenance_cost():
    """维修费用趋势"""
    from sqlalchemy import func, extract
    results = db.session.query(
        extract('year', MaintenanceRecord.repair_date).label('year'),
        extract('month', MaintenanceRecord.repair_date).label('month'),
        func.sum(MaintenanceRecord.repair_cost).label('total')
    ).group_by('year', 'month').order_by('year', 'month').all()
    labels = [f"{int(r.year)}-{int(r.month):02d}" for r in results]
    data = [round(r.total, 2) for r in results]
    return jsonify(labels=labels, data=data)

@app.route('/api/analytics/unpaid_overview')
def api_analytics_unpaid_overview():
    """各业主欠费情况"""
    from sqlalchemy import func
    results = db.session.query(
        Owner.name,
        func.sum(Invoice.unpaid_amount).label('unpaid')
    ).join(Invoice, Invoice.owner_id == Owner.id
    ).filter(Invoice.unpaid_amount > 0
    ).group_by(Owner.name).all()
    labels = [r[0] for r in results]
    data = [round(r.unpaid, 2) for r in results]
    return jsonify(labels=labels, data=data)

if __name__ == '__main__':
    app.run(debug=True)
