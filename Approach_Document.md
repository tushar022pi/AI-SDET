# AI SDET

## 1. Overview

This project implements an AI-assisted software testing pipeline that extracts structured requirements from PDF documents, preserves their hierarchy, tracks changes across document versions, and generates traceable test cases from selected requirements.

The system is built as a REST API using FastAPI, SQLAlchemy, SQLite, and an LLM integration with a deterministic mock mode for testing.

## 2. Architecture

The system is organized into the following layers:

- **PDF Parser** — extracts pages, text, and heading information from PDF documents.
- **Hierarchy Builder** — reconstructs document structure and parent-child relationships.
- **Node Service** — stores extracted requirements as versioned document nodes.
- **Version Service** — compares nodes across document versions using stable logical IDs and content hashes.
- **Selection API** — creates version-pinned selections of requirements.
- **Test Case Service** — generates structured QA test cases using either a mock generator or an LLM.
- **Staleness Analysis** — determines whether previously generated test cases are still valid after a new document version is ingested.
- **REST API** — exposes document, search, versioning, selection, test generation, and staleness operations.

### Data flow

```text
PDF
 ↓
PDF Parser
 ↓
Hierarchy Builder
 ↓
Versioned Document Nodes
 ↓
Selection
 ↓
LLM / Mock Generator
 ↓
Generated Test Cases
 ↓
Version Comparison
 ↓
Staleness / Impact Analysis
```

## 3. PDF Parsing Approach

The implementation uses PyMuPDF to extract text blocks and font information from PDF pages.

The parser identifies headings primarily through:

- Font size
- Text position
- Heading-like formatting
- Document ordering

Extracted information is then passed to the hierarchy builder.

The parser is intentionally separated from hierarchy reconstruction so that parsing and document structure can evolve independently.

## 4. Hierarchy Reconstruction

The hierarchy builder processes detected headings in document order.

Each heading receives:

- Heading text
- Hierarchy level
- Parent node
- Body text
- Content hash
- Stable logical node ID
- Document version

A stack-based approach is used to determine the parent of each heading.

For example:

```text
Installation
├── Initial Setup
├── Network Configuration
└── Safety Checks
```

The implementation also handles repeated headings by generating deterministic identifiers such as:

```text
installation
installation#2
installation#3
```

## 5. Node Identity and Version Matching

A key design decision was to separate **logical identity** from **content identity**.

The system uses:

```text
logical_node_id
```

to identify the same semantic section across document versions.

The node also stores:

```text
content_hash
```

which is a SHA-256 hash of the body text.

Therefore:

```text
Same logical ID + same content hash
        → unchanged

Same logical ID + different content hash
        → changed

Logical ID only in V2
        → new node
```

This prevents a content edit from incorrectly appearing as a completely new requirement.

### Matching normalization

Heading normalization:

- Converts text to lowercase
- Removes version numbers
- Removes leading numbering such as `1.` or `2.`
- Normalizes whitespace

For example:

```text
1. Installation
```

and:

```text
Installation
```

map to the same logical identifier.

## 6. Version Comparison

The version comparison API compares V1 and V2 nodes and returns:

- Unchanged nodes
- Changed nodes
- New nodes

For changed nodes, the API exposes both the old and new content hashes.

For the controlled CT-200 documents, the expected result is:

### Unchanged

- Initial Setup
- Safety Checks
- Troubleshooting

### Changed

- Installation
- Network Configuration

### New

- None

The changed sections demonstrate that the system detects semantic content changes while preserving unchanged requirements.

## 7. API Design

The main API endpoints include:

```text
GET  /
POST /ingest/{version}
GET  /sections/{version}
GET  /nodes
GET  /node/{node_id}
GET  /search
GET  /compare
POST /selection
POST /generate-tests/{node_id}
GET  /test-cases/{node_id}
GET  /test-cases/{node_id}/staleness
```

FastAPI also provides interactive API documentation through:

```text
/docs
```

## 8. Selection Strategy

A selection consists of:

```text
node_id + document version
```

This ensures that generated tests are tied to an exact version of a requirement.

Example:

```json
{
  "selections": [
    {
      "node_id": 8,
      "version": 2
    }
  ]
}
```

The selection is stored using a deterministic selection hash.

If the same selection is submitted again, the existing selection is reused instead of creating a duplicate.

This provides deterministic duplicate-selection handling.

## 9. LLM Test Generation

The test generation service accepts:

- Requirement heading
- Requirement body text

The LLM is instructed to generate **3–5 concrete and repeatable test cases**.

Each test case contains:

