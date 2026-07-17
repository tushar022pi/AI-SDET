from app.parser.pdf_parser import PDFParser


def test_extract_pages():

    parser = PDFParser("data/sample.pdf")

    pages = parser.extract_pages()

    assert len(pages) > 0


def test_extract_headings():

    parser = PDFParser("data/sample.pdf")

    headings = parser.extract_headings()

    assert len(headings) > 0