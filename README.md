# Agreement Intelligence

Extracts agreement details (parties, dates, terms, tables, signature status) from PDF contracts, shows them on a detail page, and answers questions over clauses with citations. The plan runs about 16 weeks part-time in nine phases (0–8) and is also a hands-on Databricks learning project.

## Architecture

Databricks handles bulk and backfill ingestion; FastAPI handles live uploads and queries. Both paths import the same `contract_core` package, so extraction behaves the same on each, and both write to the same stores. Postgres is the source of truth. Qdrant is an index that can be rebuilt from Postgres at any time.

| Component | Owns |
|---|---|
| `contract_core/` | Pydantic schema, prompts and validation, shared by both paths |
| Databricks (`databricks/`) | Batch ingestion (bronze → silver → gold), backfills, analytics, MLflow accuracy tracking |
| FastAPI (`api/`) | Live uploads, REST API, RAG chat graph, auth |
| Worker (`worker/`) | arq queue consumer that runs the LangGraph ingestion graph |
| Next.js (`web/`) | Detail page, review queue, chat |
| Postgres | System of record: agreements, parties, clauses, tables, signatures, extraction runs |
| Qdrant | Dense + sparse (hybrid) search over clause chunks |

Practice data: the public [CUAD](https://www.atticusprojectai.org/cuad) dataset (~500 labelled commercial contracts), which is also the evaluation golden set.

## Repository layout

```
contract_core/              shared package, installed with pip install -e
  src/contract_core/
    schema.py               Agreement schema; every field carries quote + page evidence
    validation.py           deterministic checks run after extraction
    versions.py             SCHEMA_VERSION, saved on every extraction run
  tests/test_schema.py
api/                        FastAPI app + Dockerfile
  app/main.py               GET /health, GET /schema
  app/config.py             settings from environment / .env
worker/                     arq worker + Dockerfile
  worker/main.py            process_agreement job (stub until Phase 4)
databricks/notebooks/
  00_setup.sql              catalog, schemas, raw PDF volume
scripts/download_cuad.py    downloads CUAD into data/cuad/
web/                        Next.js app (scaffolded in Phase 3)
docker-compose.yml          Postgres, Qdrant, Redis, API, worker
```

## Getting started

Prerequisites: Python 3.11+, Node 20+, [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e "contract_core[dev]" -r api/requirements.txt -r worker/requirements.txt
pytest contract_core
```

Full stack (Postgres, Qdrant, Redis, API, worker):

```powershell
docker compose up --build
```

- http://localhost:8000/health: every service should report `ok`
- http://localhost:8000/docs: OpenAPI UI
- http://localhost:6333/dashboard: Qdrant UI

Run the API on the host against the compose databases:

```powershell
docker compose up -d postgres redis qdrant
cd api; uvicorn app.main:app --reload
```

Data:

```powershell
python scripts/download_cuad.py   # -> data/cuad/ (gitignored)
```

Databricks (Free Edition):

1. Sign up at https://www.databricks.com/learn/free-edition
2. Import and run `databricks/notebooks/00_setup.sql`
3. Upload the CUAD PDFs into the volume `contracts.bronze.raw_pdfs`

Free Edition is for non-commercial learning, so only public CUAD data goes on it.

## Progress by phase

Last updated: 25 Oct 2026. Each phase ends with something you can demo. A task is ticked only once it's finished and verified.

| Phase | Weeks | Track | Status |
|---|---|---|---|
| 0 Setup | 1 | Shared | In progress |
| 1 Bronze and silver parsing | 2–3 | Databricks | Not started |
| 2 Structured extraction + MLflow | 4–5 | Databricks | Not started |
| 3 Postgres + FastAPI MVP | 6–7 | App | Not started |
| 4 Live upload + LangGraph | 8–9 | App | Not started |
| 5 Qdrant + RAG Q&A | 10–11 | App | Not started |
| 6 Router, lineage, multi-agreement | 12–13 | App | Not started |
| 7 Evals, observability, deploy | 14–15 | App | Not started |
| 8 Analytics and polish | 16 | Databricks | Not started |

### Phase 0 — Setup (week 1) · In progress

**Deliverable:** running local stack + empty Databricks medallion layout.

- [x] Monorepo: `contract_core/`, `api/`, `worker/`, `databricks/`, `web/`, plus `scripts/`
- [x] `docker-compose.yml`: Postgres, Qdrant, Redis, FastAPI, worker
- [ ] Start the stack with `docker compose up --build` and confirm `/health` reports `ok` for every service
- [x] Databricks setup notebook: catalog `contracts`, schemas `bronze` / `silver` / `gold`, volume for raw PDFs
- [ ] Create the Free Edition workspace and run `00_setup.sql`
- [x] CUAD download script
- [x] Download CUAD: 510 contracts as PDF and text, plus the `master_clauses.csv` answer key
- [ ] Pick 30 contracts as the golden set (include table-heavy, scanned and unsigned ones). CUAD has no labels for payment terms or signature status, and only says whether a liability cap exists, so label those by hand
- [x] Pydantic `Agreement` schema, each field with source quote + page
- [x] Validation rules (brought forward from Phase 2)
- [x] Install Python dependencies and pass `pytest contract_core` (4 tests pass)
- [x] `git init` and first commit

**Work done (24 Oct 2026)**

- **`contract_core` schema** ([schema.py](contract_core/src/contract_core/schema.py)): `Agreement` with title, agreement type, parties, effective and expiry dates, initial term, auto-renewal, renewal term, termination notice (days), payment terms, liability cap (amount, currency, description), governing law and signatories. Each scalar field is an `Extracted[T]` holding `value`, `evidence` (verbatim quote + 1-based page) and `confidence`. Parties carry name, role and evidence. Signatories carry signer name, title, date, page and signature type (digital, wet ink, typed, none, unknown).
- **Validation** ([validation.py](contract_core/src/contract_core/validation.py)): `validate_agreement()` flags fewer than two parties, an expiry date on or before the effective date, values with no evidence, and evidence pages beyond the document length. It returns a list of issues that the Phase 4 retry loop can feed back to the model and that Phase 2 can reuse as data-quality expectations.
- **Versioning** ([versions.py](contract_core/src/contract_core/versions.py)): `SCHEMA_VERSION = "1.0.0"`, to be saved on every extraction run.
- **Tests** ([test_schema.py](contract_core/tests/test_schema.py)): four tests covering JSON round-trip, JSON-schema generation, a valid agreement, and each validation rule. All four pass.
- **API** ([main.py](api/app/main.py)): FastAPI skeleton. `GET /health` reports Postgres, Redis and Qdrant connectivity; `GET /schema` returns the shared JSON schema and its version.
- **Worker** ([main.py](worker/worker/main.py)): arq worker with a stub `process_agreement` job.
- **Docker** ([docker-compose.yml](docker-compose.yml)): Postgres 16.6 (with health check), Qdrant 1.20.0, Redis 7.4, and API and worker images. Both images build from the repo root so they install `contract_core`.
- **Databricks** ([00_setup.sql](databricks/notebooks/00_setup.sql)): creates catalog `contracts`, schemas `bronze`, `silver`, `gold`, and volume `contracts.bronze.raw_pdfs`.
- **Data** ([download_cuad.py](scripts/download_cuad.py)): downloads CUAD v1 from Zenodo into `data/cuad/`, which is gitignored.
- **CUAD downloaded** (kept outside the repo): 510 contracts in about 25 contract-type folders, each as PDF and plain text. `master_clauses.csv` has one row per contract, with a clause column and an answer column for each of the 41 categories: 33 are Yes/No, and 8 hold values such as names, dates and durations. The 28 per-category Excel reports and the SQuAD-style JSON repeat the same labels and aren't needed.

**Work done (25 Oct 2026)**

- **Python dependencies installed** into `.venv`. Yesterday's `psycopg[binary]` failure didn't recur. It looked like a network problem: the first attempt couldn't see any versions on PyPI.
- **Smoke test:** `GET /schema` returns the 13-field schema. `GET /health` responds and reports each service as unreachable until the compose stack runs. The worker imports and registers `process_agreement`.
- **Qdrant image bumped to 1.20.0** to match the installed `qdrant-client` 1.20, which warns when the two are more than one minor version apart. `qdrant-client` is now pinned to `~=1.20.0` so they stay in step.
- **Git repository** created with a first commit; `.gitattributes` keeps line endings as LF, since the code runs in Linux containers. Pushed to https://github.com/sauravtiwari/Agreement-Intelligence.
- **Postgres moved to host port 5433**, because a local Postgres on the dev machine already uses 5432. Inside the compose network the services still talk to `postgres:5432`.
- **Docker Desktop installed** but can't start yet: it needs WSL 2, which isn't installed.

**Decisions**

- Validation rules were brought forward from Phase 2 because they're small and the schema tests use them.
- Next.js scaffolding is deferred to Phase 3, when UI work starts. `web/` holds a placeholder README.
- Python dependencies use minimum versions (`>=`) for now, except `qdrant-client`, which is pinned to the Qdrant server's minor version. A lock file comes once the stack runs.

**Blocked / remaining**

- The compose stack hasn't been started: Docker Desktop needs WSL 2 (`wsl --install` in an admin terminal, then restart).
- Databricks workspace not created; golden set not picked.

### Phase 1 — Databricks bronze and silver parsing (weeks 2–3) · Not started

**Deliverable:** `silver.parsed_documents` with pages, tables and boxes.
**Databricks skills:** Volumes, Auto Loader, Delta, Unity Catalog, AI functions.

- [ ] Bronze: Auto Loader (`binaryFile`) ingests PDFs from the volume into a Delta table
- [ ] Practise Delta basics: MERGE, time travel, schema evolution, `OPTIMIZE`
- [ ] Silver: `ai_parse_document` → text, tables, layout, bounding boxes per page
- [ ] Compare with Docling run locally on the same 30 PDFs; note which handles tables better
- [ ] Unity Catalog: table comments, permissions, lineage view

Note: CUAD mixes `.PDF` (311 files) and `.pdf` (199) extensions, so the Auto Loader file filter has to match both.

### Phase 2 — Structured extraction + MLflow (weeks 4–5) · Not started

**Deliverable:** gold tables + an accuracy report per field.
**Databricks skills:** declarative pipelines, expectations, MLflow, Jobs scheduling.

- [ ] Extraction prompts in `contract_core` (the schema was done in Phase 0)
- [ ] Run extraction in Databricks with `ai_query` (JSON schema output) or a pandas UDF that calls the shared code
- [x] Validation rules: dates parse, expiry after effective date, both parties present (done in Phase 0)
- [ ] Lakeflow Declarative Pipeline with data-quality expectations (bad rows quarantined)
- [ ] MLflow: log prompt version, model and field-level accuracy against the golden set
- [ ] Gold tables: `agreements`, `parties`, `clauses`, `payment_schedule`

### Phase 3 — Postgres + FastAPI MVP (weeks 6–7) · Not started

**Deliverable:** browse and view CUAD agreements end to end.

- [ ] Postgres schema (Alembic migrations): agreements, parties, clauses, tables, signatures, extraction_runs (with prompt, model and schema versions)
- [ ] Sync job: Databricks gold → Postgres (upsert by agreement id)
- [ ] FastAPI: `GET /agreements`, `GET /agreements/{id}`, filters (party, expiry window, status)
- [ ] Next.js detail page: extracted fields with evidence quotes; PDF viewer highlighting the source box

### Phase 4 — Live upload path + LangGraph (weeks 8–9) · Not started

**Deliverable:** upload a new PDF and watch it appear, reviewed, on the detail page.

- [ ] `POST /agreements/upload` → blob storage → queue (arq + Redis) → worker
- [ ] LangGraph ingestion graph in the worker: parse → extract → validate → retry with error feedback (max 2) → save
- [ ] Signatures: pyHanko for digital signatures; vision-LLM check of signature-page crops for wet ink; execution status per party
- [ ] Human review: low-confidence fields pause the graph (interrupt); review UI approves or corrects
- [ ] SHA-256 dedup; processing status pushed to the UI

### Phase 5 — Qdrant + RAG Q&A (weeks 10–11) · Not started

**Deliverable:** ask a question about a contract and get a cited answer.

- [ ] Clause-aware chunking (section headings, numbered clauses; tables kept whole)
- [ ] Qdrant collection: dense + sparse (BM25) vectors; payload `tenant_id`, `agreement_id`, `clause_type`, `section_no`, `page`; payload indexes on the filter fields
- [ ] Databricks batch embeds and upserts chunks for the backfill; the worker upserts live uploads
- [ ] `POST /chat`: hybrid search filtered by agreement → rerank → answer with page citations

### Phase 6 — Router, lineage, multi-agreement (weeks 12–13) · Not started

**Deliverable:** "Which contracts with Acme renew next quarter, and what are their termination terms?" works.

- [ ] LangGraph query router: structured (SQL on Postgres) vs clause (Qdrant) vs comparison (fan-out)
- [ ] Document lineage: MSA → SOW → amendments; compute effective terms
- [ ] Multi-turn chat memory via the LangGraph Postgres checkpointer
- [ ] Groundedness check before answering

### Phase 7 — Evals, observability, deploy (weeks 14–15) · Not started

**Deliverable:** deployed demo with an eval dashboard.

- [ ] Langfuse tracing on both graphs; cost and latency per document and per query
- [ ] Eval suite in CI: field accuracy (golden set) + faithfulness and citation accuracy for Q&A
- [ ] Auth + tenant isolation enforced in SQL and Qdrant filters
- [ ] Deploy: containers to Azure (App Service or AKS), Qdrant Cloud, managed Postgres

### Phase 8 — Analytics and polish (week 16) · Not started

- [ ] Databricks SQL dashboard: contracts expiring by month, value by counterparty, extraction accuracy trend
- [ ] Alerts: renewals due, unsigned drafts
- [ ] Write-up: architecture, trade-offs, eval results (portfolio piece)
- [ ] Optional: Databricks Data Engineer Associate certification

## Key design decisions

1. **Extraction is not RAG.** Metadata comes from whole-document structured extraction into Postgres. Qdrant serves clause Q&A only.
2. **One shared core.** `contract_core` is plain Python with no framework coupling, so the same functions run in a Databricks pandas UDF and in the worker.
3. **Chunks and embeddings are stored in Postgres/Delta too.** Rebuilding or migrating the Qdrant collection is then an upsert job, with no re-embedding.
4. **Every extraction is versioned.** `parser_version`, `prompt_version`, `model` and `schema_version` are saved per run, so bulk reprocessing is safe and traceable.
5. **Retriever behind an interface.** Graph nodes call `retriever.search(query, tenant_id, filters)`, so swapping Qdrant for another store is a config change.
6. **Tenant filter from day one.** `tenant_id` is on every Postgres row and every Qdrant payload; access is enforced in queries, never by the LLM.

## Definition of done

A new PDF goes from upload to a reviewed detail page and cited answers, with measured accuracy:

- Field-level extraction accuracy measured on the 30-contract golden set (target set after the Phase 2 baseline)
- Signature status correct per party on the golden set
- Cited answers with page numbers; faithfulness tracked in CI
- The same PDF gives the same fields on the Databricks batch path and the live path
- Deployed demo + write-up of architecture and trade-offs
