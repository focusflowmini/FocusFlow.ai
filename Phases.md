# FocusFlow.ai — Full-Scale Architecture Review & Phased Roadmap

> **Perspective:** Senior AI Systems Architect  
> **Date:** March 26, 2026  
> **Scope:** Complete codebase audit — Backend, Extension, Infrastructure, AI Pipeline

---

## 1. Identified Issues (Current State)

### 🔴 Critical (System-breaking)

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| C1 | **`agent_logs.json` is NDJSON, not valid JSON** — `reset_sessions()` writes `[]` but `log_event()` appends raw JSON lines. File is perpetually corrupted after first mixed-use. IDE errors confirm this. | `logges.py:80-93`, `main.py:82-84` | Logs silently lost, error in IDE, `json.loads()` fails on re-read |
| C2 | **Exposed API key committed to git** — Groq API key is hardcoded in `.env` which is tracked by git (no `.gitignore` entry for `.env` in backend). | `backend/.env` | Key compromise, billing abuse, credential leak |
| C3 | **No authentication or authorization** — Any client can start sessions, connect to WebSockets, or reset ALL server data. `/session/reset` is a **nuke button** with zero protection. | `main.py:74-86` | Any attacker can wipe all sessions, hijack other users' data |
| C4 | **`groq_service.py` is dead code** — Entire file is imported nowhere. The actual LLM calls go through DSPy in `agent_logic.py`. Two different model references (`llama-3.3-70b-versatile` vs config model). | `groq_service.py` | Confusion, maintenance burden, misleading architecture |
| C5 | **`tracker.py:update_score()` references `datetime` without import** — `datetime.now()` will crash at runtime. The method appears to be dead code since `main.py` bypasses it. | `tracker.py:60` | `NameError` crash if ever called |
| C6 | **`startSession()` in `background.js` ignores the `goal` parameter** — It accepts `goal` but only calls `connectWebSocket()`, which reads `session_id` from storage. The goal is never forwarded. | `background.js:107-111` | Session starts are fragile; goal not propagated |

### 🟡 High (Reliability & Correctness)

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| H1 | **File-based persistence (`sessions.json`)** — `save_sessions()` and `load_sessions()` do full read/write on every single tab event. Race conditions under concurrent WebSocket writes. No file locking. | `main.py:19-36` | Data corruption, lost writes, O(n) I/O per request |
| H2 | **CORS is `allow_origins=["*"]`** — Wide-open CORS in production allows any website to call the backend API. | `main.py:42-48` | Cross-origin exploitation, CSRF attacks |
| H3 | **No WebSocket heartbeat** — Docs require heartbeat (`technical_requirements.md` 1.1), but neither extension nor backend implements one. Service worker can be killed by Chrome after 30s of inactivity. | `background.js`, `main.py:88` | Silent disconnects, zombie sessions, no monitoring |
| H4 | **Bare `except:` swallowing errors** — `_evaluation_node` catches all exceptions and silently defaults to 0.5. No logging. | `agent_logic.py:100` | Hides LLM failures, rate limit errors, network issues |
| H5 | **No input validation on WebSocket messages** — `json.loads(data)` can crash on malformed input. No schema validation on `tab_update`, `set_focus_tab`, or `feedback` messages. | `main.py:101-102` | Server crash from malformed client data |
| H6 | **Blocking I/O in async context** — `save_sessions()`, `load_sessions()`, and `log_event()` do synchronous file I/O inside async handlers, blocking the event loop. | `main.py`, `logges.py` | Event loop starvation under load |
| H7 | **Whitelist feature is declared but never used** — `/session/start` accepts `whitelist`, `SessionTracker` stores it, but no code ever checks it during classification or decision-making. | `main.py:61`, `tracker.py:8` | Feature is dead |
| H8 | **DSPy `dspy.settings.configure()` is deprecated** — Should use `dspy.configure(lm=...)` in newer DSPy versions. | `agent_logic.py:54` | Eventually breaks on DSPy upgrade |

