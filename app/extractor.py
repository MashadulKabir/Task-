import json
import re
from datetime import datetime
import httpx
from .config import USE_LOCAL_LLM, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY

EMPTY_RESULT = {
    "invoice_number": None, "invoice_date": None, "supplier_name": None,
    "customer_name": None, "subtotal": None, "tax": None, "total": None,
    "currency": None, "line_items": [], "confidence_notes": []
}

def _money(value):
    if value is None:
        return None
    cleaned = str(value).replace(",", "").replace("৳", "").replace("$", "").replace("€", "").strip()
    match = re.search(r"-?\d+(?:\.\d{1,4})?", cleaned)
    try:
        return round(float(match.group()), 4) if match else None
    except ValueError:
        return None

def _first(patterns, text, flags=re.I | re.M):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip(" :\t")
    return None

def heuristic_extract(text: str) -> dict:
    result = dict(EMPTY_RESULT)
    result["line_items"] = []
    result["confidence_notes"] = ["Heuristic extraction was used; review the extracted values before relying on them."]
    result["invoice_number"] = _first([r"(?:invoice\s*(?:no|number|#)|bill\s*no)\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]+)"], text)
    result["invoice_date"] = _first([r"(?:invoice\s*date|date)\s*[:#-]?\s*(\d{1,4}[/-]\d{1,2}[/-]\d{1,4})"], text)
    result["supplier_name"] = _first([r"(?:supplier|vendor|seller)\s*(?:name)?\s*[:#-]?\s*([^\n]+)"], text)
    result["customer_name"] = _first([r"(?:customer|bill\s*to|buyer)\s*(?:name)?\s*[:#-]?\s*([^\n]+)"], text)
    for field, labels in {
        "subtotal": [r"(?:sub\s*total|subtotal)\s*[:=]?\s*([\$€৳]?[\d,]+(?:\.\d{1,2})?)"],
        "tax": [r"(?:vat|tax)\s*[:=]?\s*([\$€৳]?[\d,]+(?:\.\d{1,2})?)"],
        "total": [r"\b(?:grand\s*total|total\s*due|amount\s*due|total)\b\s*[:=]?\s*([\$€৳]?[\d,]+(?:\.\d{1,2})?)"]
    }.items():
        raw = _first(labels, text)
        result[field] = _money(raw)
    upper = text.upper()
    for token, currency in [("BDT", "BDT"), ("৳", "BDT"), ("USD", "USD"), ("$", "USD"), ("EUR", "EUR"), ("€", "EUR"), ("GBP", "GBP")]:
        if token in upper or token in text:
            result["currency"] = currency
            break
    return result

def llm_extract(text: str) -> dict:
    prompt = f'''Extract invoice information from the text below. Return ONLY valid JSON with these keys: invoice_number, invoice_date, supplier_name, customer_name, subtotal, tax, total, currency, line_items, confidence_notes. Use null for missing or uncertain scalar values. Never guess. line_items must be an array of objects with description, quantity, unit_price, amount. Numeric values must be numbers.\n\nDOCUMENT TEXT:\n{text[:18000]}'''
    response = httpx.post(f"{LLM_BASE_URL.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                          json={"model": LLM_MODEL, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}, timeout=90)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    parsed = json.loads(content)
    return normalize_result(parsed)

def normalize_result(data: dict) -> dict:
    result = dict(EMPTY_RESULT)
    for key in result:
        if key in data:
            result[key] = data[key]
    for key in ("subtotal", "tax", "total"):
        value = result[key]
        if value is not None:
            try:
                result[key] = float(value)
            except (ValueError, TypeError):
                result[key] = None
    if not isinstance(result["line_items"], list):
        result["line_items"] = []
    if not isinstance(result["confidence_notes"], list):
        result["confidence_notes"] = [str(result["confidence_notes"])]
    return result

def extract_invoice(text: str) -> dict:
    if USE_LOCAL_LLM:
        try:
            return llm_extract(text)
        except Exception as exc:
            fallback = heuristic_extract(text)
            fallback["confidence_notes"].append(f"Local LLM was unavailable; heuristic fallback used ({type(exc).__name__}).")
            return fallback
    return heuristic_extract(text)
