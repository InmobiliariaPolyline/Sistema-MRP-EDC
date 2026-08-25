from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # principal | obra
    location = Column(String)   # ciudad/distrito
    address = Column(String)    # dirección física
    owner_id = Column(Integer, nullable=True)  # FK a users.id; NULL = legado sin dueño

    movements = relationship("Movement", back_populates="warehouse")
    inventory = relationship("Inventory", back_populates="warehouse")