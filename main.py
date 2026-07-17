from fastapi import FastAPI
from fastapi import Depends

from sqlalchemy.orm import Session

from app.parser.pdf_parser import PDFParser

from app.services.hierarchy_builder import HierarchyBuilder
from app.services.node_service import NodeService
from app.services.version_service import VersionService
from app.services.test_case_service import TestCaseService

from app.database.database import Base
from app.database.database import engine
from app.database.db_session import get_db

from app.models.document_node import DocumentNode


app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "AI SDET Assignment Running"
    }


@app.get("/read-pdf")
def read_pdf():

    parser = PDFParser("data/sample.pdf")

    text = parser.extract_text()

    return {
        "text": text[:3000]
    }


@app.get("/pages")
def get_pages():

    parser = PDFParser("data/sample.pdf")

    return parser.extract_pages()


@app.get("/headings")
def get_headings():

    parser = PDFParser("data/sample.pdf")

    return parser.extract_headings()


@app.get("/hierarchy")
def get_hierarchy():

    parser = PDFParser("data/sample.pdf")

    pages = parser.extract_pages()

    headings = parser.extract_headings()

    builder = HierarchyBuilder()

    hierarchy = builder.build(
        pages,
        headings
    )

    return hierarchy


@app.post("/ingest/{version}")
def ingest_document(
    version: int,
    db: Session = Depends(get_db)
):

    parser = PDFParser("data/sample.pdf")

    pages = parser.extract_pages()

    headings = parser.extract_headings()

    builder = HierarchyBuilder()

    hierarchy = builder.build(
        pages,
        headings
    )

    service = NodeService()

    return service.save_nodes(
        db,
        hierarchy,
        version
    )


@app.get("/nodes")
def get_nodes(
    db: Session = Depends(get_db)
):

    nodes = db.query(
        DocumentNode
    ).all()

    result = []

    for node in nodes:

        result.append({
            "id": node.id,
            "heading": node.heading,
            "level": node.level,
            "document_version": node.document_version,
            "logical_node_id": node.logical_node_id,
            "is_changed": node.is_changed
        })

    return result


@app.get("/node/{node_id}")
def get_node(
    node_id: int,
    db: Session = Depends(get_db)
):

    node = db.query(
        DocumentNode
    ).filter(
        DocumentNode.id == node_id
    ).first()

    if not node:
        return {
            "message": "Node not found"
        }

    return {
        "id": node.id,
        "heading": node.heading,
        "level": node.level,
        "body_text": node.body_text,
        "content_hash": node.content_hash,
        "document_version": node.document_version,
        "logical_node_id": node.logical_node_id,
        "is_changed": node.is_changed
    }


@app.get("/compare")
def compare_versions(
    db: Session = Depends(get_db)
):

    version1_nodes = db.query(
        DocumentNode
    ).filter(
        DocumentNode.document_version == 1
    ).all()

    version2_nodes = db.query(
        DocumentNode
    ).filter(
        DocumentNode.document_version == 2
    ).all()

    service = VersionService()

    return service.compare_versions(
        version1_nodes,
        version2_nodes
    )


@app.get("/generate-tests/{node_id}")
def generate_tests(
    node_id: int,
    db: Session = Depends(get_db)
):

    node = db.query(
        DocumentNode
    ).filter(
        DocumentNode.id == node_id
    ).first()

    if not node:
        return {
            "message": "Node not found"
        }

    service = TestCaseService()

    test_cases = service.generate_test_cases(
        node.heading,
        node.body_text
    )

    return {
        "node_id": node.id,
        "heading": node.heading,
        "test_cases": test_cases
    }