import json

from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.parser.pdf_parser import PDFParser

from app.services.hash_service import generate_hash
from app.services.hierarchy_builder import HierarchyBuilder
from app.services.node_service import NodeService
from app.services.version_service import VersionService
from app.services.test_case_service import TestCaseService

from app.database.database import Base
from app.database.database import engine
from app.database.db_session import get_db

from app.models.selection import Selection
from app.models.document_node import DocumentNode
from app.models.generated_test_case import GeneratedTestCase


app = FastAPI()


class SelectionItem(BaseModel):
    node_id: int
    version: int


class SelectionRequest(BaseModel):
    selections: list[SelectionItem]


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

    # Select the correct PDF based on document version
    if version == 1:
        pdf_path = "data/ct200_manual_v1.pdf"

    elif version == 2:
        pdf_path = "data/ct200_manual_v2.pdf"

    else:
        return {
            "message": "Only document versions 1 and 2 are supported"
        }

    parser = PDFParser(pdf_path)

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


@app.get("/sections/{version}")
def get_sections(
    version: int,
    db: Session = Depends(get_db)
):

    nodes = db.query(DocumentNode).filter(
        DocumentNode.document_version == version,
        DocumentNode.parent_id == None
    ).all()

    return [
        {
            "id": node.id,
            "heading": node.heading,
            "level": node.level,
            "document_version": node.document_version,
            "logical_node_id": node.logical_node_id,
            "content_hash": node.content_hash,
            "is_changed": node.is_changed
        }
        for node in nodes
    ]


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

    node = db.query(DocumentNode).filter(
        DocumentNode.id == node_id
    ).first()

    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found"
        )

    children = db.query(DocumentNode).filter(
        DocumentNode.parent_id == node.id
    ).all()

    return {
        "id": node.id,
        "heading": node.heading,
        "level": node.level,
        "body_text": node.body_text,
        "content_hash": node.content_hash,
        "document_version": node.document_version,
        "logical_node_id": node.logical_node_id,
        "is_changed": node.is_changed,
        "children": [
            {
                "id": child.id,
                "heading": child.heading,
                "level": child.level,
                "document_version": child.document_version,
                "logical_node_id": child.logical_node_id,
                "content_hash": child.content_hash,
                "is_changed": child.is_changed
            }
            for child in children
        ]
    }


@app.get("/compare")
def compare_versions(
    db: Session = Depends(get_db)
):

    v1_nodes = db.query(DocumentNode).filter(
        DocumentNode.document_version == 1
    ).all()

    v2_nodes = db.query(DocumentNode).filter(
        DocumentNode.document_version == 2
    ).all()

    version_service = VersionService()

    comparison = version_service.compare_versions(
        v1_nodes,
        v2_nodes
    )

    # Reset changed flags for V2 nodes
    for node in v2_nodes:
        node.is_changed = False

    # Mark changed V2 nodes
    for item in comparison["changed"]:

        for node in v2_nodes:

            if (
                node.heading == item["heading"]
                and node.content_hash == item["new_hash"]
            ):
                node.is_changed = True

    db.commit()

    return comparison


@app.get("/search")
def search_nodes(
    q: str,
    version: int = None,
    db: Session = Depends(get_db)
):

    query = db.query(DocumentNode).filter(
        DocumentNode.body_text.ilike(f"%{q}%")
    )

    if version is not None:

        query = query.filter(
            DocumentNode.document_version == version
        )

    nodes = query.all()

    result = []

    for node in nodes:

        result.append({
            "id": node.id,
            "heading": node.heading,
            "body_text": node.body_text,
            "document_version": node.document_version,
            "logical_node_id": node.logical_node_id,
            "content_hash": node.content_hash,
            "is_changed": node.is_changed
        })

    return {
        "query": q,
        "version": version,
        "results": result
    }


@app.post("/selection")
def create_selection(
    request: SelectionRequest,
    db: Session = Depends(get_db)
):

    selected_nodes = []

    # Validate every requested node/version pair
    for item in request.selections:

        node = db.query(DocumentNode).filter(
            DocumentNode.id == item.node_id,
            DocumentNode.document_version == item.version
        ).first()

        if not node:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Node {item.node_id} for "
                    f"version {item.version} not found"
                )
            )

        selected_nodes.append({
            "node_id": node.id,
            "version": node.document_version,
            "heading": node.heading,
            "body_text": node.body_text,
            "content_hash": node.content_hash,
            "logical_node_id": node.logical_node_id
        })

    # Create a deterministic representation of the selection.
    # The exact node content hash is included, so if the
    # requirement changes, the selection hash also changes.
    selection_data = json.dumps(
        selected_nodes,
        sort_keys=True
    )

    selection_hash = generate_hash(
        selection_data
    )

    # Reuse an existing identical selection instead of
    # creating duplicate selection records.
    existing_selection = db.query(Selection).filter(
        Selection.selection_hash == selection_hash
    ).first()

    if existing_selection:

        return {
            "selection_id": existing_selection.id,
            "selection_hash": existing_selection.selection_hash,
            "selection_count": len(selected_nodes),
            "selections": selected_nodes,
            "reused": True
        }

    # Create a new selection
    selection = Selection(
        selection_hash=selection_hash,
        selections_json=selection_data
    )

    db.add(selection)

    db.commit()

    db.refresh(selection)

    return {
        "selection_id": selection.id,
        "selection_hash": selection.selection_hash,
        "selection_count": len(selected_nodes),
        "selections": selected_nodes,
        "reused": False
    }