### 🟠 Medium (Quality & Maintainability)

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| M1 | **Typo: class named `Logges`** — Should be `Logger` or `ObservationPipeline`. Confusing naming throughout. | `logges.py:100` | Poor readability |
| M2 | **Duplicate drift/strategy logic** — Both `agent_logic.py:_decision_node` AND `logges.py:Prevention.recommend_strategy` compute action strategies with slightly different thresholds. Which one wins? | `agent_logic.py:109-133`, `logges.py:43-62` | Conflicting decisions, unpredictable behavior |
| M3 | **No tests whatsoever** — Zero unit tests, integration tests, or E2E tests. | Entire project | No confidence in changes, regressions everywhere |
| M4 | **Content script injects styles via `document.head.appendChild`** — Creates duplicate `<style>` tags on every warning. No cleanup. | `blocker.js:61-67` | DOM pollution, memory leak |
| M5 | **`config.py` double-loads env** — Uses both `load_dotenv()` AND `pydantic_settings` which auto-reads `.env`. Redundant. | `config.py:3-5` | Confusion about which takes precedence |
| M6 | **Architecture doc says PostgreSQL** — But the actual implementation uses flat JSON files. Docs are misleading. | `docs/architecture.md:36` | False claims |
| M7 | **Extension popup fetches from `localhost:8000`** — Hardcoded backend URL means the extension cannot work with any deployed server. | `popup/script.js:26,74`, `background.js:9` | Cannot deploy to production |
| M8 | **DSPy output parsing is fragile** — `float(result.relevance)` assumes LLM returns a clean float string. LLMs often return `"0.7 - moderately relevant"` | `agent_logic.py:99` | Silent fallback to 0.5, inaccurate scores |

---

## 2. Identified Enhancements

### 🏗️ Architecture

| # | Enhancement | Rationale |
|---|-------------|-----------|
| A1 | **Replace JSON file persistence with a real database** (SQLite → PostgreSQL) | Eliminate race conditions, enable queries, support analytics |
| A2 | **Add an API gateway / Auth layer** (JWT or API key per user) | Multi-user security, session isolation, rate limiting |
| A3 | **Decouple AI pipeline from request handler** — Use a task queue (Celery/Redis) for LLM calls | LLM calls take 1-3s; blocking the WebSocket loop kills responsiveness |
| A4 | **Implement a proper logging framework** (structlog / Python logging) | Replace `print()` statements, enable log levels, structured output |
| A5 | **Configurable backend URL in extension** — Use `chrome.storage.sync` or options page | Enable production deployment, multi-environment support |
| A6 | **Add WebSocket ping/pong heartbeat** | Detect dead connections, keep service worker alive |

### 🧠 AI / Agent Pipeline

| # | Enhancement | Rationale |
|---|-------------|-----------|
| AI1 | **Unify decision logic** — Remove the duplicate strategy computation in `logges.py`, let LangGraph be the single source of truth | Eliminate conflicting actions |
| AI2 | **Add structured output parsing** (JSON mode or Pydantic output parser) | Stop relying on fragile `float()` casts from LLM text |
| AI3 | **Implement the whitelist** — Actually use the whitelist domains in classification | Users expect this feature since the API accepts it |
| AI4 | **Add long-term memory** — Store per-user feedback to improve classification over time | Currently, "Actually Productive" feedback is fire-and-forget |
| AI5 | **Add LLM fallback / retry with exponential backoff** | One failed Groq call shouldn't crash the entire session |
| AI6 | **Support multiple LLM providers** (Groq, OpenAI, local Ollama) | Reduce vendor lock-in, enable offline mode |

### 🎨 Extension / UX

| # | Enhancement | Rationale |
|---|-------------|-----------|
| U1 | **Add a productivity dashboard** — Show session stats, focus time, top distractions | Users have no visibility into their productivity patterns |
| U2 | **Session timer in popup** — Show elapsed focus time | Core UX expectation for a productivity tool |
| U3 | **Options page for configuration** — Backend URL, sensitivity, theme, notification preferences | Currently zero user configurability |
| U4 | **Keyboard shortcuts** — Quick set focus tab, dismiss warnings | Power user workflow |
| U5 | **Badge icon updates** — Show distraction score on extension badge | Ambient awareness without opening popup |
| U6 | **Warning auto-dismiss should be configurable** — Currently hardcoded to 10s | `blocker.js:78` |

### 🔧 DevOps / Quality

| # | Enhancement | Rationale |
|---|-------------|-----------|
| D1 | **Add comprehensive test suite** — Unit tests for all services, integration tests for WebSocket flow | Zero tests = zero confidence |
| D2 | **Set up CI/CD pipeline** — Linting (ruff), type checking (mypy), tests | Catch regressions before merge |
| D3 | **Dockerize the backend** | Consistent dev/prod environments |
| D4 | **Add environment-based config** — dev/staging/production profiles | Currently no environment separation |
| D5 | **Implement proper error monitoring** — Sentry or equivalent | `print()` logging is invisible in production |

