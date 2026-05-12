from collections import defaultdict
from urllib.parse import urljoin

from sqlalchemy.orm import Session

from app.crawlers.registry import crawler_registry
from app.models import Document, DocumentChunk, DocumentChunkVector, Source
from app.services.chunking import split_document_chunks
from app.services.embedding import get_embedding_service
from app.services.registry import source_registry
from app.services.vectorizer import dumps_vector
from app.utils import sha256_text


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding = get_embedding_service()

    def run(self, source_keys: list[str] | None = None, limit_per_channel: int = 10) -> dict:
        results: dict[str, dict] = defaultdict(lambda: {"fetched": 0, "stored": 0})
        configs = source_registry.get_many(source_keys)

        for config in configs:
            source = self._ensure_source(config)
            crawler = crawler_registry.create(config.crawler, config)

            for channel in config.channels:
                items = crawler.fetch_channel(channel, limit=limit_per_channel)
                results[config.key]["fetched"] += len(items)

                for item in items:
                    item["url"] = urljoin(config.base_url, item["url"])
                    if self._upsert_document(source.id, item):
                        results[config.key]["stored"] += 1

        self.db.commit()
        return {"sources": results}

    def rebuild_chunks(self) -> dict:
        total = 0
        for doc in self.db.query(Document).all():
            self._refresh_chunks(doc, (doc.content_clean or "").strip())
            total += 1
        self.db.commit()
        return {"documents": total}

    def rebuild_vectors(self) -> dict:
        total = 0
        for doc in self.db.query(Document).all():
            if not doc.chunks:
                self._refresh_chunks(doc, (doc.content_clean or "").strip())
            else:
                vectors = self.embedding.embed_texts([chunk.content or "" for chunk in doc.chunks])
                for chunk, vector in zip(doc.chunks, vectors, strict=True):
                    if chunk.vector:
                        chunk.vector.model_name = self.embedding.model_name
                        chunk.vector.dimensions = len(vector)
                        chunk.vector.vector_json = dumps_vector(vector)
                    else:
                        chunk.vector = DocumentChunkVector(
                            model_name=self.embedding.model_name,
                            dimensions=len(vector),
                            vector_json=dumps_vector(vector),
                        )
            total += 1
        self.db.commit()
        return {"documents": total}

    def _ensure_source(self, config) -> Source:
        source = self.db.query(Source).filter(Source.key == config.key).first()
        if source:
            source.name = config.name
            source.base_url = config.base_url
            source.region = config.region
            source.enabled = config.enabled
            source.config_path = config.file_path
            return source

        source = Source(
            key=config.key,
            name=config.name,
            base_url=config.base_url,
            region=config.region,
            enabled=config.enabled,
            config_path=config.file_path,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def _upsert_document(self, source_id: int, item: dict) -> bool:
        content_clean = item.get("content_clean", "").strip()
        content_hash = sha256_text(f"{item.get('title', '')}\n{content_clean}")

        doc = self.db.query(Document).filter(Document.url == item["url"]).first()
        if not doc:
            doc = Document(source_id=source_id, url=item["url"], title=item.get("title", ""))
            self.db.add(doc)

        changed = doc.content_hash != content_hash
        doc.channel = item.get("channel", "")
        doc.issuer = item.get("issuer", "")
        doc.publish_time = item.get("publish_time", "")
        doc.summary = item.get("summary", "")
        doc.content_raw = item.get("content_raw", "")
        doc.content_clean = content_clean
        doc.content_hash = content_hash
        if changed or not doc.chunks:
            self._refresh_chunks(doc, content_clean)
        return changed

    def _refresh_chunks(self, doc: Document, content_clean: str) -> None:
        chunks = split_document_chunks(content_clean)
        vectors = self.embedding.embed_texts(chunks)
        doc.chunks.clear()

        for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            doc.chunks.append(
                DocumentChunk(
                    chunk_index=index,
                    content=chunk,
                    content_hash=sha256_text(chunk),
                    vector=DocumentChunkVector(
                        model_name=self.embedding.model_name,
                        dimensions=len(vector),
                        vector_json=dumps_vector(vector),
                    ),
                )
            )
