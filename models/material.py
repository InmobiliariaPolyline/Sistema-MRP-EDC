from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String)
    description = Column(String)
    unit_price = Column(Float, nullable=True, default=0.0)
    unit_price_dolares = Column(Float, nullable=True, default=0.0)

    movements = relationship("Movement", back_populates="material")
    inventory = relationship("Inventory", back_populates="material")