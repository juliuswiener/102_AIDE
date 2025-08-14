# Knowledge Base Generator — Requirements (v0.1)

**Goal**: Build a self-contained system that ingests mixed-format documents (PDF/HTML/Markdown), normalizes and indexes content, performs lightweight tagging, and exposes a REST API for search/browse. Python-only; deterministic; offline-capable.

---

## 1. Scope & Objectives

- **Primary objectives**
  - Recursively ingest documents from a directory.
  - Extract text + metadata, normalize to a canonical schema.
  - Compute tags/keywords and section-level snippets.
  - Provide full‑text search (BM25‑style or equivalent) with ranking & highlighting.
  - Expose a REST API for search, tags, docs, and admin ops.
  - Provide a CLI for ingest/reindex/stats.
- **Non‑goals (v0.1)**
  - No external web scraping or network retrieval.
  - No embeddings/vector search or LLM dependence (future extension).
  - No user auth/roles (single‑user admin only).
  - No distributed workers; single-node process model.

---

## 2. System Overview

- **Services**: `api` (FastAPI), `indexer` (library + CLI), `db` (SQLite default; Postgres optional under docker-compose)
- **Data flow**: Filesystem → Extractors → Normalizer → DB (documents, sections, tags) → Index (in-DB FTS5 or Whoosh) → API
- **Runtime profiles**:
  - **Offline**: local SQLite + Python stdlib + optional PyPDF2/BeautifulSoup.
  - **Containerized**: docker-compose with Postgres + pg\_trgm or SQLite/FTS5.

---

## 3. Input Formats & Extraction

