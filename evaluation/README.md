# Evaluation

Run `python scripts/run_evaluation.py` from the repository root. It evaluates the deterministic heuristic extractor against the small, synthetic labelled cases in `evaluation/labeled_invoices.json` and writes `evaluation/results.json` plus `evaluation/report.md`.

**Important:** this is a smoke-test dataset authored for the project, not a representative real-world invoice benchmark. The measured values must not be presented as production accuracy. OCR throughput and real-world success/failure rates require a larger labelled set containing digital PDFs, scans, images, XLS/XLSX and CSV from varied sources.
