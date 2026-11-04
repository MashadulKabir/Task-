# Known Limitations and Honest Status

1. **Background jobs:** FastAPI `BackgroundTasks` runs work in the API process. It is not a durable queue and is not suitable for multi-worker production deployment. A Redis-backed Celery/RQ worker is a recommended next step.
2. **LLM extraction:** optional adapter expects an OpenAI-compatible endpoint. The default heuristic is not robust across arbitrary invoice layouts. Line-item extraction is incomplete. Human review is required.
3. **OCR:** Tesseract is an external system dependency. OCR quality depends on language packs, scan resolution, skew, rotation and image quality. Current preprocessing is intentionally modest.
4. **XLS:** legacy `.xls` parsing requires `xlrd`; test with real files on the target machine.
5. **Search:** semantic mode currently uses TF-IDF lexical similarity, not vector embeddings. No external vector database is included.
6. **Database:** SQLite is used for easy local setup. Production multi-user deployments should use PostgreSQL with migrations and access controls.
7. **Frontend:** React interface is an MVP. Install npm dependencies and run a production build locally before submission. This environment did not have Vite installed, so a frontend build could not be verified here.
8. **Security:** no user authentication, tenant isolation, antivirus scanning, encryption-at-rest policy, or production rate limiting is implemented. Keep it local for the assessment unless these controls are added.
9. **Evaluation:** included benchmark contains three synthetic text-only cases. It does not validate OCR or generalization to real invoices. Report only metrics generated from your actual labelled dataset.
10. **Tests:** current automated suite has five passing tests. This is not full coverage of every format, failure mode or UI workflow.

Do not describe these limitations as completed features. The assessment asks for reliability and scalability; the current implementation demonstrates a foundation, not production readiness.
