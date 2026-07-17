# Decision Log

## 1. Most likely silent failure

Incorrect heading detection.

A heading may be classified incorrectly and generate a wrong hierarchy.

Mitigation:

Unit tests and manual inspection.

---

## 2. Simplicity over correctness

Simple heading matching was used for version comparison.

Production system would require semantic matching.

---

## 3. Unhandled input

Scanned PDFs with image-only content.

Current system expects extractable text.

Future improvement would add OCR support.