---

## 3. Phased Roadmap

### Phase 0: Triage & Stabilize (1 week)
> **Goal:** Fix all critical/high bugs. Make the existing app actually work reliably.

**Priority: 🔴 CRITICAL — Do this before anything else.**

| Task | Fixes | Effort |
|------|-------|--------|
| Fix `agent_logs.json` corruption | C1 | 1h |
| Rotate and gitignore the Groq API key | C2 | 30m |
| Remove dead `groq_service.py` | C4 | 15m |
| Fix `datetime` import in `tracker.py` | C5 | 5m |
| Fix `startSession()` goal propagation | C6 | 30m |
| Add basic WebSocket message validation | H5 | 2h |
| Replace bare `except:` with proper error handling + logging | H4 | 1h |
| Restrict CORS to known extension origin | H2 | 30m |
| Make backend URL configurable in extension | M7 | 1h |
| Add `.env` to `.gitignore` properly | C2 | 5m |

**Deliverables:** App doesn't crash, logs don't corrupt, secrets don't leak.

---

### Phase 1: Foundation Refactor (2 weeks)
> **Goal:** Replace hacked-together internals with production-grade infrastructure.

**Priority: 🟡 HIGH — Required before adding any features.**

#### 1.1 Database Layer
- [ ] Add SQLite (dev) + PostgreSQL (prod) via SQLAlchemy/Tortoise ORM
- [ ] Migrate `sessions.json` and `agent_logs.json` to database tables
- [ ] Schema: `sessions`, `tab_events`, `agent_actions`, `user_feedback`
- [ ] Add Alembic for migrations

#### 1.2 Unified AI Pipeline
- [ ] Remove duplicate decision logic (unify `agent_logic.py` + `logges.py`)
- [ ] Add structured output parsing with Pydantic models
- [ ] Implement LLM retry with exponential backoff
- [ ] Implement the whitelist feature in the classification node

#### 1.3 Authentication
- [ ] Add API key or JWT-based auth for REST endpoints
- [ ] Add session ownership validation on WebSocket connect
- [ ] Secure the `/session/reset` endpoint (admin-only or session-scoped)

#### 1.4 Async I/O
- [ ] Replace all synchronous file I/O with async equivalents or DB calls
- [ ] Move LLM inference off the WebSocket handler into a background task

#### 1.5 Observability
- [ ] Replace all `print()` with `structlog`
- [ ] Add request/response logging middleware
- [ ] Add WebSocket connection lifecycle logging

**Deliverables:** Production-grade backend with proper DB, auth, and observability.

---

### Phase 2: Extension Hardening & UX (2 weeks)
> **Goal:** Make the extension production-ready and delightful.

**Priority: 🟠 MEDIUM-HIGH — User-facing quality.**

#### 2.1 Extension Architecture
- [ ] Add `chrome.alarms` heartbeat to keep service worker alive
- [ ] Add WebSocket reconnection with exponential backoff + jitter
- [ ] Add an Options page (backend URL, sensitivity slider, notification prefs)
- [ ] Store settings in `chrome.storage.sync` for cross-device persistence

#### 2.2 UX Improvements
- [ ] Add session timer in popup (elapsed focus time)
- [ ] Add extension badge showing distraction score (color-coded)
- [ ] Add keyboard shortcuts (set focus tab, dismiss warning)
- [ ] Make warning auto-dismiss duration configurable
- [ ] Fix content script style injection (prevent duplicate `<style>` tags)

#### 2.3 Popup Dashboard
- [ ] Show real-time distraction score with animated gauge
- [ ] Show recent AI decisions (last 5 actions)
- [ ] Show current context window (what the AI "sees")

**Deliverables:** Polished, reliable extension UX.

---

### Phase 3: Intelligence & Memory (3 weeks)
> **Goal:** Make the AI agent genuinely intelligent with long-term learning.

**Priority: 🟢 MEDIUM — Differentiation features.**

#### 3.1 Long-Term Memory
- [ ] Store user feedback ("Actually Productive") persistently per user
- [ ] Build a per-user domain reputation model (frequently allowed/blocked sites)
- [ ] Use feedback history as few-shot examples in LLM prompts

