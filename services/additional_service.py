import json
import os
from sqlalchemy.orm import Session
from models.budget_additional import BudgetAdditional
from datetime import datetime


def create_additional(db: Session, budget_id: int, request_date: datetime,
                      concept: str, notes: str = None) -> BudgetAdditional:
    a = BudgetAdditional(
        budget_id    = budget_id,
        request_date = request_date,
        concept      = (concept or "").strip(),
        notes        = (notes or "").strip() or None,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def get_additionals(db: Session, budget_id: int = None,
                    only_pending: bool = False,
                    only_confirmed: bool = False):
    q = db.query(BudgetAdditional)
    if budget_id is not None:
        q = q.filter(BudgetAdditional.budget_id == budget_id)
    if only_pending:
        q = q.filter((BudgetAdditional.confirmed == False) | (BudgetAdditional.confirmed.is_(None)))
    if only_confirmed:
        q = q.filter(BudgetAdditional.confirmed == True)
    return q.order_by(BudgetAdditional.request_date.desc(), BudgetAdditional.id.desc()).all()


def update_additional(db: Session, additional_id: int,
                      request_date: datetime = None,
                      concept: str = None,
                      notes: str = None) -> bool:
    a = db.query(BudgetAdditional).filter(BudgetAdditional.id == additional_id).first()
    if not a:
        return False
    if request_date is not None:
        a.request_date = request_date
    if concept is not None:
        a.concept = (concept or "").strip()
    if notes is not None:
        a.notes = (notes or "").strip() or None
    db.commit()
    return True


def delete_additional(db: Session, additional_id: int) -> bool:
    a = db.query(BudgetAdditional).filter(BudgetAdditional.id == additional_id).first()
    if not a:
        return False
    db.delete(a)
    db.commit()
    return True


# ── Confirmación ─────────────────────────────────────────────────────────────

ADDITIONAL_STORAGE_DIR = os.path.join("storage", "additionals")


def _save_uploaded_file(additional_id: int, uploaded_file) -> dict:
    """Guarda un archivo subido en disco y devuelve un dict {name, path}."""
    folder = os.path.join(ADDITIONAL_STORAGE_DIR, str(additional_id))
    os.makedirs(folder, exist_ok=True)
    safe_name = uploaded_file.name.replace("\\", "_").replace("/", "_")
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    path = os.path.join(folder, f"{ts}_{safe_name}")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return {"name": uploaded_file.name, "path": path}


def confirm_additional(db: Session, additional_id: int,
                       uploaded_files: list = None,
                       links: list = None) -> tuple[bool, str]:
    """Confirma la autorización del adicional.

    Requiere AL MENOS un documento (archivo subido) o un enlace.
    Genera un código único `AD-YYYYMMDD-{id:05d}` y guarda los documentos
    como JSON en la columna `documents`.

    Devuelve (ok, mensaje_o_codigo).
    """
    a = db.query(BudgetAdditional).filter(BudgetAdditional.id == additional_id).first()
    if not a:
        return False, "Adicional no encontrado."
    if a.confirmed:
        return False, "Este adicional ya está confirmado."

    uploaded_files = uploaded_files or []
    links = [l.strip() for l in (links or []) if l and l.strip()]

    if not uploaded_files and not links:
        return False, "Debes adjuntar al menos un documento o enlace."

    saved_files = []
    for uf in uploaded_files:
        try:
            saved_files.append(_save_uploaded_file(additional_id, uf))
        except Exception as e:
            return False, f"Error guardando archivo «{getattr(uf, 'name', '?')}»: {e}"

    payload = {
        "files": saved_files,
        "links": [{"url": l} for l in links],
    }

    now  = datetime.now()
    code = f"AD-{now.strftime('%Y%m%d')}-{a.id:05d}"

    a.confirmed         = True
    a.confirmation_code = code
    a.confirmed_at      = now
    a.documents         = json.dumps(payload, ensure_ascii=False)

    db.commit()
    return True, code


def update_confirmed_additional(db: Session, additional_id: int,
                                concept: str = None,
                                notes: str = None,
                                request_date: datetime = None,
                                new_files: list = None,
                                links: list = None,
                                remove_file_paths: list = None) -> tuple[bool, str]:
    """Edita un adicional ya confirmado.

    - Mantiene `confirmation_code` y `confirmed_at` originales.
    - Permite quitar archivos previos (por su `path`) y/o agregar nuevos.
    - Reemplaza la lista de enlaces.
    - Debe quedar AL MENOS un documento o enlace tras la edición.
    """
    a = db.query(BudgetAdditional).filter(BudgetAdditional.id == additional_id).first()
    if not a:
        return False, "Adicional no encontrado."
    if not a.confirmed:
        return False, "Este adicional aún no está confirmado."

    current = get_documents(a)
    remove_set = set(remove_file_paths or [])

    kept_files = [f for f in current["files"] if f.get("path") not in remove_set]

    new_files = new_files or []
    for uf in new_files:
        try:
            kept_files.append(_save_uploaded_file(additional_id, uf))
        except Exception as e:
            return False, f"Error guardando archivo «{getattr(uf, 'name', '?')}»: {e}"

    cleaned_links = [l.strip() for l in (links or []) if l and l.strip()]

    if not kept_files and not cleaned_links:
        return False, "Debe quedar al menos un documento o enlace."

    # Borrar físicamente los archivos eliminados
    for f in current["files"]:
        if f.get("path") in remove_set:
            try:
                if os.path.isfile(f["path"]):
                    os.remove(f["path"])
            except OSError:
                pass

    payload = {
        "files": kept_files,
        "links": [{"url": l} for l in cleaned_links],
    }
    a.documents = json.dumps(payload, ensure_ascii=False)

    if concept is not None and concept.strip():
        a.concept = concept.strip()
    if notes is not None:
        a.notes = notes.strip() or None
    if request_date is not None:
        a.request_date = request_date

    db.commit()
    return True, "ok"


def get_documents(additional: BudgetAdditional) -> dict:
    """Devuelve los documentos asociados (parseo seguro del JSON)."""
    if not additional.documents:
        return {"files": [], "links": []}
    try:
        data = json.loads(additional.documents)
        return {
            "files": data.get("files", []) or [],
            "links": data.get("links", []) or [],
        }
    except (ValueError, TypeError):
        return {"files": [], "links": []}
