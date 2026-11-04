# InvoiceAI — Invoice Document Processing MVP

A Python/FastAPI + React application for uploading invoice documents, extracting text, extracting invoice fields, validating totals, storing processing history, and searching processed documents.

> **Project status: assessment MVP / in development.** This repository includes working core paths and tests, but it is not a production-hardened service. Read `docs/KNOWN_LIMITATIONS.md` before submission and disclose AI-assisted development in `AI_ASSISTANCE.md`.

## Features mapped to the assignment

| Assignment | Implementation location | Current scope |
|---|---|---|
| 1. Document processing | `app/document_reader.py` | PDF digital text + OCR fallback, JPG/JPEG/PNG/TIF/TIFF OCR, XLSX/XLS and CSV parsing. PDF pages and workbook sheets are iterated. OCR uses grayscale/autocontrast/contrast/sharpen preprocessing. |
| 2. AI extraction | `app/extractor.py`, `prompts/invoice_extraction.txt` | Structured invoice JSON; deterministic regex baseline; optional OpenAI-compatible local LLM endpoint; missing values remain null in the baseline. Line-item extraction is limited and needs more layout-specific work. |
| 3. Validation | `app/validator.py` | Required-field checks, numeric/negative checks, subtotal + tax vs total, line-item sum warning, duplicate invoice check. |
| 4. Backend API | `app/main.py`, `app/worker.py` | Upload, list, detail/status, result, corrections, reprocess, keyword/semantic-like search. Uses FastAPI BackgroundTasks. |
| 5. Database/search | `app/database.py`, `app/search.py` | SQLite document metadata, extracted text, JSON results, validation, processing history; keyword and TF-IDF similarity search. |
| 6. Frontend | `frontend/` | React/Vite dashboard for upload, status/list, details and corrections/search (review UI is MVP-level). |
| 7. Testing/evaluation | `tests/`, `scripts/run_evaluation.py`, `evaluation/` | Automated tests and a reproducible synthetic text-extraction smoke benchmark. It is not a representative real-world benchmark. |

## Requirements

- Windows 10/11, macOS or Linux
- Python 3.10+
- Node.js 18+ and npm
- Tesseract OCR installed and available on PATH for image/scanned-PDF OCR
- Optional: a local OpenAI-compatible LLM server such as llama.cpp for LLM extraction

## Windows setup (PowerShell)

Open PowerShell in the repository folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000`  
Swagger docs: `http://127.0.0.1:8000/docs`

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

For OCR, install Tesseract and either add it to PATH or set `TESSERACT_CMD` in `.env` to the full path to `tesseract.exe`.

## Local LLM configuration (optional)

The default is `USE_LOCAL_LLM=false`, so the application uses its deterministic heuristic baseline. To use a local OpenAI-compatible server, edit `.env`:

```dotenv
USE_LOCAL_LLM=true
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=local-model
LLM_API_KEY=not-needed
```

Restart the API after changing `.env`. The configured model must expose `/chat/completions`. The LLM output is normalized, but should still be reviewed; do not assume model output is correct.

## API quick reference

- `GET /health`
- `POST /api/documents/upload` — multipart field `files`, accepts multiple files
- `GET /api/documents` — optional `status`, `q`, `limit`
- `GET /api/documents/{id}` — metadata, result, validation and history
- `GET /api/documents/{id}/result`
- `PATCH /api/documents/{id}/corrections` — JSON object in `values`
- `POST /api/documents/{id}/reprocess`
- `GET /api/search?q=...&mode=keyword|semantic`

## Run tests and evaluation

```powershell
python -m pytest -q
python scripts/run_evaluation.py
```

The evaluation writes `evaluation/results.json` and `evaluation/report.md`. The included labelled data has only three synthetic text examples and measures the heuristic extractor's exact-match score on eight scalar fields. The reported number is a smoke-test metric only, not a claim of real-world invoice accuracy. Add manually labelled, representative PDFs, scans, images and spreadsheets before reporting meaningful accuracy.

## Git repository setup

```powershell
git init
git add .
git commit -m "Initial InvoiceAI assessment MVP"
```

Create an empty GitHub repository, then add its URL:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/InvoiceAI.git
git push -u origin main
```

Do not commit `.env`, private invoices, API keys, or personal data. `.gitignore` excludes local environment and storage content.

## Submission checklist

- [ ] Push source code to a Git repository and include the repository URL in the submission email.
- [ ] Include this README and setup instructions.
- [ ] Include `docs/architecture.md` and `docs/database_schema.md` (Mermaid diagrams).
- [ ] Run backend and frontend locally; verify upload, status, result, correction and search flows.
- [ ] Test PDF, image, Excel and CSV examples, including malformed files and scanned documents.
- [ ] Run pytest and include the actual terminal output / test report.
- [ ] Run the evaluation script; expand the labelled dataset before claiming meaningful accuracy.
- [ ] Record a walkthrough showing upload → processing → extracted result → validation → correction/search.
- [ ] Include `AI_ASSISTANCE.md` and the prompt in `prompts/` as the AI-assisted development disclosure.

## Security and production notes

See `docs/KNOWN_LIMITATIONS.md`. This project is a local assessment MVP and should not be exposed to the public internet without authentication, authorization, malware scanning, rate limiting, durable queueing, secure storage and deployment hardening.
