from sqlalchemy.orm import Session
from sqlalchemy import func
from models.budget import Budget
from datetime import datetime
import json


def create_budget(db: Session, name: str, budget_soles: float, budget_dolares: float, notes: str = None) -> Budget:
    budget_soles   = max(0.0, float(budget_soles or 0))
    budget_dolares = max(0.0, float(budget_dolares or 0))
    b = Budget(
        name=name,
        budget_soles=budget_soles,
        budget_dolares=budget_dolares,
        notes=notes,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def get_budgets(db: Session):
    return db.query(Budget).order_by(Budget.created_at.desc()).all()


def count_budget_inventory(db: Session, budget_id: int) -> int:
    """Count active inventory records linked to this budget."""
    from models.inventory import Inventory
    return db.query(Inventory).filter(
        Inventory.budget_id == budget_id,
        Inventory.is_active == True,
    ).count()


def delete_budget(db: Session, budget_id: int):
    """Borra el presupuesto, congela su inventario y cancela todos los
    requerimientos en estado pending/partial.

    Returns (ok: bool, cancelled_count: int).
    """
    from models.inventory import Inventory
    from models.requirement import Requirement
    from services.requirement_service import cancel_requirement

    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False, 0

    # Cancelar SOLO los requerimientos pendientes/parciales vinculados a este proyecto
    pending_reqs = db.query(Requirement).filter(
        Requirement.status.in_(["pending", "partial"]),
        Requirement.budget_id == budget_id,
    ).all()
    cancelled = 0
    for req in pending_reqs:
        if cancel_requirement(db, req.id, reason=f"Proyecto «{b.name}» eliminado"):
            cancelled += 1

    # Freeze all inventory records linked to this project
    db.query(Inventory).filter(Inventory.budget_id == budget_id).update({"is_active": False})
    db.delete(b)
    db.commit()
    return True, cancelled


def update_budget(db: Session, budget_id: int, name: str = None,
                  budget_soles: float = None, budget_dolares: float = None,
                  notes: str = None, is_active: bool = None) -> bool:
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False
    was_active = bool(b.is_active)
    if name is not None:
        b.name = name
    if budget_soles is not None:
        b.budget_soles = max(0.0, float(budget_soles))
    if budget_dolares is not None:
        b.budget_dolares = max(0.0, float(budget_dolares))
    if notes is not None:
        b.notes = notes
    if is_active is not None:
        b.is_active = is_active
    db.commit()
    # If we just turned an inactive project active, lock any floating stock
    # at the current material prices.
    if is_active is True and not was_active:
        from services.inventory_service import lock_unlocked_inventory
        lock_unlocked_inventory(db, budget_id)
    return True


def finish_budget(db: Session, budget_id: int) -> bool:
    """Marca la obra como finalizada (is_finished=True, is_active=False)."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False
    b.is_finished = True
    b.is_active   = False
    b.finished_at = datetime.utcnow()
    db.commit()
    return True


def reactivate_budget(db: Session, budget_id: int) -> bool:
    """Reactiva una obra finalizada (is_finished=False, is_active=True)."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False
    was_active = bool(b.is_active)
    b.is_finished = False
    b.is_active   = True
    b.finished_at = None
    db.commit()
    if not was_active:
        from services.inventory_service import lock_unlocked_inventory
        lock_unlocked_inventory(db, budget_id)
    return True


def deactivate_budget_with_reason(db: Session, budget_id: int,
                                  reason: str, reactivation_date: datetime) -> bool:
    """Desactiva un proyecto registrando el motivo, la fecha de desactivación
    y la fecha programada de reactivación."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False
    b.is_active           = False
    b.deactivated_at      = datetime.utcnow()
    b.deactivation_reason = (reason or "").strip() or None
    b.reactivation_date   = reactivation_date
    db.commit()
    return True


def confirm_reactivation(db: Session, budget_id: int, note: str = None) -> bool:
    """Confirma la reactivación del proyecto. Si se entrega una nota, queda
    registrada en el historial como entrada de reactivación manual.
    Limpia los campos de desactivación pero conserva el historial completo.

    Al reactivar, todo el stock con costo flotante (`unlocked_qty > 0`) que
    pertenece al proyecto se bloquea al precio actual y se descuenta del
    presupuesto."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        return False
    was_active = bool(b.is_active)
    if note and note.strip():
        history = get_extension_history(b)
        history.append({
            "type":           "manual_reactivation",
            "previous_date":  b.reactivation_date.isoformat() if b.reactivation_date else None,
            "reason":         note.strip(),
            "reactivated_at": datetime.utcnow().isoformat(),
        })
        b.extension_history = json.dumps(history)
    b.is_active           = True
    b.deactivated_at      = None
    b.deactivation_reason = None
    b.reactivation_date   = None
    db.commit()
    if not was_active:
        from services.inventory_service import lock_unlocked_inventory
        lock_unlocked_inventory(db, budget_id)
    return True


def get_extension_history(b: Budget) -> list:
    """Devuelve la lista de extensiones registradas (puede estar vacía)."""
    raw = getattr(b, "extension_history", None)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except (ValueError, TypeError):
        pass
    return []


def extend_reactivation(db: Session, budget_id: int,
                        new_date: datetime, reason: str) -> bool:
    """Extiende la fecha de reactivación de un proyecto desactivado y
    registra el motivo en el historial de extensiones."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b or b.is_active:
        return False
    history = get_extension_history(b)
    history.append({
        "previous_date": b.reactivation_date.isoformat() if b.reactivation_date else None,
        "new_date":      new_date.isoformat(),
        "reason":        (reason or "").strip(),
        "extended_at":   datetime.utcnow().isoformat(),
    })
    b.reactivation_date  = new_date
    b.extension_history  = json.dumps(history)
    db.commit()
    return True


def deduct_budget(db: Session, budget_id: int, soles: float, dolares: float) -> bool:
    """OBSOLETO — el presupuesto es fijo y solo cambia por `update_budget`
    (botón Editar). Mantiene la firma como no-op para compatibilidad."""
    return False


def credit_budget(db: Session, budget_id: int, soles: float, dolares: float) -> bool:
    """OBSOLETO — el presupuesto es fijo y solo cambia por `update_budget`
    (botón Editar). Mantiene la firma como no-op para compatibilidad."""
    return False


def get_dispatch_costs(db: Session, since: datetime = None, until: datetime = None,
                       budget_id: int = None):
    """
    Returns (list_of_dicts, grand_total_soles, grand_total_dolares).
    Each dict: material name/code/unit, total_qty dispatched, unit_price (S/.), unit_price_dolares,
    total_cost (S/.), total_cost_dolares.
    Filtered by Dispatch.dispatch_date when since/until are provided.
    When `budget_id` is provided, only despachos cuyo `Requirement.budget_id` coincide se cuentan.
    """
    from models.dispatch import Dispatch, DispatchItem
    from models.material import Material
    from models.requirement import Requirement

    q = (
        db.query(
            DispatchItem.material_id,
            func.sum(DispatchItem.dispatched_qty).label("total_qty"),
        )
        .join(Dispatch, DispatchItem.dispatch_id == Dispatch.id)
    )
    if since:
        q = q.filter(Dispatch.dispatch_date >= since)
    if until:
        q = q.filter(Dispatch.dispatch_date <= until)
    if budget_id is not None:
        q = q.join(Requirement, Dispatch.requirement_id == Requirement.id).filter(
            Requirement.budget_id == budget_id
        )

    rows = q.group_by(DispatchItem.material_id).all()

    result = []
    grand_total          = 0.0
    grand_total_dolares  = 0.0
    for row in rows:
        mat = db.query(Material).filter(Material.id == row.material_id).first()
        if not mat:
            continue
        price         = mat.unit_price         or 0.0
        price_dolares = mat.unit_price_dolares or 0.0
        cost          = row.total_qty * price
        cost_dolares  = row.total_qty * price_dolares
        grand_total         += cost
        grand_total_dolares += cost_dolares
        result.append({
            "id":                 mat.id,
            "material":           mat.name,
            "code":               mat.code,
            "unit":               mat.unit or "—",
            "total_qty":          row.total_qty,
            "unit_price":         price,
            "unit_price_dolares": price_dolares,
            "total_cost":         cost,
            "total_cost_dolares": cost_dolares,
        })

    result.sort(key=lambda x: x["total_cost"], reverse=True)
    return result, grand_total, grand_total_dolares


def get_all_projects_cost_summary(db: Session) -> list:
    """Return a list of dicts with cost vs budget for every project."""
    budgets = get_budgets(db)
    result = []
    for b in budgets:
        costs, total_soles, total_dol = get_dispatch_costs(db, since=b.created_at)
        result.append({
            "id":              b.id,
            "name":            b.name,
            "budget_soles":    b.budget_soles,
            "budget_dolares":  b.budget_dolares,
            "is_active":       b.is_active,
            "is_finished":     getattr(b, "is_finished", False),
            "finished_at":     getattr(b, "finished_at", None),
            "cost_soles":      total_soles,
            "cost_dolares":    total_dol,
            "n_materials":     len(costs),
            "created_at":      b.created_at,
        })
    return result


def get_movement_summary(db: Session, since: datetime = None, until: datetime = None,
                         budget_id: int = None) -> dict:
    """Total units IN vs OUT in the movement log for the given period.

    Cuando se pasa `budget_id`, las KPIs se acotan a movimientos vinculados
    explícitamente a ese proyecto (`Movement.budget_id`).
    """
    from models.movement import Movement

    def _sum_abs(mtype: str) -> int:
        q = db.query(func.sum(func.abs(Movement.qty_change))).filter(
            Movement.movement_type == mtype
        )
        if since:
            q = q.filter(Movement.timestamp >= since)
        if until:
            q = q.filter(Movement.timestamp <= until)
        if budget_id is not None:
            q = q.filter(Movement.budget_id == budget_id)
        return q.scalar() or 0

    return {
        "total_in":  _sum_abs("IN"),
        "total_out": _sum_abs("OUT"),
    }
