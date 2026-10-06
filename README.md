# AI-SDET 

An AI-assisted Software Development Engineer in Test (SDET) system for extracting structured requirements from document versions, detecting requirement changes, generating test cases, and identifying stale test cases after document updates.

## Overview

This project implements a backend API that:

- Parses PDF documents into structured content.
- Reconstructs document hierarchy.
- Assigns stable logical IDs to requirements across document versions.
- Stores document nodes and content hashes.
- Ingests multiple document versions without destroying previous versions.
- Compares document versions and detects changed/unchanged requirements.
- Searches requirements by text and document version.
- Creates version-pinned requirement selections.
- Generates 3–5 test cases from selected requirements.
- Stores generated test cases with full source traceability.
- Retrieves previously generated test cases.
- Detects whether generated test cases are stale after a newer document version is ingested.

The project is intentionally backend-focused. A frontend/UI is not required by the assignment.

---

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- PyMuPDF / PDF parsing
- OpenAI API integration
- Pytest

The application supports a mock LLM mode so the complete workflow can be tested without requiring an OpenAI API key or API credits.

---

## Project Structure

```text
AI-SDET/
│
├── app/
│   ├── database/
│   │   ├── database.py
│   │   └── db_session.py
│   │
│   ├── models/
│   │   ├── document_node.py
│   │   ├── generated_test_case.py
│   │   └── selection.py
│   │
│   ├── parser/
│   │   └── pdf_parser.py
│   │
│   ├── services/
│   │   ├── hash_service.py
│   │   ├── hierarchy_builder.py
│   │   ├── node_service.py
│   │   ├── test_case_service.py
│   │   └── version_service.py
│   │
│   └── tests/
│       ├── test_api.py
│       ├── test_hierarchy.py
│       ├── test_parser.py
│       ├── test_test_case_service.py
│       └── test_versioning.py
│
├── data/
│   ├── sample.pdf
│   ├── ct200_manual_v1.pdf
│   └── ct200_manual_v2.pdf
│
├── main.py
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/tushar022pi/AI-SDET.git
cd AI-SDET
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell execution policy prevents activation, the project can still be run using the Python executable inside the virtual environment.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## Environment Variables

The project defaults to mock LLM mode.

```text
USE_MOCK_LLM=true
```

This allows the complete test-generation workflow to run without an OpenAI API key.

For real LLM generation, set:

```powershell
$env:USE_MOCK_LLM="false"
$env:OPENAI_API_KEY="your-api-key"
```

The OpenAI API is only used when mock mode is disabled.

---

## Running the Application

Start the FastAPI server with:

```powershell
uvicorn main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Running Tests

Run the complete test suite:

```powershell
pytest
```

The current implementation has **23 passing tests** covering:

- API endpoints
- PDF parsing
- hierarchy construction
- version comparison
- test-case generation
- output validation
- selection behavior
- duplicate selection handling
- generated test retrieval
- stale test detection

Expected result:

```text
23 passed
```

---

# Document Version Workflow

The project includes two controlled CT-200 Controller Manual versions.

### Version 1

```text
data/ct200_manual_v1.pdf
```

### Version 2

```text
data/ct200_manual_v2.pdf
```

The documents intentionally contain both unchanged and changed requirements.

For example:

### Installation

Version 1:

```text
At least 50 mm clearance around ventilation openings.
```

Version 2:

```text
At least 75 mm clearance around ventilation openings.
```

This should be detected as a changed requirement.

### Network Configuration

Version 1 requires static IPv4 configuration.

Version 2 changes the requirement to DHCP followed by address reservation.

This should also be detected as changed.

Other sections remain unchanged.

---

# Ingest Version 1

Start the server and send:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ingest/1
```

This stores the Version 1 document nodes.

---

# Ingest Version 2

After Version 1 has been ingested:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ingest/2
```

Version 1 remains in the database.

Version 2 is stored as a separate document version.

The system does not overwrite the Version 1 requirements.

---

# API Endpoints

## Health Check

```http
GET /
```

Example:

```json
{
  "message": "AI SDET Assignment Running"
}
```

---

## Extract PDF Text

