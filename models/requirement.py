from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id_obra = Column(Integer, ForeignKey("warehouses.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    notes = Column(String)

    budget_id   = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    budget_name = Column(String, nullable=True)

    items = relationship("RequirementItem", back_populates="requirement")
    dispatches = relationship("Dispatch", back_populates="requirement")

class RequirementItem(Base):
    __tablename__ = "requirement_items"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    material=relationship("Material")

    requested_qty = Column(Integer)
    fulfilled_qty = Column(Integer, default=0)
    status = Column(String, default="pending")

    requirement = relationship("Requirement", back_populates="items")