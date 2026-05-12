from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AskRequest, AskResponse, IngestRequest, IngestResponse, PolicyExtraction, SearchResult, SourceCreateRequest, SourceDiscoverRequest, SourceDiscoverResponse, SourceView
from app.services.extractor import PolicyExtractionService
from app.services.ingestion import IngestionService
from app.services.qa import QAService
from app.services.registry import source_registry
from app.services.retrieval import RetrievalService
from app.services.source_admin import source_admin_service
from app.services.source_discovery import source_discovery_service

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/sources", response_model=list[SourceView])
def list_sources():
    return source_registry.list_sources()


@router.post("/sources/reload", response_model=list[SourceView])
def reload_sources():
    source_registry.load(force=True)
    return source_registry.list_sources()


@router.post("/sources", response_model=list[SourceView])
def create_source(request: SourceCreateRequest):
    try:
        return source_admin_service.create_source(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sources/discover", response_model=SourceDiscoverResponse)
def discover_source(request: SourceDiscoverRequest):
    try:
        return source_discovery_service.discover(request.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/documents/search", response_model=list[SearchResult])
def search_documents(q: str, db: Session = Depends(get_db)):
    return RetrievalService(db).search(q)


@router.get("/documents/{document_id}/extract", response_model=PolicyExtraction)
async def extract_document(document_id: int, db: Session = Depends(get_db)):
    return await PolicyExtractionService(db).extract_document(document_id)


@router.post("/ingest/run", response_model=IngestResponse)
def run_ingestion(request: IngestRequest, db: Session = Depends(get_db)):
    service = IngestionService(db)
    return service.run(source_keys=request.source_keys, limit_per_channel=request.limit_per_channel)


@router.post("/ingest/rechunk")
def rebuild_chunks(db: Session = Depends(get_db)):
    return IngestionService(db).rebuild_chunks()


@router.post("/ingest/revector")
def rebuild_vectors(db: Session = Depends(get_db)):
    return IngestionService(db).rebuild_vectors()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    return QAService(db).answer(request.question, top_k=request.top_k, history=request.history)


@router.post("/ask/stream")
async def ask_stream(request: AskRequest, db: Session = Depends(get_db)):
    service = QAService(db)
    return StreamingResponse(
        service.stream_answer(request.question, top_k=request.top_k, history=request.history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