```http
GET /read-pdf
```

Extracts text from the sample PDF.

---

## Extract Pages

```http
GET /pages
```

Returns parsed PDF page information.

---

## Extract Headings

```http
GET /headings
```

Returns detected headings.

---

## Build Hierarchy

```http
GET /hierarchy
```

Builds the structured hierarchy from the sample document.

---

## Ingest Document Version

```http
POST /ingest/{version}
```

Examples:

```http
POST /ingest/1
POST /ingest/2
```

---

## Get Sections

```http
GET /sections/{version}
```

Returns the top-level sections for a specific document version.

Example:

```http
GET /sections/1
```

---

## Get All Nodes

```http
GET /nodes
```

Returns all stored document nodes across versions.

---

## Get a Node

```http
GET /node/{node_id}
```

Returns:

- Node metadata
- Full body text
- Content hash
- Logical node ID
- Document version
- Changed status
- Immediate children

---

## Search Requirements

```http
GET /search?q={query}
```

Optional version filtering:

```http
GET /search?q=DHCP&version=2
```

The search operates against stored requirement body text.

---

## Compare Versions

```http
GET /compare
```

The comparison identifies:

- unchanged requirements
- changed requirements
- new requirements

For changed requirements, the API returns both the old and new content hashes.

The controlled CT-200 example should identify:

```text
Changed:
- 1. Installation
- 3. Network Configuration

Unchanged:
- 2. Initial Setup
- 4. Safety Checks
- 5. Troubleshooting
```

---

# Version Matching Strategy

The system separates:

1. **Logical identity**
2. **Content identity**

A logical node ID represents the same conceptual requirement across document versions.

The content hash represents the exact requirement content.

For example:

```text
logical_node_id:
installation
```

The content hash can change when the requirement changes.

Therefore:

```text
same logical_node_id
+
different content_hash
=
changed requirement
```

Whereas:

```text
same logical_node_id
+
same content_hash
=
unchanged requirement
```

This prevents the system from treating a changed requirement as an entirely new requirement.

---

# Selection API

Requirements can be selected with a specific document version.

```http
POST /selection
```

Example:

```json
{
  "selections": [
    {
      "node_id": 2,
      "version": 1
    }
  ]
}
```

The selection stores:

- node ID
- document version
- heading
- body text
- content hash
- logical node ID

This makes the selection version-pinned and traceable to the exact requirement content used for test generation.

---

# Duplicate Selection Policy

Identical selections are reused.

A deterministic selection hash is calculated from the selected node information.

If an identical selection already exists, the API returns the existing selection instead of creating a duplicate.

This provides idempotent selection behavior.

A selection whose underlying requirement content changes produces a different selection hash.

---

# Test Case Generation

Test cases can be generated from a selected requirement.

```http
GET /generate-tests/{node_id}?selection_id={selection_id}
```

Example:

```http
GET /generate-tests/2?selection_id=1
```

Each generated test case contains:

- title
- steps
- expected result
- source node
- document version
- logical node ID
- source content hash
- selection ID

This provides traceability between the generated test and the exact requirement used to generate it.

---

# LLM Behavior

The application supports two modes.

## Mock Mode

Default:

```text
USE_MOCK_LLM=true
```

Mock mode generates deterministic test cases without making an external API request.

This allows tests and demonstrations to run without API credits.

## Real LLM Mode

When:

```text
USE_MOCK_LLM=false
```

the application uses the OpenAI API.

The generated response is expected to contain JSON in the following structure:

```json
{
  "test_cases": [
    {
      "title": "Test title",
      "steps": [
        "Step 1",
        "Step 2"
      ],
      "expected_result": "Expected result"
    }
  ]
}
```

The service validates:

- JSON validity
- `test_cases` presence
- 3–5 test cases
- test case titles
- test steps
- expected results

If the LLM returns malformed output, a corrective prompt is attempted before the request is considered failed.

---

# Generated Test Retrieval

```http
GET /test-cases/{node_id}
```

Returns all stored test cases associated with the requirement node.

Stored information includes the original source hash and version.

---

# Staleness Detection

