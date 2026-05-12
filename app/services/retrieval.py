from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Document, DocumentChunk, DocumentChunkVector
from app.schemas import SearchResult
from app.services.vectorizer import cosine_similarity, expand_semantic_queries, loads_vector, text_to_vector


@dataclass
class SearchCandidate:
    document: Document
    snippet: str
    lexical_score: float = 0.0
    vector_score: float = 0.0

    @property
    def total_score(self) -> float:
        return self.lexical_score + self.vector_score


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, limit: int = 20, queries: list[str] | None = None) -> list[SearchResult]:
        normalized_queries = self._normalized_queries(query, queries)
        candidates = self._lexical_candidates(query, normalized_queries, limit)
        self._merge_vector_candidates(candidates, query, limit)

        ranked = sorted(
            candidates.values(),
            key=lambda item: (
                item.total_score,
                item.document.publish_time or "",
                item.document.updated_at.isoformat() if item.document.updated_at else "",
            ),
            reverse=True,
        )[:limit]

        return [
            SearchResult(
                id=item.document.id,
                title=item.document.title,
                url=item.document.url,
                publish_time=item.document.publish_time,
                issuer=item.document.issuer,
                channel=item.document.channel,
                snippet=item.snippet,
            )
            for item in ranked
        ]

    def get_document(self, document_id: int) -> Document | None:
        return (
            self.db.query(Document)
            .options(joinedload(Document.chunks))
            .filter(Document.id == document_id)
            .first()
        )

    def _lexical_candidates(
        self, query: str, normalized_queries: list[str], limit: int
    ) -> dict[int, SearchCandidate]:
        results: dict[int, SearchCandidate] = {}
        chunk_rows = self._run_chunk_query(normalized_queries, max(limit * 4, 16))

        for row in chunk_rows:
            score = self._match_score(row.document, row.content, normalized_queries)
            self._upsert_candidate(
                results,
                SearchCandidate(
                    document=row.document,
                    snippet=self._snippet(row.content or row.document.content_clean or row.document.summary, query),
                    lexical_score=score,
                ),
            )

        document_rows = self._run_document_query(normalized_queries, max(limit * 3, 12))
        for row in document_rows:
            score = self._match_score(row, row.content_clean or row.summary, normalized_queries)
            self._upsert_candidate(
                results,
                SearchCandidate(
                    document=row,
                    snippet=self._snippet(row.content_clean or row.summary, query),
                    lexical_score=score,
                ),
            )

        return results

    def _merge_vector_candidates(self, results: dict[int, SearchCandidate], query: str, limit: int) -> None:
        query_vector = text_to_vector(query)
        if not any(query_vector):
            return

        chunk_vectors = (
            self.db.query(DocumentChunkVector)
            .options(joinedload(DocumentChunkVector.chunk).joinedload(DocumentChunk.document))
            .all()
        )

        ranked_vectors: list[tuple[float, DocumentChunk]] = []
        for item in chunk_vectors:
            if not item.chunk or not item.chunk.document:
                continue
            score = cosine_similarity(query_vector, loads_vector(item.vector_json))
            if score <= 0:
                continue
            ranked_vectors.append((score, item.chunk))

        ranked_vectors.sort(key=lambda item: item[0], reverse=True)
        for score, chunk in ranked_vectors[: max(limit * 5, 20)]:
            document = chunk.document
            vector_score = score * 18
            self._upsert_candidate(
                results,
                SearchCandidate(
                    document=document,
                    snippet=self._snippet(chunk.content or document.content_clean or document.summary, query),
                    vector_score=vector_score,
                ),
            )

    def _upsert_candidate(self, results: dict[int, SearchCandidate], incoming: SearchCandidate) -> None:
        existing = results.get(incoming.document.id)
        if not existing:
            results[incoming.document.id] = incoming
            return

        existing.lexical_score = max(existing.lexical_score, incoming.lexical_score)
        existing.vector_score = max(existing.vector_score, incoming.vector_score)
        if incoming.total_score > existing.total_score and incoming.snippet:
            existing.snippet = incoming.snippet

    def _normalized_queries(self, query: str, queries: list[str] | None) -> list[str]:
        normalized = [item.strip() for item in (queries or [query]) if item and item.strip()]
        expanded = []
        for item in normalized:
            for variant in expand_semantic_queries(item):
                if variant not in expanded:
                    expanded.append(variant)
        return expanded

    def _run_chunk_query(self, terms: list[str], limit: int) -> list[DocumentChunk]:
        valid_terms = self._expand_terms(terms)
        if not valid_terms:
            return []

        predicates = [DocumentChunk.content.ilike(f"%{term}%") for term in valid_terms]
        return (
            self.db.query(DocumentChunk)
            .options(joinedload(DocumentChunk.document))
            .join(DocumentChunk.document)
            .filter(or_(*predicates))
            .order_by(Document.publish_time.desc(), Document.updated_at.desc(), DocumentChunk.chunk_index.asc())
            .limit(limit)
            .all()
        )

    def _run_document_query(self, terms: list[str], limit: int) -> list[Document]:
        valid_terms = self._expand_terms(terms)
        if not valid_terms:
            return []

        predicates = []
        for term in valid_terms:
            keyword = f"%{term}%"
            predicates.extend(
                [
                    Document.title.ilike(keyword),
                    Document.content_clean.ilike(keyword),
                    Document.summary.ilike(keyword),
                ]
            )

        return (
            self.db.query(Document)
            .filter(or_(*predicates))
            .order_by(Document.publish_time.desc(), Document.updated_at.desc())
            .limit(limit)
            .all()
        )

    def _expand_terms(self, terms: list[str]) -> list[str]:
        expanded: list[str] = []
        for term in terms:
            normalized = term.strip()
            if normalized and normalized not in expanded:
                expanded.append(normalized)
            for token in self._keyword_terms(normalized):
                if token not in expanded:
                    expanded.append(token)
        return expanded[:40]

    @staticmethod
    def _snippet(text: str, query: str, size: int = 180) -> str:
        if not text:
            return ""
        pos = text.lower().find(query.lower())
        if pos == -1:
            return text[:size]
        start = max(0, pos - 40)
        end = min(len(text), pos + size)
        return text[start:end]

    @staticmethod
    def _keyword_terms(query: str) -> list[str]:
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", "", query)
        chunks = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", cleaned)
        terms: list[str] = []

        for chunk in chunks:
            if len(chunk) <= 4:
                terms.append(chunk)
                continue

            for size in (4, 3, 2):
                for index in range(0, len(chunk) - size + 1):
                    part = chunk[index : index + size]
                    if part not in terms:
                        terms.append(part)

        return terms[:24]

    def _match_score(self, row: Document, chunk_text: str, queries: list[str]) -> float:
        haystack = " ".join([row.title or "", row.summary or "", row.content_clean or "", chunk_text or ""])
        score = 0.0

        for query in queries:
            if query and query in haystack:
                score += 10

            for term in self._keyword_terms(query):
                if term and term in haystack:
                    score += max(1, len(term))

        title = row.title or ""
        for query in queries:
            if query and query in title:
                score += 12

            for term in self._keyword_terms(query):
                if term and term in title:
                    score += max(2, len(term) * 2)

        return score