#### 3.2 Advanced Classification
- [ ] Add URL content extraction for ambiguous sites (optional, privacy-conscious)
- [ ] Implement multi-signal scoring (URL pattern, title NLP, time-of-day, session duration)
- [ ] Add category confidence scores with "uncertain" handling

#### 3.3 Multi-Provider LLM
- [ ] Abstract LLM provider behind an interface (Groq, OpenAI, Ollama)
- [ ] Add local model support for privacy-first users
- [ ] Implement provider health checks and automatic fallback

#### 3.4 Advanced Agent Graph
- [ ] Add conditional branching in LangGraph (skip evaluation for whitelisted domains)
- [ ] Add a "reflection" node that assesses its own decision quality
- [ ] Implement session-aware scoring (gradually increase tolerance for long sessions)

**Deliverables:** AI that learns from user behavior and gets smarter over time.

---

### Phase 4: Analytics & Scale (3 weeks)
> **Goal:** Production deployment with analytics dashboard and multi-user support.

**Priority: 🔵 LOWER — Scale & monetization readiness.**

#### 4.1 Analytics Dashboard (Web App)
- [ ] Build a React/Next.js dashboard
- [ ] Charts: focus time trends, distraction categories, productivity score over time
- [ ] Daily/weekly productivity reports
- [ ] Session replay: timeline of AI decisions

#### 4.2 Multi-User Infrastructure
- [ ] User accounts with OAuth (Google, GitHub)
- [ ] Per-user data isolation and encryption
- [ ] Rate limiting per user (LLM cost control)
- [ ] Subscription tier support (free/pro)

#### 4.3 Deployment & DevOps
- [ ] Dockerize backend with docker-compose (app + DB + Redis)
- [ ] CI/CD pipeline (GitHub Actions): lint → test → build → deploy
- [ ] Add Sentry for error monitoring
- [ ] Add health check and readiness endpoints
- [ ] Deploy to Railway/Render/Fly.io with managed Postgres

#### 4.4 Chrome Web Store
- [ ] Prepare extension for Chrome Web Store submission
- [ ] Add privacy policy and terms of service
- [ ] Add onboarding flow for new users

**Deliverables:** Fully deployed SaaS-ready product.

---

## 4. Priority & Impact Matrix

```
                        HIGH IMPACT
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        │  Phase 0: Triage  │  Phase 1: Refactor│
        │  ● Fix crashes    │  ● Database       │
        │  ● Fix security   │  ● Auth           │
        │  ● Fix dead code  │  ● Unified AI     │
        │                   │                   │
 LOW ───┼───────────────────┼───────────────────┼─── HIGH
 EFFORT │                   │                   │  EFFORT
        │  Phase 2: UX      │  Phase 4: Scale   │
        │  ● Heartbeat      │  ● Analytics      │
        │  ● Badge/Timer    │  ● Multi-user     │
        │  ● Options page   │  ● CI/CD          │
        │                   │                   │
        │  Phase 3: Intel   │                   │
        │  ● Memory         │                   │
        │  ● Multi-LLM      │                   │
        └───────────────────┼───────────────────┘
                            │
                        LOW IMPACT
```

| Phase | Impact | Effort | Priority |
|-------|--------|--------|----------|
| **Phase 0** | 🔴 Critical | Low (1 week) | **P0 — NOW** |
| **Phase 1** | 🟡 High | Medium (2 weeks) | **P1 — Next** |
| **Phase 2** | 🟠 Medium-High | Medium (2 weeks) | **P2** |
| **Phase 3** | 🟢 Medium | High (3 weeks) | **P3** |
| **Phase 4** | 🔵 Lower initially, High long-term | High (3 weeks) | **P4** |

---

## 5. Quick Wins (Can do today)

These require < 30 minutes each and immediately improve the project:

1. **Add `.env` to `.gitignore`** and rotate the leaked API key
2. **Delete `groq_service.py`** (dead code)
3. **Fix `datetime` import** in `tracker.py`
4. **Replace bare `except:`** in `agent_logic.py:100` with `except (ValueError, TypeError):`
5. **Fix `agent_logs.json`** — make `log_event()` use proper JSON array append pattern

---

> **Bottom Line:** The core *concept* of FocusFlow is strong — agentic AI for productivity is a compelling product. But the implementation has critical bugs (corrupted logs, leaked keys, dead code), no tests, no auth, and uses flat files instead of a database. Phase 0 + Phase 1 will transform it from a broken prototype into a solid foundation. Phases 2-4 build the features that make it genuinely valuable.
