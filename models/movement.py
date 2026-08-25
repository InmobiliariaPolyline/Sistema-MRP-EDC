from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database import Base

class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))

    qty_change = Column(Integer)
    movement_type = Column(String)

    reference_type = Column(String)
    reference_id = Column(Integer)

    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True, index=True)

    user_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="movements")
    material = relationship("Material", back_populates="movements")
