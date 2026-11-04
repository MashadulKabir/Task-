from app.extractor import heuristic_extract

def test_extracts_basic_invoice_fields():
    text = """INVOICE\nInvoice No: INV-1001\nInvoice Date: 2026-10-20\nSupplier: ABC Limited\nCustomer: XYZ Company\nSubtotal: 1000.00\nVAT: 150.00\nGrand Total: 1150.00 BDT"""
    result = heuristic_extract(text)
    assert result["invoice_number"] == "INV-1001"
    assert result["supplier_name"] == "ABC Limited"
    assert result["subtotal"] == 1000.0
    assert result["total"] == 1150.0
    assert result["currency"] == "BDT"
