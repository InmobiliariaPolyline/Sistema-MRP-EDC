from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from database import Base
from datetime import datetime


class Budget(Base):
    __tablename__ = "budgets"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    budget_soles   = Column(Float, nullable=False, default=0.0)
    budget_dolares = Column(Float, nullable=False, default=0.0)
    notes          = Column(String, nullable=True)
    is_active      = Column(Boolean, nullable=False, default=True)
    is_finished    = Column(Boolean, nullable=False, default=False)
    finished_at    = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    deactivated_at        = Column(DateTime, nullable=True)
    deactivation_reason   = Column(String, nullable=True)
    reactivation_date     = Column(DateTime, nullable=True)
    extension_history     = Column(Text, nullable=True)