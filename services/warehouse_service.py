from sqlalchemy.orm import Session
from models.warehouse import Warehouse

def create_warehouse(db: Session, name, type, location, owner_id=None, address=None):
    already_exists = db.query(Warehouse).filter(
        Warehouse.name == name,
        Warehouse.owner_id == owner_id
    ).first()
    if already_exists:
        return {"error": "El almacén ya existe"}
    warehouse = Warehouse(name=name, type=type, location=location, address=address, owner_id=owner_id)
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return {"value": warehouse}

def get_warehouses(db: Session, owner_id=None):
    """Retorna almacenes. Si owner_id se especifica, filtra por propietario."""
    q = db.query(Warehouse)
    if owner_id is not None:
        q = q.filter(Warehouse.owner_id == owner_id)
    return q.all()

def get_warehouse(db: Session, warehouse_id):
    return db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

def get_warehouses_by_owner(db: Session, owner_id: int):
    return db.query(Warehouse).filter(Warehouse.owner_id == owner_id).all()

def get_owner_warehouse_ids(db: Session, owner_id: int) -> list[int]:
    """Retorna lista de IDs de almacenes de un propietario."""
    rows = db.query(Warehouse.id).filter(Warehouse.owner_id == owner_id).all()
    return [r[0] for r in rows]

def delete_warehouse(db: Session, warehouse_id):
    from models.requirement import Requirement
    from services.requirement_service import cancel_requirement

    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        return

    # Cancelar requerimientos activos asociados a este almacén de obra
    active_reqs = (
        db.query(Requirement)
        .filter(
            Requirement.warehouse_id_obra == warehouse_id,
            Requirement.status.notin_(["cancelled", "fulfilled"]),
        )
        .all()
    )
    for req in active_reqs:
        cancel_requirement(db, req.id, reason=f"Almacén eliminado: {warehouse.name}")

    db.delete(warehouse)
    db.commit()

def update_warehouse(db: Session, warehouse_id, name, type, location, address=None):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if warehouse:
        exists = db.query(Warehouse).filter(
            Warehouse.name == name,
            Warehouse.owner_id == warehouse.owner_id,
            Warehouse.id != warehouse_id
        ).first()
        if exists:
            return {"error": "Otro almacén con ese nombre ya existe"}
        warehouse.name = name
        warehouse.type = type
        warehouse.location = location
        warehouse.address = address
        db.commit()
        return {"value": "Almacén actualizado correctamente"}
