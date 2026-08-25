from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))

    stock = Column(Integer, default=0)
    reserved = Column(Integer, default=0)

    # Optional link to the budget/project this stock belongs to
    budget_id   = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    budget_name = Column(String, nullable=True)

    # False when the linked project was deleted — stock is frozen until redirected
    is_active = Column(Boolean, default=True, nullable=False)

    # Cost locking system: locked_cost_* is the cumulative amount already
    # deducted from the budget for this inventory line (fixed even if material
    # prices change later). unlocked_qty are units added while the project was
    # deactivated — their cost is floating until the project is reactivated.
    unlocked_qty         = Column(Integer, default=0, nullable=False)
    locked_cost_soles    = Column(Float,   default=0.0, nullable=False)
    locked_cost_dolares  = Column(Float,   default=0.0, nullable=False)

    # Editable free-form note shown on the inventory card
    note = Column(Text, nullable=True)

    last_updated = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="inventory")
    material  = relationship("Material", back_populates="inventory")
    budget    = relationship("Budget", foreign_keys=[budget_id])