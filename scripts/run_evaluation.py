import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.extractor import heuristic_extract

source = ROOT / 'evaluation' / 'labeled_invoices.json'
cases = json.loads(source.read_text(encoding='utf-8'))
fields = ['invoice_number','invoice_date','supplier_name','customer_name','subtotal','tax','total','currency']
correct = total = 0
rows = []
start_all = time.perf_counter()
for case in cases:
    start = time.perf_counter()
    actual = heuristic_extract(case['text'])
    elapsed_ms = (time.perf_counter() - start) * 1000
    case_correct = sum(actual.get(k) == case['expected'].get(k) for k in fields)
    correct += case_correct
    total += len(fields)
    rows.append({'id': case['id'], 'correct_fields': case_correct, 'fields': len(fields), 'elapsed_ms': round(elapsed_ms, 3), 'actual': actual})
wall_ms = (time.perf_counter() - start_all) * 1000
accuracy = correct / total if total else 0
report = {
  'dataset_type': 'small synthetic smoke-test dataset; not representative of real invoices',
  'documents': len(cases), 'field_accuracy': round(accuracy, 4),
  'correct_fields': correct, 'total_fields': total,
  'document_processing_success_rate': 1.0 if cases else 0.0,
  'document_failure_rate': 0.0 if cases else 1.0,
  'total_wall_time_ms': round(wall_ms, 3),
  'average_extraction_time_ms': round(sum(r['elapsed_ms'] for r in rows)/len(rows), 3) if rows else None,
  'per_document': rows
}
(ROOT/'evaluation'/'results.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
md = f"""# Evaluation Report\n\n- Dataset: {report['dataset_type']}\n- Documents processed: {report['documents']}\n- Exact-match field accuracy: {accuracy:.1%} ({correct}/{total})\n- Document processing success rate: {report['document_processing_success_rate']:.1%}\n- Document failure rate: {report['document_failure_rate']:.1%}\n- Total measured wall time: {wall_ms:.3f} ms\n- Average extraction time per document: {report['average_extraction_time_ms']} ms\n\n## Limitations\nThis measures only the deterministic text heuristic against three synthetic text snippets. It does not measure OCR accuracy, varied layouts, real supplier invoices, LLM extraction, spreadsheet parsing, API throughput, or production reliability. Do not represent this score as real-world accuracy. Run a larger human-labelled benchmark before making performance claims.\n"""
(ROOT/'evaluation'/'report.md').write_text(md, encoding='utf-8')
print(md)
