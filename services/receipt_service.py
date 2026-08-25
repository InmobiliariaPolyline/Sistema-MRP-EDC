from sqlalchemy.orm import Session
from models.receipt import Receipt, ReceiptItem
from models.dispatch import Dispatch
from models.warehouse import Warehouse
from models.movement import Movement
from services.inventory_service import get_or_create_inventory
from datetime import datetime, timezone, timedelta

_LIMA = timezone(timedelta(hours=-5))  # Peru UTC-5, sin horario de verano

def _now_lima() -> datetime:
    return datetime.now(_LIMA).replace(tzinfo=None)


def create_receipt(db: Session, dispatch_id, user_id=1, owner_id=None):

    dispatch = db.query(Dispatch).filter(
        Dispatch.id == dispatch_id
    ).first()

    if not dispatch:
        return False, "Despacho no existe"
    if dispatch.status == "cancelled":
        return False, "No se puede recibir un despacho cancelado"

    # 🔒 evitar duplicados
    if dispatch.receipt:
        return False, "Este despacho ya fue recibido"

    requirement = dispatch.requirement
    if not requirement:
        return False, "El requerimiento del despacho no existe"
    warehouse = db.query(Warehouse).filter(Warehouse.id == requirement.warehouse_id_obra).first()
    if owner_id is not None and (not warehouse or warehouse.owner_id != owner_id):
        return False, "No tienes permiso para recibir este despacho"
    warehouse_obra = requirement.warehouse_id_obra
    req_budget_id   = getattr(requirement, "budget_id", None)
    req_budget_name = getattr(requirement, "budget_name", None)

    receipt = Receipt(
        dispatch_id=dispatch_id,
        receipt_date=_now_lima(),
        user_id=user_id
    )

    db.add(receipt)
    # La recepción y sus movimientos se guardan juntos al final.
    db.flush()

    for item in dispatch.items:
        material_id = item.material_id
        qty = item.dispatched_qty

        # 📦 INVENTARIO OBRA — separado por proyecto cuando el req. está vinculado
        inventory = get_or_create_inventory(
            db, warehouse_obra, material_id,
            budget_id=req_budget_id,
            budget_name=req_budget_name,
        )

        inventory.stock += qty

        # 📄 ITEM RECEIPT
        receipt_item = ReceiptItem(
            receipt_id=receipt.id,
            material_id=material_id,
            received_qty=qty,
            confirmed=True
        )
        db.add(receipt_item)

        # 🔁 MOVEMENT ENTRADA
        movement = Movement(
            warehouse_id=warehouse_obra,
            material_id=material_id,
            qty_change=qty,
            movement_type="IN",
            reference_type="receipt",
            reference_id=receipt.id,
            budget_id=req_budget_id,
            user_id=user_id
        )
        db.add(movement)

    db.commit()

    return True, "Recepción registrada correctamente"