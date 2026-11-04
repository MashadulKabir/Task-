import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def keyword_match(query: str, document: dict) -> bool:
    haystack = " ".join(str(document.get(k) or "") for k in ("filename", "extracted_text", "result"))
    terms = [term for term in re.findall(r"[\w-]+", query.lower()) if term]
    return not terms or all(term in haystack.lower() for term in terms)

def semantic_rank(query: str, documents: list[dict]) -> list[dict]:
    # Lightweight local semantic-like retrieval using TF-IDF; replace with embeddings for production.
    texts = [" ".join([str(d.get("filename") or ""), str(d.get("extracted_text") or ""), str(d.get("result") or "")]) for d in documents]
    if not texts or not query.strip():
        return documents
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(texts + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        return [doc for _, doc in sorted(zip(scores, documents), key=lambda pair: pair[0], reverse=True) if _ > 0]
    except ValueError:
        return []
