from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Tuple


@dataclass(frozen=True)
class SeedOwner:
    name: str
    phone: str
    email: str
    unit: str
    area: float
    unit_type: str
    vehicle_count: int
    parking_spots: str
    vehicles_json: str


@dataclass(frozen=True)
class SeedChargeType:
    name: str
    billing_cycle: str
    unit: str
    price: float
    link_to: str
    description: str


@dataclass(frozen=True)
class SeedEquipment:
    name: str
    equipment_type: str
    location: str
    serial: str
    status: str
    install_date: date


@dataclass(frozen=True)
class SeedAnnouncement:
    title: str
    content: str


def get_seed_data() -> Tuple[List[SeedOwner], List[SeedChargeType], List[SeedEquipment], List[SeedAnnouncement]]:
    """集中管理用于本项目 `init-db` 的自造测试数据。

    约定：
    - 主项目中任何“手写测试数据”都放在这里（其它文件不再写死测试数据）
    - `app.py` 只负责调用这里的数据来初始化数据库
    """

    owners = [
        SeedOwner(
            name="张三",
            phone="13800001111",
            email="zhangsan@example.com",
            unit="A-2-302",
            area=120.5,
            unit_type="三室两厅",
            vehicle_count=2,
            parking_spots="P-001,P-002",
            vehicles_json='[{"plate":"沪A12345","model":"Tesla 3"},{"plate":"沪B67890","model":"BMW X5"}]',
        ),
        SeedOwner(
            name="李四",
            phone="13900002222",
            email="lisi@example.com",
            unit="B-1-101",
            area=85.0,
            unit_type="两室一厅",
            vehicle_count=1,
            parking_spots="P-003",
            vehicles_json='[{"plate":"沪C11111","model":"Toyota Camry"}]',
        ),
        SeedOwner(
            name="王五",
            phone="13700003333",
            email="wangwu@example.com",
            unit="C-3-501",
            area=150.0,
            unit_type="四室及以上",
            vehicle_count=3,
            parking_spots="P-004,P-005,P-006",
            vehicles_json='[{"plate":"沪D22222","model":"Mercedes E300"},{"plate":"沪E33333","model":"Audi A6"},{"plate":"沪F44444","model":"Volkswagen Passat"}]',
        ),
        SeedOwner(
            name="赵六",
            phone="13600004444",
            email="zhaoliu@example.com",
            unit="A-1-102",
            area=62.0,
            unit_type="一室一厅",
            vehicle_count=0,
            parking_spots="",
            vehicles_json="[]",
        ),
        SeedOwner(
            name="钱七",
            phone="13500005555",
            email="qianqi@example.com",
            unit="B-2-808",
            area=98.6,
            unit_type="三室一厅",
            vehicle_count=1,
            parking_spots="P-007",
            vehicles_json='[{"plate":"沪G55555","model":"BYD Han"}]',
        ),
        SeedOwner(
            name="孙八",
            phone="13400006666",
            email="sunba@example.com",
            unit="C-2-206",
            area=110.2,
            unit_type="三室两厅",
            vehicle_count=2,
            parking_spots="P-008,P-009",
            vehicles_json='[{"plate":"沪H66666","model":"Toyota RAV4"},{"plate":"沪J77777","model":"Honda CR-V"}]',
        ),
        SeedOwner(
            name="周九",
            phone="13300007777",
            email="zhoujiu@example.com",
            unit="D-1-1201",
            area=142.3,
            unit_type="四室及以上",
            vehicle_count=1,
            parking_spots="P-010",
            vehicles_json='[{"plate":"沪K88888","model":"Audi Q5"}]',
        ),
        SeedOwner(
            name="吴十",
            phone="13200008888",
            email="wushi@example.com",
            unit="D-2-303",
            area=76.5,
            unit_type="两室一厅",
            vehicle_count=1,
            parking_spots="P-011",
            vehicles_json='[{"plate":"沪L99999","model":"Volkswagen Golf"}]',
        ),
    ]

    charge_types = [
        SeedChargeType(
            name="物业费",
            billing_cycle="月",
            unit="月",
            price=2.5,
            link_to="area",
            description="2.5元/㎡·月",
        ),
        SeedChargeType(
            name="停车费",
            billing_cycle="月",
            unit="月",
            price=300,
            link_to="vehicles",
            description="300元/月·辆",
        ),
        SeedChargeType(
            name="水费",
            billing_cycle="月",
            unit="月",
            price=4.2,
            link_to="none",
            description="示例：按户计费（演示用）",
        ),
        SeedChargeType(
            name="电费",
            billing_cycle="月",
            unit="月",
            price=0.62,
            link_to="none",
            description="示例：按户计费（演示用）",
        ),
        SeedChargeType(
            name="保洁服务费",
            billing_cycle="季",
            unit="季",
            price=120,
            link_to="none",
            description="每季度一次（演示用）",
        ),
    ]

    equipment = [
        SeedEquipment(
            name="1号电梯",
            equipment_type="电梯",
            location="A座",
            serial="EL-001",
            status="正常",
            install_date=date(2020, 1, 15),
        ),
        SeedEquipment(
            name="2号电梯",
            equipment_type="电梯",
            location="B座",
            serial="EL-002",
            status="正常",
            install_date=date(2020, 1, 15),
        ),
        SeedEquipment(
            name="3号电梯",
            equipment_type="电梯",
            location="C座",
            serial="EL-003",
            status="维护",
            install_date=date(2017, 9, 3),
        ),
        SeedEquipment(
            name="中央空调系统",
            equipment_type="空调",
            location="A座",
            serial="AC-001",
            status="正常",
            install_date=date(2019, 6, 1),
        ),
        SeedEquipment(
            name="B座空调主机",
            equipment_type="空调",
            location="B座",
            serial="AC-002",
            status="维护",
            install_date=date(2016, 5, 20),
        ),
        SeedEquipment(
            name="主水管",
            equipment_type="水管",
            location="地下层",
            serial="WP-001",
            status="正常",
            install_date=date(2018, 3, 10),
        ),
        SeedEquipment(
            name="A座支路水管",
            equipment_type="水管",
            location="A座地下管井",
            serial="WP-002",
            status="正常",
            install_date=date(2021, 11, 8),
        ),
        SeedEquipment(
            name="燃气管道",
            equipment_type="燃气",
            location="全小区",
            serial="GAS-001",
            status="正常",
            install_date=date(2018, 3, 10),
        ),
        SeedEquipment(
            name="燃气报警器",
            equipment_type="燃气",
            location="D座配电间",
            serial="GAS-AL-01",
            status="停用",
            install_date=date(2015, 7, 1),
        ),
    ]

    announcements = [
        SeedAnnouncement(
            title="停水通知",
            content="本周三9:00-12:00小区停水，请提前蓄水。",
        )
        ,
        SeedAnnouncement(
            title="电梯维护公告",
            content="C座3号电梯将于本周五10:00-16:00维护，期间请使用其他电梯或楼梯。",
        ),
        SeedAnnouncement(
            title="消防演练通知",
            content="下周二15:00进行消防演练，请各位业主配合参与，注意安全。",
        ),
    ]

    return owners, charge_types, equipment, announcements


