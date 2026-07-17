from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean

from app.database.database import Base


class DocumentNode(Base):

    __tablename__ = "document_nodes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    heading = Column(String)

    level = Column(Integer)

    body_text = Column(Text)

    content_hash = Column(String)

    parent_id = Column(
        Integer,
        ForeignKey("document_nodes.id"),
        nullable=True
    )

    # NEW FIELDS FOR VERSIONING

    document_version = Column(
        Integer,
        default=1
    )

    logical_node_id = Column(
        String,
        nullable=True
    )

    is_changed = Column(
        Boolean,
        default=False
    )