@app.get("/generate-tests/{node_id}")
def generate_tests(
    node_id: int,
    selection_id: int = None,
    db: Session = Depends(get_db)
):

    node = db.query(DocumentNode).filter(
        DocumentNode.id == node_id
    ).first()

    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found"
        )

    # If a selection_id is provided, verify that the node
    # belongs to that selection.
    if selection_id is not None:

        selection = db.query(Selection).filter(
            Selection.id == selection_id
        ).first()

        if not selection:
            raise HTTPException(
                status_code=404,
                detail=f"Selection {selection_id} not found"
            )

        selected_data = json.loads(
            selection.selections_json
        )

        selected_node_ids = [
            item["node_id"]
            for item in selected_data
        ]

        if node.id not in selected_node_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Node {node_id} does not belong "
                    f"to selection {selection_id}"
                )
            )

    test_case_service = TestCaseService()

    test_cases = test_case_service.generate_test_cases(
        node.heading,
        node.body_text
    )

    saved_test_cases = []

    for test_case in test_cases:

        saved_test_case = GeneratedTestCase(
            selection_id=selection_id,
            node_id=node.id,
            document_version=node.document_version,
            logical_node_id=node.logical_node_id,
            source_content_hash=node.content_hash,
            title=test_case["title"],
            steps=json.dumps(test_case["steps"]),
            expected_result=test_case["expected_result"]
        )

        db.add(saved_test_case)

        db.flush()

        saved_test_cases.append({
            "id": saved_test_case.id,
            "selection_id": saved_test_case.selection_id,
            "title": saved_test_case.title,
            "steps": test_case["steps"],
            "expected_result": saved_test_case.expected_result
        })

    db.commit()

    return {
        "selection_id": selection_id,
        "node_id": node.id,
        "document_version": node.document_version,
        "heading": node.heading,
        "source_content_hash": node.content_hash,
        "test_cases": saved_test_cases
    }


@app.get("/test-cases/{node_id}")
def get_test_cases(
    node_id: int,
    db: Session = Depends(get_db)
):

    test_cases = (
        db.query(GeneratedTestCase)
        .filter(
            GeneratedTestCase.node_id == node_id
        )
        .all()
    )

    if not test_cases:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No generated test cases found "
                f"for node {node_id}"
            )
        )

    result = []

    for test_case in test_cases:

        result.append({
            "id": test_case.id,
            "selection_id": test_case.selection_id,
            "node_id": test_case.node_id,
            "document_version": test_case.document_version,
            "logical_node_id": test_case.logical_node_id,
            "source_content_hash": test_case.source_content_hash,
            "title": test_case.title,
            "steps": json.loads(test_case.steps),
            "expected_result": test_case.expected_result
        })

    return {
        "node_id": node_id,
        "test_case_count": len(result),
        "test_cases": result
    }


@app.get("/test-cases/{node_id}/staleness")
def check_test_case_staleness(
    node_id: int,
    db: Session = Depends(get_db)
):

    node = db.query(DocumentNode).filter(
        DocumentNode.id == node_id
    ).first()

    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found"
        )

    test_cases = db.query(GeneratedTestCase).filter(
        GeneratedTestCase.node_id == node_id
    ).all()

    if not test_cases:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No generated test cases found "
                f"for node {node_id}"
            )
        )

    # Find the newest document version available in the database.
    latest_version = db.query(
        DocumentNode.document_version
    ).order_by(
        DocumentNode.document_version.desc()
    ).first()

    if latest_version is None:

        return {
            "node_id": node_id,
            "test_case_count": len(test_cases),
            "test_cases": []
        }

    current_version_number = latest_version[0]

    result = []

    for test_case in test_cases:

        # Find the corresponding requirement in the newest
        # available document version using the stable
        # logical node ID.
        current_node = db.query(DocumentNode).filter(
            DocumentNode.logical_node_id ==
            test_case.logical_node_id,
            DocumentNode.document_version ==
            current_version_number
        ).first()

        if not current_node:

            result.append({
                "test_case_id": test_case.id,
                "selection_id": test_case.selection_id,
                "node_id": test_case.node_id,
                "logical_node_id": test_case.logical_node_id,
                "generated_from_version": test_case.document_version,
                "current_version": current_version_number,
                "source_content_hash": (
                    test_case.source_content_hash
                ),
                "current_content_hash": None,
                "status": "no_new_version",
                "reason": (
                    "The corresponding requirement was not "
                    "found in the newer document version."
                )
            })

            continue

        # If the generated test case came from the latest
        # version, it is already current.
        if test_case.document_version == current_version_number:

            status = "current"

            reason = (
                "The test case was generated from the latest "
                "available document version."
            )

        elif (
            current_node.content_hash ==
            test_case.source_content_hash
        ):

            status = "current"

            reason = (
                "The requirement content is unchanged since "
                "the test case was generated."
            )

        else:

            status = "stale"

            reason = (
                "The requirement content changed after the "
                "test case was generated."
            )

        result.append({
            "test_case_id": test_case.id,
            "selection_id": test_case.selection_id,
            "node_id": test_case.node_id,
            "logical_node_id": test_case.logical_node_id,
            "generated_from_version": test_case.document_version,
            "current_version": current_node.document_version,
            "source_content_hash": (
                test_case.source_content_hash
            ),
            "current_content_hash": (
                current_node.content_hash
            ),
            "status": status,
            "reason": reason
        })

    return {
        "node_id": node_id,
        "test_case_count": len(result),
        "test_cases": result
    }