from sqlalchemy.orm import Session
from models.material import Material
from datetime import datetime

# Crear
def create_material(db: Session, code, name, unit, description,
                    unit_price: float = 0.0, unit_price_dolares: float = 0.0):
    existing_code = db.query(Material).filter(Material.code == code).first()
    if existing_code:
        return False, 'code'

    existing_name = db.query(Material).filter(Material.name == name).first()
    if existing_name:
        return False, 'name'

    material = Material(
        code=code,
        name=name,
        unit=unit,
        description=description,
        unit_price=max(0.0, float(unit_price or 0)),
        unit_price_dolares=max(0.0, float(unit_price_dolares or 0)),
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return True, material

# Listar — más recientes primero
def get_materials(db: Session):
    return db.query(Material).order_by(Material.id.desc()).all()

def get_materials_filtered(db: Session, skip: int=0, limit:int =10,
                           code_filter: str = None, name_filter: str = None, unit_filter: str = None):
    query = db.query(Material)

    if code_filter:
        query = query.filter(Material.code.ilike(f"%{code_filter}%"))
    if name_filter:
        query = query.filter(Material.name.ilike(f"%{name_filter}%"))
    if unit_filter:
        query = query.filter(Material.unit.ilike(f"%{unit_filter}%"))

    #Obtener total de materiales antes de paginar
    total_count = query.count()

    #Aplicar paginación
    materials = query.offset(skip).limit(limit).all()


    return materials, total_count

def get_materials_filtered(db: Session, skip: int=0, limit:int =10,
                           code_filter: str = None, name_filter: str = None, unit_filter: str = None):
    query = db.query(Material)

    if code_filter:
        query = query.filter(Material.code.ilike(f"%{code_filter}%"))
    if name_filter:
        query = query.filter(Material.name.ilike(f"%{name_filter}%"))
    if unit_filter:
        query = query.filter(Material.unit.ilike(f"%{unit_filter}%"))

    #Obtener total de materiales antes de paginar
    total_count = query.count()

    #Aplicar paginación
    materials = query.offset(skip).limit(limit).all()


    return materials, total_count

# Eliminar
def delete_material(db: Session, material_id):
    material = db.query(Material).filter(Material.id == material_id).first()
    if material:
        db.delete(material)
        db.commit()

def delete_material_code(db: Session, code, user_id=None):
    from models.requirement import RequirementItem, Requirement
    from models.inventory import Inventory
    from models.movement import Movement
    from models.warehouse import Warehouse

    material = db.query(Material).filter(Material.code == code).first()
    if not material:
        return

    mat_id   = material.id
    mat_name = material.name

    # 1. Cancelar requerimientos activos que incluyen este material
    req_items = db.query(RequirementItem).filter(RequirementItem.material_id == mat_id).all()
    cancelled_ids = set()
    for item in req_items:
        req = item.requirement
        if req and req.status not in ("cancelled", "fulfilled") and req.id not in cancelled_ids:
            from services.requirement_service import cancel_requirement
            cancel_requirement(db, req.id, reason=f"Material eliminado: {mat_name}")
            cancelled_ids.add(req.id)

    # 2. Eliminar SOLO los registros de inventario PRINCIPAL del cliente actual,
    #    registrando un movimiento OUT por cada uno con stock > 0.
    #    El inventario en almacenes "obra" se conserva: el material ya llegó a la
    #    obra y debe quedar disponible aunque el material desaparezca del catálogo.
    inventories = db.query(Inventory).join(
        Warehouse, Inventory.warehouse_id == Warehouse.id
    ).filter(
        Inventory.material_id == mat_id,
        Warehouse.type == "principal",
    ).all()
    for inv in inventories:
        if inv.stock > 0:
            db.add(Movement(
                warehouse_id=inv.warehouse_id,
                material_id=mat_id,
                qty_change=-inv.stock,
                movement_type="OUT",
                reference_type="material_eliminado",
                reference_id=None,
                budget_id=inv.budget_id,
                user_id=user_id,
                timestamp=datetime.utcnow(),
            ))
        db.delete(inv)
    db.commit()

    # 3. El catálogo de Material solo se elimina si ya no queda ningún inventario
    #    (obra incluida) que lo referencie — preservar la FK obra→material.
    remaining = db.query(Inventory).filter(Inventory.material_id == mat_id).count()
    if remaining == 0:
        db.delete(material)
        db.commit()

# Actualizar
def update_material(db: Session, material_id, code, name, unit, description,
                    unit_price: float = None, unit_price_dolares: float = None):
    material = db.query(Material).filter(Material.id == material_id).first()

    if material:
        existing_code = db.query(Material).filter(
            Material.code == code,
            Material.id != material_id
        ).first()

        if existing_code:
            return False, 'code'

        existing_name = db.query(Material).filter(
            Material.name == name,
            Material.id != material_id
        ).first()

        if existing_name:
            return False, 'name'

        material.code = code
        material.name = name
        material.unit = unit
        material.description = description
        if unit_price is not None:
            material.unit_price = max(0.0, float(unit_price))
        if unit_price_dolares is not None:
            material.unit_price_dolares = max(0.0, float(unit_price_dolares))

        db.commit()
        return True, material
