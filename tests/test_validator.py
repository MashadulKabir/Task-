from app.validator import validate_invoice

def test_amount_mismatch_is_flagged():
    result = validate_invoice({"invoice_number":"A1", "invoice_date":"2026-01-01", "supplier_name":"Acme", "subtotal":100, "tax":10, "total":120, "line_items":[]})
    assert any(error["code"] == "amount_mismatch" for error in result["errors"])
    assert result["requires_manual_review"]

def test_missing_fields_are_reported():
    result = validate_invoice({"line_items": []})
    fields = {error["field"] for error in result["errors"]}
    assert {"invoice_number", "invoice_date", "supplier_name", "total"}.issubset(fields)

def test_duplicate_invoice_is_reported():
    invoice = {"invoice_number":"INV-1", "supplier_name":"Acme", "invoice_date":"2026-01-01", "total":10}
    result = validate_invoice(invoice, [invoice])
    assert any(error["code"] == "duplicate_invoice" for error in result["errors"])
