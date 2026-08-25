from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class BudgetAdditional(Base):
    """Solicitudes "Adicional" — ajustes o agregados que NO son parte del
    alcance original de un proyecto (más fierro, más área construida, etc.).
    """
    __tablename__ = "budget_additionals"

    id           = Column(Integer, primary_key=True, index=True)
    budget_id    = Column(Integer, ForeignKey("budgets.id"), nullable=False, index=True)
    request_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    concept      = Column(String, nullable=False)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)

    confirmed         = Column(Boolean, nullable=False, default=False)
    confirmation_code = Column(String, nullable=True, index=True)
    confirmed_at      = Column(DateTime, nullable=True)
    documents         = Column(Text, nullable=True)
