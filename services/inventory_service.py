from sqlalchemy.orm import Session
from models.inventory import Inventory
from models.material import Material
from models.movement import Movement

from models.warehouse import Warehouse
from datetime import datetime

def get_or_create_inventory(db: Session, warehouse_id, material_id,
                            budget_id=None, budget_name=None):
    """Returns the inventory record matching (warehouse, material, budget).
    When budget_id is provided, separate records are kept per project so each
    one appears as its own card. When budget_id is None, falls back to the
    record without a project."""
    q = db.query(Inventory).filter(
        Inventory.warehouse_id == warehouse_id,
        Inventory.material_id == material_id,
    )
    if budget_id is not None:
        q = q.filter(Inventory.budget_id == budget_id)
    else:
        q = q.filter(Inventory.budget_id == None)
    inventory = q.first()

    if not inventory:
        inventory = Inventory(
            warehouse_id=warehouse_id,
            material_id=material_id,
            stock=0,
            reserved=0,
            budget_id=budget_id,
            budget_name=budget_name,
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

    return inventory

def add_stock(db: Session, warehouse_id, material_id, qty, user_id,
              budget_id=None, budget_name=None):
    """Add stock to the appropriate inventory record.
    Creates separate records per budget_id so they appear as distinct cards.

    Budget cost handling:
    - If budget is provided and ACTIVE: deducts (qty × current_price) from the
      budget and adds the same amount to the inventory's locked_cost. This is
      a "fixed" expense that won't change if material prices fluctuate later.
    - If budget is provided and INACTIVE: does not touch the budget; instead
      increments unlocked_qty. The cost stays "floating" (qty × current_price
      at view time) until the project is reactivated, which locks it in.

    Returns a tuple (newly_fulfilled, applied_cost_soles, applied_cost_dolares).
    applied_cost_* is only > 0 when a real deduction took place (active project).
    """
    if budget_id is not None:
        inventory = db.query(Inventory).filter(
            Inventory.warehouse_id == warehouse_id,
            Inventory.material_id == material_id,
            Inventory.budget_id == budget_id,
        ).first()
        if not inventory:
            inventory = Inventory(
                warehouse_id=warehouse_id,
                material_id=material_id,
                stock=0,
                reserved=0,
                budget_id=budget_id,
                budget_name=budget_name,
            )
            db.add(inventory)
            db.commit()
            db.refresh(inventory)
    else:
        inventory = db.query(Inventory).filter(
            Inventory.warehouse_id == warehouse_id,
            Inventory.material_id == material_id,
            Inventory.budget_id == None,
        ).first()
        if not inventory:
            inventory = Inventory(
                warehouse_id=warehouse_id,
                material_id=material_id,
                stock=0,
                reserved=0,
            )
            db.add(inventory)
            db.commit()
            db.refresh(inventory)

    from services.requirement_service import reprocess_requirements

    inventory.stock += qty
    inventory.last_updated = datetime.utcnow()

    # El monto del presupuesto (Budget.budget_soles / .budget_dolares) es FIJO
    # y solo cambia con el botón "Editar". Las operaciones de stock únicamente
    # actualizan la línea de inventario (locked_cost_* / unlocked_qty). El
    # "disponible" se calcula dinámicamente como
    #     budget_soles - locked_consumed - floating_consumed.
    applied_cost_s = 0.0
    applied_cost_d = 0.0
    if budget_id is not None:
        from models.budget import Budget
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        material = db.query(Material).filter(Material.id == material_id).first()
        if budget and material:
            unit_s = float(material.unit_price or 0.0)
            unit_d = float(material.unit_price_dolares or 0.0)
            if budget.is_active:
                applied_cost_s = qty * unit_s
                applied_cost_d = qty * unit_d
                inventory.locked_cost_soles   = float(inventory.locked_cost_soles   or 0.0) + applied_cost_s
                inventory.locked_cost_dolares = float(inventory.locked_cost_dolares or 0.0) + applied_cost_d
            else:
                inventory.unlocked_qty = int(inventory.unlocked_qty or 0) + qty

    movement = Movement(
        warehouse_id=warehouse_id,
        material_id=material_id,
        qty_change=qty,
        movement_type="IN",
        reference_type="manual",
        reference_id=None,
        budget_id=budget_id,
        user_id=user_id
    )

    db.add(movement)
    db.commit()
    newly_fulfilled = reprocess_requirements(db)
    return newly_fulfilled, applied_cost_s, applied_cost_d


def update_inventory_note(db: Session, inventory_id: int, note: str, owner_id: int = None) -> bool:
    """Save the free-form note attached to an inventory record."""
    inv = db.query(Inventory).join(Warehouse).filter(Inventory.id == inventory_id).first()
    if not inv:
        return False
    if owner_id is not None and inv.warehouse.owner_id != owner_id:
        return False
    inv.note = (note or "").strip() or None
    inv.last_updated = datetime.utcnow()
    db.commit()
    return True


def get_budget_available(db: Session, budget_id: int) -> tuple:
    """Devuelve (disponible_S/, disponible_$).
    Consumo total = bloqueado (activo) + pendiente de resolución + perdido + flotante."""
    from models.budget import Budget
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return 0.0, 0.0
    locked_s, locked_d   = get_locked_consumed(db, budget_id)
    pend_s,   pend_d     = get_pending_deleted_consumed(db, budget_id)
    lost_s,   lost_d     = get_lost_consumed(db, budget_id)
    float_s,  float_d    = get_floating_consumed(db, budget_id)
    avail_s = max(0.0, float(b.budget_soles)   - locked_s - pend_s - lost_s - float_s)
    avail_d = max(0.0, float(b.budget_dolares) - locked_d - pend_d - lost_d - float_d)
    return avail_s, avail_d


def get_locked_consumed(db: Session, budget_id: int) -> tuple:
    """Suma del costo bloqueado (S/, $) para todas las líneas de inventario
    activas del proyecto. Representa el gasto fijo ya descontado del
    presupuesto al precio del momento de cada ingreso."""
    inv_records = db.query(Inventory).filter(
        Inventory.budget_id == budget_id,
        Inventory.is_active == True,
    ).all()
    total_s = sum(float(inv.locked_cost_soles   or 0.0) for inv in inv_records)
    total_d = sum(float(inv.locked_cost_dolares or 0.0) for inv in inv_records)
    return total_s, total_d


def get_floating_consumed(db: Session, budget_id: int) -> tuple:
    """Compute the floating cost (S/, $) for a (typically deactivated) project,
    based on `unlocked_qty × current_price` across its inventory records."""
    inv_records = db.query(Inventory).filter(
        Inventory.budget_id == budget_id,
        Inventory.is_active == True,
        Inventory.unlocked_qty > 0,
    ).all()
    total_s = 0.0
    total_d = 0.0
    for inv in inv_records:
        if not inv.material:
            continue
        u = int(inv.unlocked_qty or 0)
        total_s += u * float(inv.material.unit_price         or 0.0)
        total_d += u * float(inv.material.unit_price_dolares or 0.0)
    return total_s, total_d


def lock_unlocked_inventory(db: Session, budget_id: int) -> tuple:
    """Bloquea el stock flotante de un proyecto al precio actual del material:
    pasa cada `unlocked_qty` a `locked_cost_*`. El monto del presupuesto se
    mantiene fijo — el "disponible" se calcula dinámicamente desde los
    `locked_cost_*` acumulados. Retorna (total_s, total_d) bloqueado."""
    from models.budget import Budget
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        return 0.0, 0.0
    inv_records = db.query(Inventory).filter(
        Inventory.budget_id == budget_id,
        Inventory.is_active == True,
        Inventory.unlocked_qty > 0,
    ).all()
    total_s = 0.0
    total_d = 0.0
    for inv in inv_records:
        if not inv.material:
            inv.unlocked_qty = 0
            continue
        u = int(inv.unlocked_qty or 0)
        cost_s = u * float(inv.material.unit_price         or 0.0)
        cost_d = u * float(inv.material.unit_price_dolares or 0.0)
        inv.locked_cost_soles   = float(inv.locked_cost_soles   or 0.0) + cost_s
        inv.locked_cost_dolares = float(inv.locked_cost_dolares or 0.0) + cost_d
        inv.unlocked_qty = 0
        total_s += cost_s
        total_d += cost_d
    db.commit()
    return total_s, total_d

def remove_stock(db: Session, warehouse_id, material_id, qty, user_id,
                 budget_id="__any__"):
    """Remove stock from inventory records.

    `budget_id`:
      - "__any__" (default, backwards compatible): retira distribuyendo entre
        todos los registros activos del par almacén/material (FIFO por id).
      - None: retira solo de la línea sin proyecto asignado.
      - int: retira solo de la línea vinculada a ese proyecto.
    """
    q = db.query(Inventory).filter(
        Inventory.warehouse_id == warehouse_id,
        Inventory.material_id == material_id,
        Inventory.is_active == True,
    )
    if budget_id == "__any__":
        pass
    elif budget_id is None:
        q = q.filter(Inventory.budget_id == None)
    else:
        q = q.filter(Inventory.budget_id == budget_id)
    records = q.order_by(Inventory.id).all()

    total_stock = sum(inv.stock for inv in records)
    if total_stock < qty:
        return False

    remaining = qty
    touched   = []
    for inv in records:
        if remaining <= 0:
            break
        reduce = min(inv.stock, remaining)
        inv.stock -= reduce
        # Consume unlocked units first (they were never charged to the budget).
        if (inv.unlocked_qty or 0) > 0:
            unl_drop = min(int(inv.unlocked_qty), reduce)
            inv.unlocked_qty = int(inv.unlocked_qty) - unl_drop
        inv.last_updated = datetime.utcnow()
        touched.append(inv)
        remaining -= reduce

    # Vincular el movimiento al proyecto cuando hay un único contexto claro:
    # - budget_id explícito (no "__any__") → ese proyecto.
    # - "__any__" con un solo registro tocado y con budget_id → ese proyecto.
    _mov_budget_id = None
    if budget_id not in ("__any__", None):
        _mov_budget_id = budget_id
    elif budget_id == "__any__":
        _touched_buds = {inv.budget_id for inv in touched if inv.budget_id is not None}
        if len(_touched_buds) == 1:
            _mov_budget_id = next(iter(_touched_buds))

    movement = Movement(
        warehouse_id=warehouse_id,
        material_id=material_id,
        qty_change=-qty,
        movement_type="OUT",
        reference_type="manual",
        reference_id=None,
        budget_id=_mov_budget_id,
        user_id=user_id
    )

    db.add(movement)

    # Eliminar registros que quedaron vacíos (sin stock ni reservas).
    for inv in touched:
        if int(inv.stock or 0) == 0 and int(inv.reserved or 0) == 0:
            db.delete(inv)

    db.commit()
    return True

def reserve_stock(db: Session, warehouse_id, material_id, qty):
    """
    Reserva stock para un requerimiento.
    Agrega reservas distribuidas entre todos los registros activos del material (FIFO).
    No hace commit — el llamador debe hacer commit después de todos los cambios.
    """
    records = db.query(Inventory).filter(
        Inventory.warehouse_id == warehouse_id,
        Inventory.material_id == material_id,
        Inventory.is_active == True,
    ).order_by(Inventory.id).all()

    total_available = sum(max(0, inv.stock - inv.reserved) for inv in records)
    if not records or total_available < qty:
        return False

    remaining = qty
    for inv in records:
        available = max(0, inv.stock - inv.reserved)
        if available <= 0:
            continue
        to_reserve = min(available, remaining)
        inv.reserved += to_reserve
        inv.last_updated = datetime.utcnow()
        db.add(inv)
        remaining -= to_reserve
        if remaining <= 0:
            break
    return True

def release_reservation(db: Session, warehouse_id, material_id, qty):
    """Libera reservas distribuidas entre registros activos del material (FIFO)."""
    records = db.query(Inventory).filter(
        Inventory.warehouse_id == warehouse_id,
        Inventory.material_id == material_id,
        Inventory.is_active == True,
    ).order_by(Inventory.id).all()

    remaining = qty
    for inv in records:
        if remaining <= 0:
            break
        release = min(inv.reserved, remaining)
        inv.reserved -= release
        remaining -= release

    db.commit()

def get_inventory(db: Session):
    return db.query(Inventory).all()


def get_inventory_filtered(db: Session, skip: int = 0, limit: int = 10,
                           warehouse_name: str = None, material_name: str = None, stock: int = None):
    query = db.query(Inventory)

    if warehouse_name:
        query = query.join(Warehouse).filter(Warehouse.name.ilike(f"%{warehouse_name}%"))
    if material_name:
        query = query.join(Material).filter(Material.name.ilike(f"%{material_name}%"))
    if stock is not None:
        query = query.filter(Inventory.stock == stock)

    query = query.order_by(Inventory.last_updated.desc())

    total_count = query.count()

    # Aplicar paginación
    inventory = query.offset(skip).limit(limit).all()

    return inventory, total_count

def delete_inventory_record(db: Session, inventory_id: int, owner_id: int = None) -> bool:
    from models.deleted_inventory import DeletedInventory
    from datetime import datetime as _dt
    inv = db.query(Inventory).join(Warehouse).filter(Inventory.id == inventory_id).first()
    if inv:
        if owner_id is not None and inv.warehouse.owner_id != owner_id:
            return False
        mat = inv.material
        wh  = inv.warehouse
        unit_price     = float(mat.unit_price     or 0.0) if mat else 0.0
        unit_price_dol = float(mat.unit_price_dolares or 0.0) if mat else 0.0
        db.add(DeletedInventory(
            original_id    = inv.id,
            warehouse_id   = inv.warehouse_id,
            material_id    = inv.material_id,
            warehouse_name = wh.name  if wh  else f"Almacén {inv.warehouse_id}",
            material_name  = mat.name if mat else f"Material {inv.material_id}",
            material_unit  = (mat.unit or "uds") if mat else "uds",
            unit_price     = unit_price,
            unit_price_dol = unit_price_dol,
            stock          = inv.stock,
            total_value    = inv.stock * unit_price,
            deleted_at     = _dt.utcnow(),
            status         = "pending",
            owner_id       = owner_id,
            budget_id           = inv.budget_id,
            budget_name         = inv.budget_name,
            locked_cost_soles   = float(inv.locked_cost_soles   or 0.0),
            locked_cost_dolares = float(inv.locked_cost_dolares or 0.0),
            unlocked_qty        = int(inv.unlocked_qty or 0),
        ))
        db.delete(inv)
        db.commit()
        return True
    return False


def get_deleted_inventory(db: Session, owner_id: int = None):
    from models.deleted_inventory import DeletedInventory
    q = db.query(DeletedInventory).filter(DeletedInventory.status == "pending")
    if owner_id is not None:
        q = q.filter(DeletedInventory.owner_id == owner_id)
    return q.order_by(DeletedInventory.deleted_at.desc()).all()


def resolve_deleted_inventory(db: Session, deleted_id: int, resolution: str, owner_id: int = None) -> bool:
    from models.deleted_inventory import DeletedInventory
    rec = db.query(DeletedInventory).filter(DeletedInventory.id == deleted_id).first()
    if not rec:
        return False
    if owner_id is not None and rec.owner_id != owner_id:
        return False
    rec.status = resolution
    db.commit()
    return True


def restore_deleted_inventory(db: Session, deleted_id: int) -> bool:
    """Restablece un registro previamente eliminado: devuelve el stock al
    inventario preservando el vínculo al proyecto y el costo bloqueado, de
    modo que la utilización del presupuesto vuelve al estado previo."""
    from models.deleted_inventory import DeletedInventory
    rec = db.query(DeletedInventory).filter(
        DeletedInventory.id == deleted_id,
        DeletedInventory.status == "pending",
    ).first()
    if not rec:
        return False

    # Si todavía existe el registro original, sumamos stock y costo bloqueado.
    inv = db.query(Inventory).filter(Inventory.id == rec.original_id).first()
    if inv:
        inv.stock              = int(inv.stock or 0) + int(rec.stock or 0)
        inv.locked_cost_soles  = float(inv.locked_cost_soles   or 0.0) + float(rec.locked_cost_soles   or 0.0)
        inv.locked_cost_dolares= float(inv.locked_cost_dolares or 0.0) + float(rec.locked_cost_dolares or 0.0)
        inv.unlocked_qty       = int(inv.unlocked_qty or 0) + int(rec.unlocked_qty or 0)
        inv.last_updated       = datetime.utcnow()
    else:
        # Recreamos el registro preservando el proyecto y el costo bloqueado
        # para que la barra de utilización se restablezca.
        inv = Inventory(
            warehouse_id        = rec.warehouse_id,
            material_id         = rec.material_id,
            stock               = int(rec.stock or 0),
            reserved            = 0,
            budget_id           = rec.budget_id,
            budget_name         = rec.budget_name,
            is_active           = True,
            locked_cost_soles   = float(rec.locked_cost_soles   or 0.0),
            locked_cost_dolares = float(rec.locked_cost_dolares or 0.0),
            unlocked_qty        = int(rec.unlocked_qty or 0),
        )
        db.add(inv)

    rec.status = "restored"
    db.commit()
    return True


def get_pending_deleted_consumed(db: Session, budget_id: int) -> tuple:
    """Suma del costo bloqueado de eliminaciones aún sin resolver (status
    'pending'). Estas líneas siguen contando como consumo hasta que el usuario
    las marque como devueltas o perdidas."""
    from models.deleted_inventory import DeletedInventory
    rows = db.query(DeletedInventory).filter(
        DeletedInventory.budget_id == budget_id,
        DeletedInventory.status == "pending",
    ).all()
    total_s = sum(float(r.locked_cost_soles   or 0.0) for r in rows)
    total_d = sum(float(r.locked_cost_dolares or 0.0) for r in rows)
    return total_s, total_d


def get_lost_consumed(db: Session, budget_id: int) -> tuple:
    """Suma del costo bloqueado de material marcado como perdido. Estos
    quedan permanentemente consumidos (el dinero se gastó y el material no
    vuelve)."""
    from models.deleted_inventory import DeletedInventory
    rows = db.query(DeletedInventory).filter(
        DeletedInventory.budget_id == budget_id,
        DeletedInventory.status == "lost",
    ).all()
    total_s = sum(float(r.locked_cost_soles   or 0.0) for r in rows)
    total_d = sum(float(r.locked_cost_dolares or 0.0) for r in rows)
    return total_s, total_d


def get_frozen_inventory_for_owner(db: Session, owner_id: int):
    """Return inventory records that are frozen (project deleted) for a given client."""
    from models.warehouse import Warehouse
    return (
        db.query(Inventory)
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .filter(
            Inventory.is_active == False,
            Warehouse.owner_id == owner_id,
            Warehouse.type == "principal",
        )
        .order_by(Inventory.id)
        .all()
    )


def redirect_frozen_inventory(db: Session, inventory_id: int, new_budget_id: int, owner_id: int = None) -> bool:
    """Reassign a frozen inventory record to a new project and reactivate it."""
    from models.budget import Budget
    inv = db.query(Inventory).filter(
        Inventory.id == inventory_id,
        Inventory.is_active == False,
    ).first()
    if not inv:
        return False
    if owner_id is not None and inv.warehouse.owner_id != owner_id:
        return False
    budget = db.query(Budget).filter(Budget.id == new_budget_id).first()
    if not budget:
        return False
    inv.budget_id   = new_budget_id
    inv.budget_name = budget.name
    inv.is_active   = True
    db.commit()
    return True


def assign_project_to_inventory(db: Session, inventory_id: int, budget_id, owner_id: int = None) -> bool:
    """Asigna o reasigna el proyecto de un registro de inventario.
    - budget_id puede ser un int (proyecto destino) o None (quitar proyecto).
    - Si ya existe otro registro con la misma combinación (almacén/material/proyecto),
      fusiona stock y reservas en él y elimina el actual.
    """
    from models.budget import Budget
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        return False
    if owner_id is not None and inv.warehouse.owner_id != owner_id:
        return False

    bud_name = None
    if budget_id is not None:
        bud = db.query(Budget).filter(Budget.id == budget_id).first()
        if not bud:
            return False
        bud_name = bud.name

    # Buscar si ya existe un registro destino al que fusionar
    target_q = db.query(Inventory).filter(
        Inventory.warehouse_id == inv.warehouse_id,
        Inventory.material_id  == inv.material_id,
        Inventory.id           != inv.id,
    )
    if budget_id is None:
        target_q = target_q.filter(Inventory.budget_id == None)
    else:
        target_q = target_q.filter(Inventory.budget_id == budget_id)
    target = target_q.first()

    if target:
        target.stock    += inv.stock
        target.reserved += inv.reserved
        target.last_updated = datetime.utcnow()
        db.delete(inv)
    else:
        inv.budget_id    = budget_id
        inv.budget_name  = bud_name
        inv.last_updated = datetime.utcnow()

    db.commit()
    return True


def unfreeze_inventory(db: Session, inventory_id: int) -> bool:
    """Reactivate a frozen inventory record without assigning a project (budget_id=None)."""
    inv = db.query(Inventory).filter(
        Inventory.id == inventory_id,
        Inventory.is_active == False,
    ).first()
    if not inv:
        return False
    inv.budget_id   = None
    inv.budget_name = None
    inv.is_active   = True
    db.commit()
    return True