# =========================================================
# Demo / Test mock data (used by files in `test/` folder)
# Put any hand-crafted demo lists here, keep other files clean.
# =========================================================

DEMO_OWNER_NAMES = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
DEMO_CHARGE_TYPES = ["物业费", "停车费", "水费", "电费"]
DEMO_PAYMENT_METHODS = ["线上", "线下", "现金", "银行转账"]
DEMO_EQUIPMENT_TYPES = ["电梯", "空调", "水管", "燃气"]
DEMO_EQUIPMENT_STATUSES = ["正常", "维护", "停用"]
DEMO_WORKORDER_STATUSES = ["新建", "处理中", "已完成", "已关闭"]

DEMO_OVERDUE_INVOICES = [
    {
        "id": 1,
        "owner_name": "张三",
        "amount": 500.00,
        "unpaid_amount": 500.00,
        "due_date": "2024-01-15",
        "days_overdue": 45,
    },
    {
        "id": 2,
        "owner_name": "李四",
        "amount": 300.00,
        "unpaid_amount": 300.00,
        "due_date": "2024-02-01",
        "days_overdue": 30,
    },
]

DEMO_INVOICE_STATS = {
    "total_amount": 50000.00,
    "paid_amount": 35000.00,
    "unpaid_amount": 15000.00,
    "payment_rate": 70.0,
    "total_count": 100,
    "paid_count": 70,
    "unpaid_count": 30,
}

DEMO_REVENUE_TREND = [
    {"period": "2024-01", "revenue": 12000, "total": 15000},
    {"period": "2024-02", "revenue": 13500, "total": 16000},
    {"period": "2024-03", "revenue": 14200, "total": 17000},
    {"period": "2024-04", "revenue": 15000, "total": 18000},
]

DEMO_PAYMENT_ANALYSIS = {
    "total_payments": 150,
    "total_amount": 35000.00,
    "by_method": {"线上": 20000.00, "线下": 10000.00, "现金": 5000.00},
    "by_month": [
        {"month": "2024-01", "amount": 12000},
        {"month": "2024-02", "amount": 13500},
        {"month": "2024-03", "amount": 14200},
    ],
}

DEMO_EQUIPMENT_STATUS_DIST = {"正常": 15, "维护": 3, "停用": 2}

DEMO_WORKORDER_STATS = {
    "total": 50,
    "completed": 35,
    "in_progress": 10,
    "new": 5,
    "completion_rate": 70.0,
}

