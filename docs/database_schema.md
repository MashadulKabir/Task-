# Database Schema

```mermaid
erDiagram
  DOCUMENTS ||--o{ PROCESSING_HISTORY : has
  DOCUMENTS {
    int id PK
    string filename
    string stored_name
    string file_type
    int file_size
    string sha256
    string status
    text extracted_text
    json result_json
    json validation_json
    text error_message
    datetime created_at
    datetime updated_at
  }
  PROCESSING_HISTORY {
    int id PK
    int document_id FK
    string event
    json details
    datetime created_at
  }
```

SQLite stores JSON payloads as serialized JSON text. `documents.sha256` is indexed for duplicate-file detection; `documents.status` is indexed for job filtering. `processing_history.document_id` references `documents.id` with cascading deletion.

## Invoice JSON shape
```json
{
  "invoice_number": null,
  "invoice_date": null,
  "supplier_name": null,
  "customer_name": null,
  "subtotal": null,
  "tax": null,
  "total": null,
  "currency": null,
  "line_items": [],
  "confidence_notes": []
}
```