- **Supported formats** (required):
  - **Markdown (.md)**: parse headings (#..####), code blocks, lists; keep structure.
  - **HTML (.html/.htm)**: strip boilerplate, extract `<title>`, headings, main body (BeautifulSoup), drop scripts/styles.
  - **PDF (.pdf)**: text extraction via PyPDF2 or pdfminer.six; page numbers recorded.
- **Optional formats (nice-to-have)**: `.txt` (trivial), `.rst`.
- **Character encoding**: assume UTF‑8; detect/normalize with `chardet` if needed.
- **Binary handling**: skip unsupported binaries; log warning.

---

## 4. Normalization & Segmentation

- **Canonical document schema**
  - `id` (UUID), `path`, `source_type` (pdf|html|md|txt), `title`, `author?`, `created_at_fs`, `modified_at_fs`, `ingested_at`, `checksum_sha256`, `bytes`, `language?`.
- **Sectioning rules**
  - **Markdown/HTML**: split by heading hierarchy; store `section_id`, `doc_id`, `level`, `heading_text`, `content_text`, `position`.
  - **PDF**: split by page; optionally heuristics for headings (bold/size not required in v0.1).
- **Normalization**
  - Strip excessive whitespace; preserve code fences as fenced blocks in `content_text`.
  - Store both **raw\_text** and **display\_text** where helpful (optional).

---

## 5. Tagging & Keywording

- **Method**: deterministic, local (no ML):
  - Compute TF‑IDF across sections; top‑N keywords per document (`N` configurable, default 10).
  - Add rule‑based tags: filetype, path-based tags (folder names), detected language (if implemented).
- **Storage**
  - `tags` table: `tag`, `doc_id`, `weight`.
  - Derived view: top tags with counts.

---

## 6. Indexing & Search

- **Index backend** (choose one for v0.1)
  - **SQLite FTS5** (preferred for simplicity) *or* Whoosh.
- **Indexed fields**: `title`, `section.heading_text`, `section.content_text`, `tags` (as boosted tokens).
- **Query**
  - Input: `q` (query string), optional filters: `source_type`, `tag`, `path_prefix`, `date_from`, `date_to`.
  - Ranking: BM25‑like; boost title > headings > body > tags.
  - **Highlighting**: return snippet with query terms emphasized; include `doc_id`, `section_id`, `score`.
- **Pagination**: `page`, `page_size` (default 10, max 100).

---

## 7. Data Model (relational)

- **documents** (`id` PK, `path` UNIQUE, `source_type`, `title`, `author`, `created_at_fs`, `modified_at_fs`, `ingested_at`, `checksum_sha256`, `bytes`, `language`)
- **sections** (`id` PK, `doc_id` FK, `level`, `heading_text`, `content_text`, `position`)
- **tags** (`doc_id` FK, `tag`, `weight`)
- **index\_meta** (kv store for index version, settings, stats)

---

## 8. REST API (FastAPI)

- `GET /health` → `{status:"ok"}`
- `GET /search?q=&page=&page_size=&source_type=&tag=&path_prefix=&date_from=&date_to=` → `{results:[{doc_id,section_id,title,heading,snippet,score,source_type,path}], total}`
- `GET /doc/{doc_id}` → document metadata + sections (paginated)
- `GET /tags` → `[ {tag, count} ]`
- `POST /admin/reindex` → triggers reindex (non-blocking)
- `POST /admin/ingest` body: `{path}` → enqueue ingest of given path
- Errors: JSON `{error, detail}` with appropriate HTTP codes.

---

## 9. CLI (click/argparse)

- `kb ingest <path>` → bulk ingest (recursive)
- `kb reindex` → rebuild search index
- `kb stats` → print counts (docs, sections, tags), index size, top tags
- `kb vacuum` → clean orphaned rows, compact DB (optional)

---

## 10. Configuration

- YAML or `.env` with defaults:
  - `DATA_DIR`, `DB_URL` (sqlite path by default), `INDEX_BACKEND`, `MAX_WORKERS` (ingest), `PDF_MAX_PAGES`, `KEYWORDS_TOP_N`, `SEARCH_PAGE_SIZE_MAX`.
- All config echoable via `kb stats`.

---

## 11. Performance Targets (v0.1, on dev laptop)

- Ingest throughput: ≥ **50 docs/min** for small Markdown/HTML; ≥ **5 pages/sec** for PDFs.
- Search latency (P95): ≤ **200 ms** for simple queries on 10k sections (warm cache).
- Index build time: ≤ **5 min** for 10k sections.

---

## 12. Reliability & Error Handling

- **Idempotent ingest**: re‑running on same path updates modified files (checksum change) and skips identical.
- **Atomic index updates**: build new index, then swap.
- **Failure policy**: per-file failures logged; pipeline continues; error table optional (`ingest_errors`).
- **Validation**: reject files > configured size; protect against zip‑bomb PDFs (page cap).

---

## 13. Logging & Observability

- Structured logs (JSON) with `component`, `event`, timings.
- Metrics: `ingest_docs_total`, `ingest_failures_total`, `index_size`, `search_qps`, `search_p95_ms` (export via `/metrics` optional).
- Tracing (optional): simple span timings around extract/normalize/index.

---

## 14. Security & Privacy

- Local filesystem only; no network fetch.
- No PII detection required in v0.1; treat all data as internal.
- Serve API on localhost by default; CORS disabled unless configured.

---

## 15. Testing & Acceptance Criteria

- **Unit tests**: extractors, normalizer, tagger, indexer.
- **Integration tests**: end‑to‑end ingest of mixed fixtures; search correctness on golden queries.
- **API tests**: OpenAPI schema validation; pagination; error codes.
- **CLI tests**: ingest/reindex/stats flows on temp dirs.
- **Determinism**: same corpus → identical index stats & top‑N keywords (given fixed seed).
- **Completion criterion**: All required tests pass within configured time cap (to be set by harness).

---

## 16. Directory Layout (reference)

```
kb/
  api/
    main.py
    routers/
  core/
    config.py
    logging.py
  extract/
    pdf.py
    html.py
    markdown.py
  normalize/
    segment.py
  index/
    fts.py
  store/
    db.py
    models.py
  cli.py
  tests/
    unit/
    integration/
  fixtures/
    corpus_small/
    corpus_medium/
  pyproject.toml
  README.md
```

---

## 17. Milestones

- **M1 (Skeleton)**: DB schema, CLI scaffold, FastAPI skeleton, health endpoint.
- **M2 (Extraction)**: MD/HTML/PDF extractors + basic normalization; unit tests.
- **M3 (Index/Search)**: FTS5 index, search API, highlighting.
- **M4 (Tagging)**: TF‑IDF tags + `/tags` endpoint, stats.
- **M5 (Stability)**: Idempotent ingest, atomic reindex, metrics/logging.
- **M6 (Perf pass)**: Meet v0.1 performance targets on medium corpus.

---

## 18. Future Extensions (out of v0.1)

- Embedding/Vectored search and hybrid ranking.
- AuthN/Z, multi-tenant indexes.
- Distributed ingestion workers.
- Doc render previews and diffing.
- Language detection + per-language analyzers.

