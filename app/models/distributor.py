from sqlalchemy import Column, String, Boolean
from app.core.database import Base


class Distributor(Base):
    __tablename__ = "distributors"

    distributor_id   = Column(String, primary_key=True)
    distributor_code = Column(String, unique=True)
    name             = Column(String)
    email            = Column(String)
    region           = Column(String)
    priority         = Column(String)
    is_active        = Column(Boolean, default=True)

    @property
    def distributor_name(self):
        return self.name