import json
from pathlib import Path
from .database import connection, add_history, now
from .document_reader import extract_document_text
from .extractor import extract_invoice
from .validator import validate_invoice

def process_document(document_id: int):
    with connection() as db:
        row = db.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return
        db.execute("UPDATE documents SET status='processing',updated_at=? WHERE id=?", (now(), document_id))
        add_history(db, document_id, "processing_started")
        path = Path(row["stored_name"])
    try:
        text = extract_document_text(path)
        result = extract_invoice(text)
        with connection() as db:
            known_rows = db.execute("SELECT result_json FROM documents WHERE id<>? AND status='completed'", (document_id,)).fetchall()
            known = [json.loads(r[0]) for r in known_rows if r[0]]
            validation = validate_invoice(result, known)
            db.execute("UPDATE documents SET status='completed',extracted_text=?,result_json=?,validation_json=?,error_message=NULL,updated_at=? WHERE id=?",
                       (text, json.dumps(result, ensure_ascii=False), json.dumps(validation, ensure_ascii=False), now(), document_id))
            add_history(db, document_id, "processing_completed", {"validation": validation})
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE documents SET status='failed',error_message=?,updated_at=? WHERE id=?", (str(exc), now(), document_id))
            add_history(db, document_id, "processing_failed", {"error": str(exc)})
