# init_db.py
from database import Base, engine, SessionLocal

# Importar todos tus modelos
from models import (

    warehouse, material, inventory, requirement,
    dispatch, receipt, movement, user,
    login_log, failed_login, session, budget, deleted_inventory,
    budget_additional,
)


def run_migrations():
    """Migraciones manuales para agregar columnas"""
    from sqlalchemy import text, inspect
    from database import DATABASE_URL

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    is_sqlite = DATABASE_URL.startswith("sqlite")

    print("Ejecutando migraciones manuales...")

    def add_col(conn, table, col, col_def):
        # SQLite does not support IF NOT EXISTS in ALTER TABLE ADD COLUMN
        if is_sqlite:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))
        else:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_def}"))
        print(f"  [OK] Columna {col} añadida en {table}")

    print("🔧 Ejecutando migraciones manuales...")

    with engine.connect() as conn:
        # users table
        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "role" not in cols:
                add_col(conn, "users", "role", "VARCHAR NOT NULL DEFAULT 'cliente'")
            if "is_active" not in cols:
                add_col(conn, "users", "is_active", "BOOLEAN NOT NULL DEFAULT true")

        # user_sessions table
        if "user_sessions" in tables:
            cols = {c["name"] for c in inspector.get_columns("user_sessions")}
            if "role" not in cols:
                add_col(conn, "user_sessions", "role", "VARCHAR NOT NULL DEFAULT 'cliente'")

        # warehouses table
        if "warehouses" in tables:
            cols = {c["name"] for c in inspector.get_columns("warehouses")}
            if "owner_id" not in cols:
                add_col(conn, "warehouses", "owner_id", "INTEGER")
            if "address" not in cols:
                add_col(conn, "warehouses", "address", "VARCHAR")

        # materials table — precio unitario para cálculo de costos
        if "materials" in tables:
            cols = {c["name"] for c in inspector.get_columns("materials")}
            if "unit_price" not in cols:
                add_col(conn, "materials", "unit_price", "FLOAT DEFAULT 0.0")
            if "unit_price_dolares" not in cols:
                add_col(conn, "materials", "unit_price_dolares", "FLOAT DEFAULT 0.0")

        # budgets table — estado activo/inactivo y finalización de obra
        if "budgets" in tables:
            cols = {c["name"] for c in inspector.get_columns("budgets")}
            if "is_active" not in cols:
                default_val = "1" if is_sqlite else "true"
                add_col(conn, "budgets", "is_active", f"BOOLEAN NOT NULL DEFAULT {default_val}")
            if "is_finished" not in cols:
                default_val = "0" if is_sqlite else "false"
                add_col(conn, "budgets", "is_finished", f"BOOLEAN NOT NULL DEFAULT {default_val}")
            if "finished_at" not in cols:
                dt_type = "DATETIME" if is_sqlite else "TIMESTAMP"
                add_col(conn, "budgets", "finished_at", dt_type)
            if "deactivated_at" not in cols:
                dt_type = "DATETIME" if is_sqlite else "TIMESTAMP"
                add_col(conn, "budgets", "deactivated_at", dt_type)
            if "deactivation_reason" not in cols:
                add_col(conn, "budgets", "deactivation_reason", "VARCHAR")
            if "reactivation_date" not in cols:
                dt_type = "DATETIME" if is_sqlite else "TIMESTAMP"
                add_col(conn, "budgets", "reactivation_date", dt_type)
            if "extension_history" not in cols:
                add_col(conn, "budgets", "extension_history", "TEXT")

        # inventory table — per-budget tracking and freeze flag
        if "inventory" in tables:
            cols = {c["name"] for c in inspector.get_columns("inventory")}
            if "budget_id" not in cols:
                add_col(conn, "inventory", "budget_id", "INTEGER")
            if "budget_name" not in cols:
                add_col(conn, "inventory", "budget_name", "VARCHAR")
            if "is_active" not in cols:
                default_val = "1" if is_sqlite else "true"
                add_col(conn, "inventory", "is_active", f"BOOLEAN NOT NULL DEFAULT {default_val}")
            if "unlocked_qty" not in cols:
                add_col(conn, "inventory", "unlocked_qty", "INTEGER NOT NULL DEFAULT 0")
            if "locked_cost_soles" not in cols:
                add_col(conn, "inventory", "locked_cost_soles", "FLOAT NOT NULL DEFAULT 0.0")
            if "locked_cost_dolares" not in cols:
                add_col(conn, "inventory", "locked_cost_dolares", "FLOAT NOT NULL DEFAULT 0.0")
            if "note" not in cols:
                add_col(conn, "inventory", "note", "TEXT")

        # requirements table — vínculo opcional a un proyecto/budget
        if "requirements" in tables:
            cols = {c["name"] for c in inspector.get_columns("requirements")}
            if "budget_id" not in cols:
                add_col(conn, "requirements", "budget_id", "INTEGER")
            if "budget_name" not in cols:
                add_col(conn, "requirements", "budget_name", "VARCHAR")

        # dispatches — estado persistente de cancelación
        if "dispatches" in tables:
            cols = {c["name"] for c in inspector.get_columns("dispatches")}
            if "status" not in cols:
                add_col(conn, "dispatches", "status", "VARCHAR NOT NULL DEFAULT 'active'")

        # movements — vínculo a proyecto/budget para KPIs por ámbito
        if "movements" in tables:
            cols = {c["name"] for c in inspector.get_columns("movements")}
            if "budget_id" not in cols:
                add_col(conn, "movements", "budget_id", "INTEGER")
                print("  [INFO] Retropoblando movements.budget_id...")
                # Dispatch movements → requirement.budget_id
                conn.execute(text("""
                    UPDATE movements
                    SET budget_id = (
                        SELECT r.budget_id FROM dispatches d
                        JOIN requirements r ON r.id = d.requirement_id
                        WHERE d.id = movements.reference_id
                    )
                    WHERE reference_type = 'dispatch' AND budget_id IS NULL
                """))
                # Receipt movements → receipt.dispatch_id → requirement.budget_id
                conn.execute(text("""
                    UPDATE movements
                    SET budget_id = (
                        SELECT r.budget_id FROM receipts rc
                        JOIN dispatches d ON d.id = rc.dispatch_id
                        JOIN requirements r ON r.id = d.requirement_id
                        WHERE rc.id = movements.reference_id
                    )
                    WHERE reference_type = 'receipt' AND budget_id IS NULL
                """))
                # Manual/eliminado → si existe UNA sola inventory line para (wh, mat) con budget, úsala
                conn.execute(text("""
                    UPDATE movements
                    SET budget_id = (
                        SELECT i.budget_id FROM inventory i
                        WHERE i.warehouse_id = movements.warehouse_id
                          AND i.material_id  = movements.material_id
                          AND i.budget_id IS NOT NULL
                        LIMIT 1
                    )
                    WHERE reference_type IN ('manual','material_eliminado')
                      AND budget_id IS NULL
                      AND (
                        SELECT COUNT(DISTINCT i2.budget_id) FROM inventory i2
                        WHERE i2.warehouse_id = movements.warehouse_id
                          AND i2.material_id  = movements.material_id
                          AND i2.budget_id IS NOT NULL
                      ) = 1
                """))
                print("  [OK] Retropoblado completado.")

        # budget_additionals — confirmación de autorización + documentos
        if "budget_additionals" in tables:
            cols = {c["name"] for c in inspector.get_columns("budget_additionals")}
            if "confirmed" not in cols:
                default_val = "0" if is_sqlite else "false"
                add_col(conn, "budget_additionals", "confirmed", f"BOOLEAN NOT NULL DEFAULT {default_val}")
            if "confirmation_code" not in cols:
                add_col(conn, "budget_additionals", "confirmation_code", "VARCHAR")
            if "confirmed_at" not in cols:
                dt_type = "DATETIME" if is_sqlite else "TIMESTAMP"
                add_col(conn, "budget_additionals", "confirmed_at", dt_type)
            if "documents" not in cols:
                add_col(conn, "budget_additionals", "documents", "TEXT")

        # deleted_inventory — registros eliminados con resolución pendiente
        if "deleted_inventory" in tables:
            cols = {c["name"] for c in inspector.get_columns("deleted_inventory")}
            if "budget_id" not in cols:
                add_col(conn, "deleted_inventory", "budget_id", "INTEGER")
            if "budget_name" not in cols:
                add_col(conn, "deleted_inventory", "budget_name", "VARCHAR")
            if "locked_cost_soles" not in cols:
                add_col(conn, "deleted_inventory", "locked_cost_soles", "FLOAT NOT NULL DEFAULT 0.0")
            if "locked_cost_dolares" not in cols:
                add_col(conn, "deleted_inventory", "locked_cost_dolares", "FLOAT NOT NULL DEFAULT 0.0")
            if "unlocked_qty" not in cols:
                add_col(conn, "deleted_inventory", "unlocked_qty", "INTEGER NOT NULL DEFAULT 0")

        conn.commit()
    print("Migraciones manuales completadas.\n")


def bootstrap_superadmin():
    """Crea el usuario superadmin"""
    from services.auth_service import superadmin_exists, register_user

    db = SessionLocal()
    try:
        if not superadmin_exists(db):
            ok, msg = register_user(
                db,
                username="superadmin",
                email="admin@sistema-mrp.com",
                password="Admin123!",
                role="superadmin",
            )
            if ok:
                print("="*70)
                print("SUPERADMIN CREADO EXITOSAMENTE")
                print("="*70)
                print("   Usuario:     superadmin")
                print("   Email:       admin@sistema-mrp.com")
                print("   Contrasena:  Admin123!")
                print("   Cambia esta contrasena en el primer inicio de sesion!")
                print("="*70)
            else:
                print(f"[WARN] No se pudo crear superadmin: {msg}")
        else:
            print("[INFO] El superadmin ya existe.")
    finally:
        db.close()


def init_db():
    print("Iniciando base de datos...\n")

    run_migrations()

    # Crear todas las tablas (solo crea las que no existen)
    Base.metadata.create_all(bind=engine)
    print("Todas las tablas han sido verificadas/creadas.\n")

    bootstrap_superadmin()
    print("Inicializacion de la base de datos completada.")


if __name__ == "__main__":
    init_db()
