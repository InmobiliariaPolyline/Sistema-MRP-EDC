from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id"))

    receipt_date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer)

    items = relationship("ReceiptItem", backref="receipt")
    dispatch = relationship("Dispatch", back_populates="receipt")
    
class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))

    received_qty = Column(Integer)
    confirmed = Column(Boolean, default=False)