```http
GET /test-cases/{node_id}/staleness
```

The system finds the newest document version available.

It then compares the content hash of the current requirement with the hash stored when the test case was generated.

Possible statuses include:

### Current

The requirement content has not changed.

### Stale

The requirement content has changed since the test case was generated.

### No New Version

The corresponding logical requirement cannot be found in the newer version.

This means an old generated test case can be traced back to the exact requirement version from which it was created.

---

# Example End-to-End Flow

## 1. Ingest V1

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ingest/1
```

## 2. Ingest V2

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ingest/2
```

## 3. Compare versions

```powershell
Invoke-RestMethod http://127.0.0.1:8000/compare
```

Expected changed requirements:

```text
1. Installation
3. Network Configuration
```

## 4. Create a selection

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/selection `
  -ContentType "application/json" `
  -Body '{"selections":[{"node_id":2,"version":1}]}'
```

## 5. Generate tests

Use the returned selection ID:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:8000/generate-tests/2?selection_id=1"
```

## 6. Retrieve generated tests

```powershell
Invoke-RestMethod `
  http://127.0.0.1:8000/test-cases/2
```

## 7. Check staleness

```powershell
Invoke-RestMethod `
  http://127.0.0.1:8000/test-cases/2/staleness
```

Because the Installation requirement changed between V1 and V2, a test generated from the V1 requirement should be reported as:

```text
stale
```

---

# Testing Strategy

The test suite is divided into several areas.

## Parser Tests

Verify PDF text and heading extraction.

## Hierarchy Tests

Verify:

- heading hierarchy
- parent/child relationships
- logical node IDs

## Versioning Tests

Verify:

- unchanged requirements
- changed requirements
- logical matching
- content hash comparison

## Test Generation Tests

Verify:

- mock output
- required structure
- 3–5 test cases
- malformed output validation

## API Tests

Verify:

- document ingestion
- sections
- node retrieval
- search
- version comparison
- selections
- duplicate selection reuse
- test generation
- test retrieval
- staleness detection

---

# Known Limitations

The implementation focuses on the required backend workflow and controlled CT-200 example.

Current limitations include:

- PDF hierarchy detection relies heavily on heading formatting and font information.
- Complex PDFs with ambiguous formatting may require additional heuristics.
- Table extraction is not yet a dedicated structured-table pipeline.
- Figure/image extraction is not yet represented as first-class document nodes.
- OCR for scanned PDFs would require an additional OCR engine.
- The current controlled documents do not require complex OCR/table reconstruction.
- Real LLM calls depend on a configured OpenAI API key.
- The mock LLM is intentionally deterministic for offline testing.
- The current implementation primarily demonstrates the V1 → V2 versioning workflow.

---

# Future Improvements

Potential production improvements include:

- OCR support for scanned documents.
- Dedicated table extraction and storage.
- Figure and caption extraction.
- Better heading classification using multiple document-layout signals.
- More robust semantic matching when headings are substantially renamed.
- Embedding-based requirement matching as a fallback to logical IDs.
- LLM-based semantic diff summaries.
- LLM output schema enforcement using structured output.
- Retry handling for transient API/network errors.
- Background processing for large documents.
- PostgreSQL for production persistence.
- Authentication and authorization.
- API pagination.
- Richer generated test-case lifecycle management.
- Automated regression-test impact analysis.
- Frontend visualization of document changes and stale tests.

---

#  Design Decisions

The implementation makes several deliberate design choices.

### Stable identity vs content hash

A requirement's logical identity is kept separate from its content hash.

This allows the system to distinguish:

```text
same requirement, changed wording
```

from:

```text
new requirement
```

### Version-pinned selections

Selections store the exact document version and content hash so test generation remains reproducible.

### Duplicate selections

Identical selections are reused rather than creating unnecessary duplicate selection records.

### Test traceability

Generated tests store the source node, document version, logical node ID, and source content hash.

This makes it possible to determine whether an existing test is still valid after document changes.

### Mock LLM

Mock mode allows the complete assignment workflow to be tested without depending on external API availability or API credits.

---

# License

This project was created as part of an AI-SDET internship assignment.