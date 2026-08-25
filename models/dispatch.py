from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from models.requirement import Requirement

from datetime import datetime
from database import Base

class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))

    dispatch_date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer)
    guia_number = Column(String)
    status = Column(String, nullable=False, default="active")

    items = relationship("DispatchItem", backref="dispatch")
    requirement = relationship("Requirement", back_populates="dispatches")

    receipt = relationship("Receipt", back_populates="dispatch", uselist=False)
class DispatchItem(Base):
    __tablename__ = "dispatch_items"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))

    dispatched_qty = Column(Integer)

    material = relationship("Material")