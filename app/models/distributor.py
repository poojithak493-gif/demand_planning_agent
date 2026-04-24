from sqlalchemy import Column, String
from app.core.database import Base

class Distributor(Base):
    __tablename__ = "distributors"

    distributor_id   = Column(String, primary_key=True)
    distributor_name = Column(String)
    email            = Column(String)
    region           = Column(String)