```json
{
  "title": "...",
  "steps": [
    "...",
    "..."
  ],
  "expected_result": "..."
}
```

The prompt explicitly instructs the model to use only the supplied requirement and not invent unsupported requirements.

## 10. Mock LLM Mode

Because external LLM access may not always be available, the implementation supports deterministic mock generation.

Mock mode is enabled by default:

```text
USE_MOCK_LLM=true
```

This allows:

- Offline development
- Repeatable tests
- CI execution without API credits
- Validation of the complete test-generation pipeline

Real LLM generation can be enabled through:

```text
USE_MOCK_LLM=false
OPENAI_API_KEY=<key>
```

## 11. Malformed LLM Output

LLM output is treated as untrusted input.

The service validates:

- JSON structure
- Presence of `test_cases`
- Number of test cases
- Required fields
- Non-empty titles
- Non-empty steps
- Non-empty expected results

If the initial response is malformed, the service sends a corrective prompt and retries.

The current strategy allows up to two attempts.

If both attempts fail, the service raises an explicit error rather than storing invalid test cases.

## 12. Test Case Traceability

Every generated test case is associated with the selected requirement.

The stored information includes the node relationship and selection relationship.

This provides traceability from:

```text
Generated Test Case
        ↓
Selection
        ↓
Document Node
        ↓
Document Version
        ↓
Original Requirement Text
```

This is important because a test case should be reproducible against the exact requirement from which it was generated.

## 13. Staleness and Impact Analysis

After a new document version is ingested, previously generated tests can be checked for staleness.

The system compares:

```text
Generated requirement hash
        vs.
Current requirement hash
```

Possible results include:

### Current

The test was generated from the latest version, or the requirement content has not changed.

### Stale

The same logical requirement exists, but its content hash changed.

### No new version

The logical requirement cannot be found in the latest version.

This provides a simple impact-analysis mechanism for identifying test cases that may need regeneration.

## 14. Edge Cases

The implementation considers several practical edge cases:

- Duplicate headings
- Heading numbering changes
- Version-number changes in document titles
- Changed requirement text
- New requirements
- Removed requirements
- Duplicate selections
- Malformed LLM responses
- Missing LLM API credentials
- Missing document nodes
- Requests for nonexistent versions or nodes

## 15. Testing Strategy

The project contains unit and API tests.

The tests cover:

- PDF parsing
- Hierarchy construction
- Hash generation
- Version matching
- API endpoints
- Search
- Version comparison
- Section retrieval
- Selection creation
- Duplicate selection handling
- Test generation
- Generated test retrieval
- Staleness detection
- LLM output validation

The complete test suite currently passes successfully.

## 16. Known Limitations

The current implementation has some deliberate limitations.

### OCR

The current parser primarily handles text-based PDFs. Scanned documents requiring OCR are not fully supported.

### Tables

Tables are not yet reconstructed into a complete structured representation.

### Figures and captions

Figure extraction and caption relationships are not fully modeled.

### Advanced heading detection

Heading detection relies mainly on PDF formatting characteristics. Highly irregular documents may require more advanced layout analysis.

### LLM reliability

LLM output can still be semantically imperfect even after structural validation.

### Version matching

The current matching strategy depends on normalized heading paths. Major document restructuring or heading renaming may require more advanced semantic matching.

## 17. Future Improvements

Possible future improvements include:

- OCR support for scanned PDFs
- Structured table extraction
- Figure and caption extraction
- Semantic embedding-based node matching
- More sophisticated document layout analysis
- LLM-generated change summaries
- Automatic test regeneration for stale requirements
- Better LLM error handling for API/network failures
- Persistent NoSQL storage for richer generated-test metadata
- Generalized comparison between arbitrary document versions
- Improved removal/deletion detection
- Test-case prioritization based on requirement impact

## 18. Design Rationale

The implementation favors deterministic and explainable behavior where possible.

Stable logical IDs provide a predictable mechanism for matching requirements across versions.

Content hashes provide an inexpensive and deterministic way to detect requirement changes.

Version-pinned selections ensure that generated tests remain traceable to the exact source requirement.

Mock LLM mode ensures that the application remains testable without depending on external API availability.

Validation and retry logic prevent malformed LLM responses from entering the stored test-case data.

## 19. Conclusion

The system provides an end-to-end pipeline for extracting structured requirements from documents, tracking requirement changes, generating traceable test cases, and identifying stale tests after document updates.

The architecture is intentionally modular so that the parser, hierarchy reconstruction, version matching, LLM generation, and impact-analysis components can be improved independently.