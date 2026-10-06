from sqlalchemy import Column, Integer, String, Text
from app.database.database import Base


class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, index=True)
    selection_hash = Column(String, nullable=False)
    selections_json = Column(Text, nullable=False)