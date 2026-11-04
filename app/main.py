import hashlib
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from .database import init_db, connection, now, add_history, document_dict
from .worker import process_document
from .search import keyword_match, semantic_rank

app = FastAPI(title="InvoiceAI API", version="1.0.0", description="Document ingestion and invoice extraction MVP")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

class Correction(BaseModel):
    values: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "InvoiceAI"}

@app.post("/api/documents/upload")
async def upload_documents(background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "At least one file is required.")
    uploaded = []
    for file in files:
        original_name = Path(file.filename or "unnamed").name
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(415, f"Unsupported file type: {ext}")
        content = await file.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"{original_name} exceeds the {MAX_UPLOAD_MB} MB limit.")
        if not content:
            raise HTTPException(400, f"{original_name} is empty.")
        digest = hashlib.sha256(content).hexdigest()
        stored = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        stored.write_bytes(content)
        with connection() as db:
            cur = db.execute("INSERT INTO documents(filename,stored_name,file_type,file_size,sha256,status,created_at,updated_at) VALUES(?,?,?,?,?,'queued',?,?)",
                             (original_name, str(stored), ext.lstrip('.'), len(content), digest, now(), now()))
            doc_id = cur.lastrowid
            add_history(db, doc_id, "uploaded", {"sha256": digest})
        background_tasks.add_task(process_document, doc_id)
        uploaded.append({"id": doc_id, "filename": original_name, "status": "queued"})
    return {"uploaded": uploaded}

@app.get("/api/documents")
def list_documents(status: str | None = None, q: str | None = None, limit: int = Query(100, ge=1, le=500)):
    with connection() as db:
        rows = db.execute("SELECT * FROM documents ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        items = [document_dict(row) for row in rows]
    if status:
        items = [item for item in items if item["status"] == status]
    if q:
        items = [item for item in items if keyword_match(q, item)]
    return {"documents": items}

@app.get("/api/documents/{document_id}")
def get_document(document_id: int):
    with connection() as db:
        row = db.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Document not found.")
        history = db.execute("SELECT event,details,created_at FROM processing_history WHERE document_id=? ORDER BY id", (document_id,)).fetchall()
    item = document_dict(row)
    item["history"] = [{"event": h["event"], "details": json.loads(h["details"] or "{}"), "created_at": h["created_at"]} for h in history]
    return item

@app.get("/api/documents/{document_id}/result")
def get_result(document_id: int):
    item = get_document(document_id)
    if item["status"] != "completed":
        raise HTTPException(409, f"Document is {item['status']}; result is not ready.")
    return {"document_id": document_id, "result": item["result"], "validation": item["validation"]}

@app.patch("/api/documents/{document_id}/corrections")
def correct_document(document_id: int, correction: Correction):
    with connection() as db:
        row = db.execute("SELECT result_json FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Document not found.")
        result = json.loads(row[0] or "{}")
        allowed = {"invoice_number", "invoice_date", "supplier_name", "customer_name", "subtotal", "tax", "total", "currency", "line_items"}
        unknown = set(correction.values) - allowed
        if unknown:
            raise HTTPException(400, f"Unsupported fields: {', '.join(sorted(unknown))}")
        result.update(correction.values)
        known_rows = db.execute("SELECT result_json FROM documents WHERE id<>? AND status='completed'", (document_id,)).fetchall()
        from .validator import validate_invoice
        validation = validate_invoice(result, [json.loads(r[0]) for r in known_rows if r[0]])
        db.execute("UPDATE documents SET result_json=?,validation_json=?,updated_at=? WHERE id=?", (json.dumps(result, ensure_ascii=False), json.dumps(validation, ensure_ascii=False), now(), document_id))
        add_history(db, document_id, "manual_correction", {"fields": list(correction.values)})
    return {"document_id": document_id, "result": result, "validation": validation}

@app.post("/api/documents/{document_id}/reprocess")
def reprocess_document(document_id: int, background_tasks: BackgroundTasks):
    with connection() as db:
        row = db.execute("SELECT id FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Document not found.")
        db.execute("UPDATE documents SET status='queued',error_message=NULL,updated_at=? WHERE id=?", (now(), document_id))
        add_history(db, document_id, "reprocess_requested")
    background_tasks.add_task(process_document, document_id)
    return {"document_id": document_id, "status": "queued"}

@app.get("/api/search")
def search_documents(q: str, mode: str = "keyword"):
    with connection() as db:
        rows = db.execute("SELECT * FROM documents WHERE status='completed' ORDER BY id DESC").fetchall()
        items = [document_dict(row) for row in rows]
    if mode == "semantic":
        ranked = semantic_rank(q, items)
        return {"query": q, "mode": mode, "documents": ranked[:50]}
    if mode != "keyword":
        raise HTTPException(400, "mode must be 'keyword' or 'semantic'.")
    return {"query": q, "mode": mode, "documents": [item for item in items if keyword_match(q, item)]}
