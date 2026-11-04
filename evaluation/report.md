# Evaluation Report

- Dataset: small synthetic smoke-test dataset; not representative of real invoices
- Documents processed: 3
- Exact-match field accuracy: 95.8% (23/24)
- Document processing success rate: 100.0%
- Document failure rate: 0.0%
- Total measured wall time: 1.413 ms
- Average extraction time per document: 0.465 ms

## Limitations
This measures only the deterministic text heuristic against three synthetic text snippets. It does not measure OCR accuracy, varied layouts, real supplier invoices, LLM extraction, spreadsheet parsing, API throughput, or production reliability. Do not represent this score as real-world accuracy. Run a larger human-labelled benchmark before making performance claims.
