# AI SDET — Decision Log

## 1. Why did you choose your hierarchy reconstruction approach?

The PDF is first parsed into pages, text blocks, and heading information.

The hierarchy is then reconstructed using heading formatting and document order. A stack-based approach is used to determine parent-child relationships between headings.

This approach was selected because it is:

- Simple to implement
- Deterministic
- Easy to test
- Suitable for the controlled PDF documents
- Independent of the database layer

The hierarchy builder also separates document structure from content hashing, allowing the same logical section to be matched across document versions even when its body text changes.

### Trade-off

A formatting-based approach may be less reliable for PDFs with inconsistent heading styles, scanned pages, or complex layouts.

A future implementation could combine font analysis, layout analysis, semantic classification, and OCR.

---

## 2. How do you decide whether a node is the same across document versions?

The system separates **logical identity** from **content identity**.

A normalized logical node ID is created from the heading and its hierarchy context.

Normalization removes information such as:

- Section numbering
- Version numbers
- Extra whitespace
- Case differences

For example:

```text
1. Installation
```

and:

```text
Installation
```

can map to the same logical node.

The actual requirement content is separately represented using a SHA-256 content hash.

The comparison therefore works as follows:

```text
Same logical ID
        │
        ├── Same content hash → Unchanged
        │
        └── Different hash → Changed

Logical ID exists only in V2 → New
```

### Why this approach?

Using the content hash alone would incorrectly treat an edited requirement as a completely new requirement.

For example:

Version 1:

```text
At least 50 mm clearance around ventilation openings.
```

Version 2:

```text
At least 75 mm clearance around ventilation openings.
```

These have different hashes but represent the same logical requirement.

Therefore:

```text
logical_node_id = stable identity
content_hash = change detection
```

### Failure modes

The approach may not correctly detect:

- Renamed headings
- Major hierarchy restructuring
- Sections moved to different parents
- Semantically equivalent headings with very different wording

These cases could be improved using semantic similarity or embedding-based matching.

---

## 3. How do you handle LLM failures and malformed output?

LLM output is treated as untrusted input.

The generation service requests a strict JSON structure containing:

```json
{
  "test_cases": [
    {
      "title": "...",
      "steps": [
        "..."
      ],
      "expected_result": "..."
    }
  ]
}
```

The response is validated before it is stored.

Validation checks include:

- Valid JSON
- Presence of `test_cases`
- Between 3 and 5 test cases
- Valid test-case objects
- Non-empty titles
- Non-empty step lists
- Non-empty expected results

If the first response is malformed, a corrective prompt is sent and the request is retried.

The current implementation allows two attempts.

If the second attempt also fails, the service returns an explicit error instead of storing malformed data.

### Why retry?

LLMs can occasionally return:

- Invalid JSON
- Missing fields
- Too few test cases
- Too many test cases
- Incorrect output structure

A corrective retry provides a simple recovery mechanism while keeping the behavior deterministic and bounded.

### Why not retry indefinitely?

Unlimited retries could:

- Increase API costs
- Increase latency
- Hide persistent failures
- Make debugging difficult

Therefore, the implementation uses a small fixed retry limit.

---

## 4. Why is mock LLM mode supported?

The system supports a deterministic mock LLM mode:

```text
USE_MOCK_LLM=true
```

This is the default.

The mock mode allows the complete application and test suite to run without:

- An OpenAI API key
- Internet access
- API credits
- Variable LLM responses

Real LLM generation can be enabled by setting:

```text
USE_MOCK_LLM=false
OPENAI_API_KEY=<key>
```

This separation also makes automated testing more reliable.

---

## 5. How are duplicate selections handled?

Selections are identified using a deterministic selection hash.

The hash is based on the selected node/version pairs.

If an identical selection is submitted again, the existing selection is reused.

This was chosen instead of creating duplicate selection records because the same selection represents the same logical generation request.

This provides:

- Idempotent behavior
- Reduced duplicate data
- Predictable API behavior
- Easier traceability

---

## 6. Why are test cases version-pinned?

Generated test cases need to remain traceable to the exact requirement from which they were generated.

Therefore, selections contain both:

```text
node_id
version
```

This prevents ambiguity when the same logical requirement changes in a later document version.

The traceability chain is:

```text
Test Case
    ↓
Selection
    ↓
Node + Version
    ↓
Requirement Content
```

This also allows the system to determine whether an existing test case is stale after a new version is ingested.

---

## 7. How is staleness determined?

The system compares the content hash of the requirement used to generate the test case with the current content hash.

Possible outcomes are:

```text
Latest version + same content
        → Current

Latest version + changed content
        → Stale

Requirement missing from latest version
        → No new version / impacted
```

This approach avoids regenerating every test case after every document update.

Only requirements whose content changed need further attention.

---

## 8. Why SQLite?

SQLite was selected because the project is a self-contained prototype and does not require a separate database server.

Advantages include:

- Zero database setup
- Simple local development
- Easy automated testing
- SQLAlchemy compatibility
- Sufficient for the expected assignment scale

The data model can later be migrated to PostgreSQL or another relational database without changing the overall service architecture significantly.

---

## 9. Why store generated test cases as structured JSON?

Generated test cases naturally have a nested structure:

```text
Test Cases
 ├── Test Case
 │    ├── Title
 │    ├── Steps
 │    └── Expected Result
 └── ...
```

JSON is therefore a natural representation for LLM output.

The application still validates the structure before storing it, rather than treating raw LLM output as trusted data.

---

## 10. Main Design Principle

The overall design prioritizes:

1. **Traceability**
2. **Deterministic version matching**
3. **Validation of LLM output**
4. **Reproducibility**
5. **Simple architecture**
6. **Testability**

The implementation intentionally favors simple and explainable mechanisms for the current document set while leaving clear extension points for OCR, semantic matching, richer document extraction, and more advanced LLM workflows.