from app.parser.pdf_parser import PDFParser
from app.services.hierarchy_builder import HierarchyBuilder


def test_hierarchy_build():

    parser = PDFParser("data/sample.pdf")

    pages = parser.extract_pages()
    headings = parser.extract_headings()

    builder = HierarchyBuilder()

    hierarchy = builder.build(
        pages,
        headings
    )

    assert len(hierarchy) > 0


def test_content_hash_exists():

    parser = PDFParser("data/sample.pdf")

    pages = parser.extract_pages()
    headings = parser.extract_headings()

    builder = HierarchyBuilder()

    hierarchy = builder.build(
        pages,
        headings
    )

    assert hierarchy[0]["content_hash"] is not None