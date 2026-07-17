
---

# Approach_Document.md

Paste:

```markdown
# Approach Document

## Architecture

FastAPI Backend

SQLite Database

SQLAlchemy ORM

PyPDF2 PDF Extraction

Pytest Unit Testing

---

## Parsing Strategy

1. Extract PDF text
2. Extract pages
3. Extract headings
4. Build hierarchy tree
5. Generate content hash
6. Store in database

---

## Hierarchy Design

Each node contains:

- Heading
- Level
- Body Text
- Parent Relationship
- Content Hash

---

## Versioning Strategy

Version 1 and Version 2 stored separately.

Matching strategy:

- Heading comparison
- Content hash comparison

If content hash changes:

is_changed = True

---

## API Design

Hierarchy browsing endpoint.

Single node retrieval endpoint.

Version comparison endpoint.

---

## Future Improvements

- OCR Support
- Better Heading Detection
- Fuzzy Matching
- LLM Test Generation