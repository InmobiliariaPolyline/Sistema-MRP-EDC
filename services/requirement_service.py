from sqlalchemy.orm import Session
from models.warehouse import Warehouse
from models.requirement import Requirement, RequirementItem
from services.inventory_service import reserve_stock
from datetime import datetime

def create_requirement(db: Session, warehouse_id, items, budget_id=None, owner_id=None):
    """
    items = [
        {"material_id": 1, "qty": 10},
        {"material_id": 2, "qty": 5}
    ]
    budget_id: opcional, vincula el requerimiento a un proyecto.
    """

    obra = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not obra:
        return False, "Almacén de obra no encontrado."
    if owner_id is not None and obra.owner_id != owner_id:
        return False, "No tienes permiso para usar este almacén."

    principal_warehouse = db.query(Warehouse).filter(
        Warehouse.owner_id == obra.owner_id,
        Warehouse.type == "principal"
    ).first()

    if not principal_warehouse:
        return False, "No hay almacén principal configurado. Por favor crea uno primero."

    if not budget_id:
        return False, "Debes seleccionar un proyecto. El proyecto es obligatorio."

    from models.budget import Budget
    _bud = db.query(Budget).filter(Budget.id == budget_id).first()
    if not _bud:
        return False, "El proyecto seleccionado no existe."
    budget_name = _bud.name

    requirement = Requirement(
        warehouse_id_obra=warehouse_id,
        created_at=datetime.now(),
        status="pending",
        budget_id=budget_id,
        budget_name=budget_name,
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    for item in items:
        material_id = item["material_id"]
        qty = item["qty"]

        reserved = reserve_stock(db, principal_warehouse.id, material_id, qty)

        req_item = RequirementItem(
            requirement_id=requirement.id,
            material_id=material_id,
            requested_qty=qty,
            fulfilled_qty=0,
            status="reserved" if reserved else "pending"
        )

        db.add(req_item)

    # El requerimiento siempre inicia en "pending" — solo pasa a "fulfilled" tras un despacho exitoso
    db.commit()

    return True, "Requerimiento creado exitosamente"



def get_requirements(db: Session, skip: int = 0, limit: int = 10,
                    requirement_id: int = None, status: str = None,
                    start_date = None, end_date = None,
                    warehouse_ids: list = None):
    
    
    
    """
    Obtiene requerimientos con filtros y paginación
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        requirement_id: Filtrar por ID de requerimiento
        status: Filtrar por estado (pending, fulfilled, partial, cancelled)
        start_date: Filtrar desde esta fecha
        end_date: Filtrar hasta esta fecha
    """
    query = db.query(Requirement)

    if warehouse_ids is not None:
        query = query.filter(Requirement.warehouse_id_obra.in_(warehouse_ids))

    if requirement_id:
        query = query.filter(Requirement.id == requirement_id)

    if status:
        query = query.filter(Requirement.status == status)

    if start_date:
        query = query.filter(Requirement.created_at >= start_date)

    if end_date:
        query = query.filter(Requirement.created_at <= end_date)
    
    # Ordenar por fecha descendente
    query = query.order_by(Requirement.created_at.desc())
    
    # Obtener total de registros antes de paginar
    total_count = query.count()
    
    # Aplicar paginación
    requirements = query.offset(skip).limit(limit).all()
    
    return requirements, total_count

def get_requirement_detail(db: Session, requirement_id):
    return db.query(Requirement).filter(
        Requirement.id == requirement_id
    ).first()
    
from services.inventory_service import release_reservation

def cancel_requirement(db: Session, requirement_id, reason: str = None, owner_id=None):
    req = get_requirement_detail(db, requirement_id)

    if not req:
        return False

    obra = db.query(Warehouse).filter(Warehouse.id == req.warehouse_id_obra).first()
    if owner_id is not None and (not obra or obra.owner_id != owner_id):
        return False

    # Obtener el almacén principal del dueño del almacén de obra
    principal = (
        db.query(Warehouse)
        .filter(Warehouse.owner_id == obra.owner_id, Warehouse.type == "principal")
        .first()
        if obra else None
    )

    for item in req.items:
        if item.status in ("reserved", "partial") and principal:
            release_reservation(
                db,
                principal.id,
                item.material_id,
                max(0, item.requested_qty - item.fulfilled_qty),
            )

    req.status = "cancelled"
    if reason:
        req.notes = reason
    db.commit()
    return True


def reprocess_requirements(db: Session):
    # from models.requirement import Requirement
    # from models.warehouse import Warehouse
    # from services.inventory_service import reserve_stock

    # Procesar solo requerimientos aún no despachados
    requirements = db.query(Requirement).filter(
        Requirement.status.in_(["pending", "partial"])
    ).all()

    newly_all_reserved = []

    for req in requirements:
        obra = db.query(Warehouse).filter(Warehouse.id == req.warehouse_id_obra).first()
        if not obra:
            continue

        principal = db.query(Warehouse).filter(
            Warehouse.owner_id == obra.owner_id,
            Warehouse.type == "principal"
        ).first()
        if not principal:
            continue

        had_pending = any(item.status == "pending" for item in req.items)

        for item in req.items:
            if item.status == "pending":
                success = reserve_stock(
                    db,
                    principal.id,
                    item.material_id,
                    item.requested_qty
                )
                if success:
                    item.status = "reserved"

        # Notificación: todos los ítems pasaron a tener stock reservado
        if had_pending:
            all_ready = all(
                item.status in ("reserved", "fulfilled")
                for item in req.items
            )
            if all_ready:
                newly_all_reserved.append(req)

        # El status padre (pending/partial) NO cambia aquí —
        # solo cambia a "fulfilled" cuando se crea un despacho exitoso

    db.commit()
    return newly_all_reserved
