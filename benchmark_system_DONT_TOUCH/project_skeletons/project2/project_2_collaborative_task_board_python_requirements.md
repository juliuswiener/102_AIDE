# Collaborative Task Board — Requirements (v0.1)

**Goal**: Build a Trello‑like board with multi‑user support, real‑time updates (WebSockets), and durable persistence. Python‑only backend; minimal JS frontend sufficient for automated tests. Entirely offline and deterministic.

---

## 1. Scope & Objectives
- **Primary objectives**
  - Users can sign up/sign in (simple token auth).
  - Create/join boards; create lists and cards; drag/drop reorder.
  - Comments on cards; activity log per board.
  - Real‑time state sync to connected clients via WebSockets.
  - Durable persistence to DB; safe restarts.
- **Non‑goals (v0.1)**
  - No SSO/OAuth; no email.
  - No file attachments; no external integrations.
  - No complex permissions (simple board membership only).

---

## 2. System Overview
- **Services**: `api` (FastAPI), `ws` (FastAPI/WebSocket routes; may share process), `db` (Postgres default; SQLite acceptable for local mode)
- **Data flow**: HTTP/JSON for CRUD; WebSockets for push events (board updates). Frontend subscribes to board channel.
- **Runtime profiles**: single container for app + DB container (docker‑compose).

---

## 3. Data Model
- **users** (`id` PK, `email` UNIQUE, `password_hash`, `created_at`)
- **boards** (`id` PK, `name`, `owner_id` FK users, `created_at`)
- **board_members** (`board_id` FK, `user_id` FK, UNIQUE(board_id,user_id))
- **lists** (`id` PK, `board_id` FK, `name`, `position` INT, `created_at`)
- **cards** (`id` PK, `list_id` FK, `title`, `description`, `position` INT, `created_at`, `updated_at`)
- **comments** (`id` PK, `card_id` FK, `user_id` FK, `body`, `created_at`)
- **events** (append‑only: `id`, `board_id`, `type`, `payload JSONB`, `created_at`) for audit/log and replay.

---

## 4. Authentication & Authorization
- **Auth**: Email + password. Issue **opaque token** on login (HTTP header `Authorization: Bearer <token>`).
- **Password storage**: Argon2 or bcrypt (library).
- **AuthZ**: Only board members can read/write a board; owner can invite members.

---

## 5. REST API (FastAPI)
- `POST /auth/signup {email,password}` → `{token}`
- `POST /auth/login {email,password}` → `{token}`
- `GET /me` → current user
- `POST /boards {name}` → create board
- `GET /boards` → list my boards
- `POST /boards/{board_id}/members {email}` → invite/add existing user
- `GET /boards/{board_id}` → board details (lists + cards summarized)
- `POST /boards/{board_id}/lists {name}` → create list
- `PATCH /lists/{list_id} {name?, position?}`
- `POST /lists/{list_id}/cards {title, description?, position?}`
- `PATCH /cards/{card_id} {title?, description?, position?, list_id?}` (move + reorder)
- `POST /cards/{card_id}/comments {body}`
- `GET /boards/{board_id}/events?since=<cursor>` → event stream (HTTP pull fallback)

All responses are JSON and validate against OpenAPI schema. Errors return JSON `{error, detail}` with 4xx/5xx.

---

## 6. WebSockets (Real‑time Updates)
- `WS /ws/boards/{board_id}`: authenticated clients join board room.
- Server broadcasts events (e.g., `card.created`, `card.moved`, `comment.created`) as JSON messages.
- On reconnect, client may send `{"resume_from": <event_id>}` to fetch missed events via HTTP events API, then resumes live stream.
- Back‑pressure: if client is slow, drop and signal to use HTTP catch‑up.

---

## 7. Eventing Model
- Every mutation produces an **event** persisted in `events` (append‑only).
- Event envelope: `{id, board_id, type, actor_user_id, payload, created_at}`.
- Types include: `list.created`, `list.renamed`, `list.reordered`, `card.created`, `card.updated`, `card.moved`, `card.reordered`, `comment.created`, `member.added`.
- WebSocket broadcasts mirror these events; HTTP `/events` enables catch‑up.

---

## 8. Ordering & Concurrency
- **Positions**: integer positions with gaps (e.g., 100, 200, ...); renormalize when necessary.
- **Moves**: moving a card updates both old/new list positions atomically (transaction).
- **Optimistic concurrency**: `updated_at` check on card updates; reject stale writes with 409.

---

## 9. Frontend (Minimal for Tests)
- Jinja2 templates + vanilla JS served by FastAPI (`/` lists boards, `/b/{id}` shows lists/cards).
- Client opens WS to `/ws/boards/{id}`; reflects changes live.
- Drag/drop optional for v0.1; tests may simulate via API calls.

---

## 10. Performance Targets (v0.1)
- **API** P95 latency ≤ **150 ms** for typical CRUD under 100 rps (local).
- **WS fanout**: broadcast to **≥ 50** connected clients within **200 ms** for single event.
- **Startup**: cold start ≤ **2 s**.

---

## 11. Reliability & Recovery
- **Durability**: all mutations in DB transactions; events appended before broadcast.
- **Crash safety**: on restart, clients can catch up using `/events` since last `event_id`.
- **Idempotency**: invitation of existing member is no‑op.

---

## 12. Logging & Metrics
- Structured logs with request ids and user ids.
- Metrics: `http_requests_total`, `ws_clients_gauge`, `events_broadcast_total`, `db_txn_seconds` (simple counters/histograms; optional `/metrics`).

---

## 13. Security
- Password hashing (argon2/bcrypt); tokens signed with server secret.
- CORS disabled by default; API binds to localhost in dev.
- Validate payload sizes; per‑user rate limits for mutation endpoints (simple leaky bucket in memory acceptable for v0.1).

---

## 14. Testing & Acceptance Criteria
- **Unit**: services (auth, board, list, card), position math, event serialization.
- **Integration**: multi‑user flows; reorder/move; restart and catch‑up; WS broadcast correctness under concurrent writers.
- **API schema**: OpenAPI validation; error codes; auth required where expected.
- **Determinism**: same ordered sequence of API calls → identical DB state + event sequence.
- **Completion criterion**: All required tests pass within configured time cap (harness‑enforced).

---

## 15. Configuration
- `.env` or YAML: `DATABASE_URL`, `JWT_SECRET` (or opaque token secret), `WS_MAX_CLIENTS`, `RATE_LIMITS`, `LOG_LEVEL`.

---

## 16. Directory Layout (reference)
```
board/
  api/
    main.py
    routes/
    ws.py
  core/
    auth.py
    config.py
    db.py
  domain/
    boards.py
    lists.py
    cards.py
    comments.py
    events.py
  web/
    templates/
    static/
  tests/
    unit/
    integration/
  pyproject.toml
  README.md
```

---

## 17. Milestones
- **M1 (Skeleton)**: DB schema/migrations; FastAPI skeleton; auth endpoints; health.
- **M2 (Boards/Lists/Cards)**: CRUD + position handling; unit tests.
- **M3 (Events/WS)**: append‑only events; WS broadcast + HTTP catch‑up; integration tests.
- **M4 (Comments & Activity)**: comments; board activity log.
- **M5 (Resilience)**: restart recovery; rate limiting; logging/metrics.
- **M6 (Perf pass)**: hit P95/API + WS targets on synthetic load.

---

## 18. Future Extensions
- Fine‑grained permissions; board roles.
- Attachments; checklists; due dates; mentions.
- Export/import; webhooks.
- Horizontal scale via Redis pub/sub for WS fanout.

