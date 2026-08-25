from sqlalchemy.orm import Session
from sqlalchemy import func
from models.inventory import Inventory
from models.requirement import Requirement
from models.movement import Movement
from models.warehouse import Warehouse
from datetime import datetime, date, timedelta


def get_kpis(db: Session, owner_id: int = None):
    """KPIs generales. Si owner_id se pasa, filtra solo los almacenes del cliente."""
    inv_q = db.query(Inventory).filter(Inventory.is_active == True)
    wh_filter_ids = None

    if owner_id is not None:
        wh_filter_ids = [
            r[0] for r in db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
        ]
        inv_q = inv_q.filter(Inventory.warehouse_id.in_(wh_filter_ids))


    # total_stock = sum([s[0] for s in total_stock])
    
    # critical = (
    #     db.query(Inventory)

    #     .join(Inventory.warehouse)
    #     .filter(Warehouse.type == "principal", Inventory.stock <= 5)
    #     .count()
    # )
    total_stock = sum(s[0] for s in inv_q.with_entities(Inventory.stock).all())

    crit_q = db.query(Inventory).join(Inventory.warehouse).filter(
        Warehouse.type == "principal",
        Inventory.stock <= 5,
        Inventory.is_active == True,
    )
    if wh_filter_ids is not None:
        crit_q = crit_q.filter(Inventory.warehouse_id.in_(wh_filter_ids))
    critical = crit_q.count()


    # today = date.today()


    # dispatch_today = db.query(Movement).filter(
    #     Movement.movement_type == "OUT"
    # ).count()
    req_q = db.query(Requirement).filter(Requirement.status.in_(["pending", "partial"]))
    if wh_filter_ids is not None:
        req_q = req_q.filter(Requirement.warehouse_id_obra.in_(wh_filter_ids))
    pending_req = req_q.count()

    mov_q = db.query(Movement).filter(Movement.movement_type == "OUT")
    if wh_filter_ids is not None:
        mov_q = mov_q.filter(Movement.warehouse_id.in_(wh_filter_ids))
    dispatch_today = mov_q.count()

    return {
        "total_stock": total_stock,
        "critical": critical,
        "pending_req": pending_req,
        "dispatch_today": dispatch_today,
    }


    #Movimientos recientes
# def get_recent_movements(db: Session):
#     return db.query(Movement).order_by(
#         Movement.timestamp.desc()
#     ).limit(10).all()



# def get_stock_by_warehouse(db: Session):
#     data = db.query(Inventory).all()


def get_recent_movements(db: Session, owner_id: int = None):
    q = db.query(Movement)
    if owner_id is not None:
        wh_ids = [
            r[0] for r in db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
        ]
        q = q.filter(Movement.warehouse_id.in_(wh_ids))
    return q.order_by(Movement.timestamp.desc()).limit(10).all()


def get_stock_by_warehouse(db: Session, owner_id: int = None):
    q = db.query(Inventory)
    if owner_id is not None:
        wh_ids = [
            r[0] for r in db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
        ]
        q = q.filter(Inventory.warehouse_id.in_(wh_ids))
    result = {}
    for inv in q.all():
        name = inv.warehouse.name
        result[name] = result.get(name, 0) + inv.stock
    return result


def get_movements_last_7_days(db: Session, owner_id: int = None):
    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    wh_ids = None
    if owner_id is not None:
        wh_ids = [
            r[0] for r in db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
        ]

    result = []
    for day in days:
        start = datetime(day.year, day.month, day.day, 0, 0, 0)
        end   = datetime(day.year, day.month, day.day, 23, 59, 59)

        def _count(mtype):
            q = db.query(Movement).filter(
                Movement.movement_type == mtype,
                Movement.timestamp >= start,
                Movement.timestamp <= end,
            )
            if wh_ids is not None:
                q = q.filter(Movement.warehouse_id.in_(wh_ids))
            return q.count()

        result.append({
            "Día": day.strftime("%d/%m"),
            "Entradas": _count("IN"),
            "Salidas": _count("OUT"),
        })
    return result


def get_top_materials_by_movement(db: Session, limit: int = 5, owner_id: int = None):
    q = db.query(Movement.material_id, func.count(Movement.id).label("total"))
    if owner_id is not None:
        wh_ids = [
            r[0] for r in db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
        ]
        q = q.filter(Movement.warehouse_id.in_(wh_ids))
    rows = q.group_by(Movement.material_id).order_by(func.count(Movement.id).desc()).limit(limit).all()

    from models.material import Material
    result = []
    for r in rows:
        mat = db.query(Material).filter(Material.id == r.material_id).first()
        if mat:
            result.append({"Material": mat.name, "Movimientos": r.total})

    return result
