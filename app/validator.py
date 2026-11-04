from decimal import Decimal, InvalidOperation

def validate_invoice(invoice: dict, known_invoices=None) -> dict:
    errors, warnings = [], []
    required = ["invoice_number", "invoice_date", "supplier_name", "total"]
    for field in required:
        if invoice.get(field) in (None, ""):
            errors.append({"field": field, "code": "missing_required_field", "message": f"{field.replace('_', ' ').title()} is missing."})
    for field in ("subtotal", "tax", "total"):
        value = invoice.get(field)
        if value is not None:
            try:
                if Decimal(str(value)) < 0:
                    errors.append({"field": field, "code": "negative_amount", "message": f"{field.title()} cannot be negative."})
            except InvalidOperation:
                errors.append({"field": field, "code": "invalid_number", "message": f"{field.title()} is not a valid number."})
    subtotal, tax, total = (invoice.get(k) for k in ("subtotal", "tax", "total"))
    if all(v is not None for v in (subtotal, tax, total)):
        if abs(float(subtotal) + float(tax) - float(total)) > 0.02:
            errors.append({"field": "total", "code": "amount_mismatch", "message": "Subtotal plus tax does not equal total."})
    items = invoice.get("line_items") or []
    item_amounts = []
    for index, item in enumerate(items):
        try:
            amount = item.get("amount")
            if amount is None and item.get("quantity") is not None and item.get("unit_price") is not None:
                amount = float(item["quantity"]) * float(item["unit_price"])
            if amount is not None:
                item_amounts.append(float(amount))
        except (ValueError, TypeError):
            errors.append({"field": f"line_items[{index}]", "code": "invalid_line_item", "message": "Line item contains an invalid numeric value."})
    if subtotal is not None and item_amounts and abs(sum(item_amounts) - float(subtotal)) > 0.02:
        warnings.append({"field": "line_items", "code": "line_item_sum_mismatch", "message": "Line item amounts do not add up to subtotal."})
    if known_invoices and invoice.get("invoice_number") and invoice.get("supplier_name"):
        for known in known_invoices:
            if (known.get("invoice_number", "").casefold() == str(invoice["invoice_number"]).casefold()
                and known.get("supplier_name", "").casefold() == str(invoice["supplier_name"]).casefold()):
                errors.append({"field": "invoice_number", "code": "duplicate_invoice", "message": "An invoice with the same number and supplier already exists."})
                break
    return {"valid": not errors, "requires_manual_review": bool(errors or warnings or invoice.get("confidence_notes")),
            "errors": errors, "warnings": warnings}
