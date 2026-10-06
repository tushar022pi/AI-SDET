from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey

from app.database.database import Base


class GeneratedTestCase(Base):

    __tablename__ = "generated_test_cases"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    selection_id = Column(
        Integer,
        ForeignKey("selections.id"),
        nullable=True
    )

    node_id = Column(
        Integer,
        ForeignKey("document_nodes.id"),
        nullable=False
    )

    document_version = Column(
        Integer,
        nullable=False
    )

    logical_node_id = Column(
        String,
        nullable=True
    )

    source_content_hash = Column(
        String,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    steps = Column(
        Text,
        nullable=False
    )

    expected_result = Column(
        Text,
        nullable=False
    )