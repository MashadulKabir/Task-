import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API = 'http://127.0.0.1:8000';
function App() {
  const [documents, setDocuments] = useState([]);
  const [selected, setSelected] = useState(null);
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('keyword');
  const [message, setMessage] = useState('');
  async function load() {
    try { const response = await fetch(`${API}/api/documents`); const data = await response.json(); setDocuments(data.documents || []); }
    catch { setMessage('Could not connect to the API. Start the FastAPI server first.'); }
  }
  useEffect(() => { load(); const timer = setInterval(load, 3000); return () => clearInterval(timer); }, []);
  async function upload(event) {
    const files = [...event.target.files]; if (!files.length) return;
    const form = new FormData(); files.forEach(file => form.append('files', file));
    setMessage('Uploading documents…');
    try { const response = await fetch(`${API}/api/documents/upload`, { method: 'POST', body: form }); const data = await response.json(); setMessage(response.ok ? `${data.uploaded.length} file(s) added to the queue.` : data.detail || 'Upload failed.'); load(); }
    catch { setMessage('Upload failed. Check that the API is running.'); }
    event.target.value = '';
  }
  async function search(event) {
    event.preventDefault(); if (!query.trim()) return load();
    const response = await fetch(`${API}/api/search?q=${encodeURIComponent(query)}&mode=${mode}`); const data = await response.json(); setDocuments(data.documents || []);
  }
  async function openDocument(id) { const response = await fetch(`${API}/api/documents/${id}`); setSelected(await response.json()); }
  async function reprocess(id) { await fetch(`${API}/api/documents/${id}/reprocess`, { method: 'POST' }); setMessage('Reprocessing queued.'); load(); }
  async function saveCorrection(event) {
    event.preventDefault();
    const fields = ['invoice_number','invoice_date','supplier_name','customer_name','subtotal','tax','total','currency'];
    const values = {};
    fields.forEach(key => { const value = event.currentTarget.elements[key].value; if (value !== '') values[key] = ['subtotal','tax','total'].includes(key) ? Number(value) : value; });
    const response = await fetch(`${API}/api/documents/${selected.id}/corrections`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({values}) });
    const data = await response.json(); if (response.ok) { setSelected({...selected, result:data.result, validation:data.validation}); setMessage('Corrections saved.'); load(); } else setMessage(data.detail || 'Could not save corrections.');
  }
  const result = selected?.result || {};
  return <div className="shell"><header><div><span className="eyebrow">DOCUMENT INTELLIGENCE</span><h1>Invoice<span>AI</span></h1><p>Upload, extract, validate and review invoices.</p></div><label className="upload">＋ Upload documents<input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,.xlsx,.xls,.csv" onChange={upload}/></label></header>
    {message && <div className="notice">{message}</div>}
    <section className="stats"><div><small>Documents</small><strong>{documents.length}</strong></div><div><small>Completed</small><strong>{documents.filter(d=>d.status==='completed').length}</strong></div><div><small>In progress</small><strong>{documents.filter(d=>['queued','processing'].includes(d.status)).length}</strong></div><div><small>Failed</small><strong>{documents.filter(d=>d.status==='failed').length}</strong></div></section>
    <main><section className="panel"><div className="panel-head"><div><h2>Documents</h2><p>Recently uploaded files and processing status</p></div><form onSubmit={search} className="search"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search invoices…"/><select value={mode} onChange={e=>setMode(e.target.value)}><option value="keyword">Keyword</option><option value="semantic">Semantic</option></select><button>Search</button></form></div>
      <div className="table-wrap"><table><thead><tr><th>File</th><th>Type</th><th>Status</th><th>Updated</th><th></th></tr></thead><tbody>{documents.map(doc=><tr key={doc.id}><td><button className="file-link" onClick={()=>openDocument(doc.id)}>{doc.filename}</button><small>#{doc.id}</small></td><td>{doc.file_type?.toUpperCase()}</td><td><span className={`status ${doc.status}`}>{doc.status}</span></td><td>{new Date(doc.updated_at).toLocaleString()}</td><td>{doc.status==='failed' && <button className="quiet" onClick={()=>reprocess(doc.id)}>Retry</button>}</td></tr>)}</tbody></table>{!documents.length && <div className="empty">No documents yet. Upload one or more invoice files to get started.</div>}</div>
    </section>
    {selected && <section className="panel detail"><div className="panel-head"><div><h2>{selected.filename}</h2><p>Document #{selected.id} · {selected.status}</p></div><button className="quiet" onClick={()=>setSelected(null)}>Close</button></div>
      {selected.status==='completed' ? <><div className="validation"><strong>{selected.validation?.requires_manual_review ? 'Manual review recommended' : 'Validation passed'}</strong><span>{selected.validation?.errors?.length || 0} errors · {selected.validation?.warnings?.length || 0} warnings</span></div>
        {[...(selected.validation?.errors||[]),...(selected.validation?.warnings||[])].map((issue,i)=><p className="issue" key={i}><b>{issue.field}</b> — {issue.message}</p>)}
        <form className="edit-grid" onSubmit={saveCorrection}>{['invoice_number','invoice_date','supplier_name','customer_name','subtotal','tax','total','currency'].map(field=><label key={field}>{field.replaceAll('_',' ')}<input name={field} defaultValue={result[field] ?? ''}/></label>)}<button className="primary">Save corrections</button></form>
        <h3>Line items</h3><pre>{JSON.stringify(result.line_items || [], null, 2)}</pre><h3>Extracted text</h3><pre className="text-preview">{selected.extracted_text || 'No text extracted.'}</pre>
      </> : <p>Processing status: {selected.status}. Refreshing automatically.</p>}
    </section>}
    </main><footer>InvoiceAI · Local development MVP</footer></div>;
}

createRoot(document.getElementById('root')).render(<App/>);
