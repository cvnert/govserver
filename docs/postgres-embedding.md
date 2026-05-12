# PostgreSQL and Embedding Configuration

## PostgreSQL

The server Docker Compose stack now starts a PostgreSQL container and points the backend to it.

Required production environment variables:

```env
POSTGRES_DB=gov_rag
POSTGRES_USER=gov_rag
POSTGRES_PASSWORD=replace-with-a-strong-password
DATABASE_URL=postgresql+psycopg://gov_rag:replace-with-a-strong-password@postgres:5432/gov_rag
```

In `docker-compose.server.yml`, `DATABASE_URL` is generated from the `POSTGRES_*` values and overrides the value from `.env`.

SQLite data is not migrated automatically. After deploying PostgreSQL, run ingestion again.

## Embedding

The app supports two embedding modes:

- `hashing`: local fallback, no external API cost, lower quality.
- `ark`, `openai`, or `openai-compatible`: calls a `/embeddings` API.

For Volcano Ark-compatible embedding:

```env
EMBEDDING_PROVIDER=ark
EMBEDDING_MODEL=your-embedding-model-id
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_TIMEOUT_SECONDS=60
EMBEDDING_FALLBACK_TO_HASH=true
```

If `EMBEDDING_API_KEY` is empty, the backend reuses `OPENAI_API_KEY`.
If `EMBEDDING_BASE_URL` is empty, it reuses `OPENAI_BASE_URL`.

Example when LLM and embedding use the same Ark account:

```env
OPENAI_API_KEY=your-ark-api-key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
EMBEDDING_PROVIDER=ark
EMBEDDING_MODEL=your-embedding-model-id
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
```

After changing the embedding model, rebuild vectors:

```bash
curl -X POST http://101.35.131.94/api/ingest/revector
```

After switching from SQLite to PostgreSQL, run ingestion again:

```bash
curl -X POST http://101.35.131.94/api/ingest/run \
  -H "Content-Type: application/json" \
  -d '{"source_keys": null, "limit_per_channel": 20}'
```
