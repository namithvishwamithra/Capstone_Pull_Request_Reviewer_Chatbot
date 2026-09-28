# Tasks: Pull Request Reviewer

**Input**: Design documents from `specs/001-pull-request-reviewer/`

**Prerequisites**: `plan.md` and `spec.md` are present. The current `plan.md` remains an unfilled template; these tasks therefore derive the application layout from the PRD and constitution. Confirm and complete the implementation plan before executing setup tasks.

**Testing**: Focused test tasks are included because the project constitution requires tests for behavior changes, contracts, security, and failure paths.

**Organization**: Tasks are grouped by user story so each priority increment can be implemented and validated independently after shared setup.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the two-project web application structure and install the stack already selected by the PRD.

- [X] T001 Create the backend package and dependency manifest in `backend/pyproject.toml` and `backend/app/__init__.py` using Python, FastAPI, Pydantic, and httpx.
- [X] T002 [P] Scaffold the React + TypeScript + Vite application and package scripts in `frontend/package.json`, `frontend/index.html`, and `frontend/src/main.tsx`.
- [X] T003 [P] Add root `.gitignore` rules for Python, Vite, SQLite, environment files, and generated artifacts in `.gitignore`.
- [X] T004 [P] Add local environment variable names and safe placeholder values (never real credentials) to `backend/.env.example` and `frontend/.env.example`.
- [X] T005 Configure backend and frontend lint, format, type-check, and test commands in `backend/pyproject.toml` and `frontend/package.json`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish secure configuration, user identity, storage, shared API contracts, and error handling required by all stories.

- [X] T006 Implement validated server-side settings and startup checks for OAuth, Google AI Studio, database, and frontend-origin configuration in `backend/app/core/config.py`.
- [X] T007 [P] Implement structured API error types and safe exception-to-response handling without secrets or submitted code in `backend/app/core/errors.py` and `backend/app/main.py`.
- [X] T008 Implement a versioned SQLite connection and schema initialization for users, OAuth credentials, request counters, reviews, and chat records in `backend/app/db/database.py` and `backend/app/db/schema.sql`.
- [X] T009 Implement GitHub OAuth authorization, state validation, callback handling, secure server-side token storage, and account lookup in `backend/app/services/auth_service.py` and `backend/app/api/auth.py`.
- [X] T010 Implement secure authenticated-user dependency and account-scoped authorization checks for protected routes in `backend/app/api/dependencies.py`.
- [X] T011 Configure FastAPI CORS to allow only the configured frontend origin and register health/auth routers in `backend/app/main.py`.
- [X] T012 [P] Define shared Pydantic request, response, pagination, and finding schemas in `backend/app/schemas/common.py` and `backend/app/schemas/review.py`.
- [X] T013 [P] Add shared frontend types and a typed API client that sends same-origin credentials and maps safe API errors in `frontend/src/lib/api.ts` and `frontend/src/lib/types.ts`.
- [X] T014 [P] Implement a reusable accessible application shell, route guards, keyboard focus treatment, and global loading/error/empty primitives in `frontend/src/App.tsx` and `frontend/src/components/`.
- [X] T015 Add focused tests for OAuth state/callback validation, account isolation, secret redaction, SQLite schema initialization, and CORS policy in `backend/tests/test_foundation.py`.
- [X] T016 Add frontend tests for authenticated/unauthenticated route states, accessible shared controls, and API error mapping in `frontend/tests/foundation.test.tsx`.

**Checkpoint**: Secure app startup, OAuth identity, account-scoped dependencies, shared schemas, and test commands are available before story work.

---

## Phase 3: User Story 1 - Review a Pull Request (Priority: P1) 🎯 MVP

**Goal**: Authenticated users submit a GitHub PR URL or unified diff and receive a summary with validated, actionable findings.

**Independent Test**: Submit a PR URL with a test GitHub account and a unified diff fixture containing known issues; verify the summary and valid changed-line findings. Submit a no-issue diff and verify an explicit empty-findings state. Confirm oversized input is rejected and no code is reviewed before privacy consent.

### Tests for User Story 1

- [X] T017 [P] [US1] Test PR URL and unified-diff input validation, the 1,000 changed-line limit, and safe error responses in `backend/tests/test_review_input.py`.
- [X] T018 [P] [US1] Test unified diff parsing, changed-line mapping, deleted/renamed files, and invalid finding locations in `backend/tests/test_diff_parser.py`.
- [X] T019 [P] [US1] Test GitHub PR metadata/diff retrieval, unauthenticated and inaccessible PR errors, rate limits, timeouts, and bounded retry behavior with mocked HTTP in `backend/tests/test_github_client.py`.
- [X] T020 [P] [US1] Test structured model response validation, a single repair attempt, severity/category values, and diff-grounded file/line ranges in `backend/tests/test_review_service.py`.
- [X] T021 [P] [US1] Test the review form, consent gating, loading/error/empty states, and summary/finding rendering in `frontend/tests/review-flow.test.tsx`.

### Implementation for User Story 1

- [X] T022 [P] [US1] Implement unified diff parsing with changed-file/hunk records and added-line coordinate mapping in `backend/app/services/diff_parser.py`.
- [X] T023 [P] [US1] Implement GitHub PR URL validation and server-side metadata/diff retrieval with timeouts and bounded exponential-backoff retries in `backend/app/services/github_client.py`.
- [X] T024 [US1] Implement review-input normalization, authentication checks, per-user request limits, and rejection of inputs over 1,000 changed lines in `backend/app/services/review_input_service.py`.
- [X] T025 [US1] Implement file/hunk chunking, generated/binary/lockfile exclusion by default, and coverage accounting in `backend/app/services/diff_chunker.py`.
- [X] T026 [US1] Implement server-side Google AI Studio calls for `gemma-4-26b-a4b-it`, review prompts, low-temperature structured responses, Pydantic validation, and one repair attempt in `backend/app/services/llm_client.py` and `backend/app/services/review_service.py`.
- [X] T027 [US1] Validate every model finding against parsed changed files and line ranges; discard unsupported locations and synthesize per-file results into a review response in `backend/app/services/finding_validator.py` and `backend/app/services/review_service.py`.
- [X] T028 [US1] Implement authenticated review creation and retrieval endpoints with safe validation/upstream failure responses in `backend/app/api/reviews.py` and register them in `backend/app/main.py`.
- [X] T029 [P] [US1] Implement the first-review Google AI Studio disclosure and explicit consent gate before any review submission in `frontend/src/components/PrivacyConsent.tsx` and `frontend/src/features/review/ReviewForm.tsx`.
- [X] T030 [P] [US1] Implement accessible PR URL/unified-diff input, request progress, retryable errors, and review summary/findings display in `frontend/src/features/review/ReviewPage.tsx` and `frontend/src/features/review/ReviewResults.tsx`.
- [X] T031 [US1] Integrate the frontend review flow with authenticated review endpoints and render only validated API findings in `frontend/src/features/review/reviewApi.ts` and `frontend/src/features/review/ReviewPage.tsx`.
- [X] T032 [US1] Run backend and frontend US1 tests and validate PR URL, raw diff, no findings, malformed model output, privacy rejection, and 1,001-line rejection scenarios in `backend/tests/` and `frontend/tests/`.

**Checkpoint**: P1 review is demonstrable without chat or saved-session functionality; results never claim completeness when review fails or input exceeds the cap.

---

## Phase 4: User Story 2 - Ask Follow-up Questions (Priority: P2)

**Goal**: Users ask questions about a completed review and receive progressively streamed answers grounded in the diff, findings, and prior conversation.

**Independent Test**: Complete a review, ask about one finding and the riskiest change, and verify grounded SSE output and session-linked history. Interrupt a stream and verify a clear incomplete/error state.

### Tests for User Story 2

- [X] T033 [P] [US2] Test chat authorization, review ownership, prompt grounding inputs, SSE event format, and upstream failure handling in `backend/tests/test_chat_api.py`.
- [X] T034 [P] [US2] Test streamed chat rendering, cancellation, reconnect/error behavior, and prevention of incomplete-response presentation in `frontend/tests/chat-flow.test.tsx`.

### Implementation for User Story 2

- [X] T035 [US2] Implement account-scoped conversation retrieval and diff/findings-grounded chat prompts in `backend/app/services/chat_service.py`.
- [X] T036 [US2] Implement authenticated SSE chat endpoint with bounded upstream timeout/retry behavior and active-session message history in `backend/app/api/chat.py` and `backend/app/services/chat_service.py`.
- [X] T037 [P] [US2] Implement accessible chat message history, pending/error states, and cancellation controls in `frontend/src/features/chat/ChatPanel.tsx`.
- [X] T038 [US2] Implement SSE consumption, incremental answer rendering, cancellation, and completion/error distinction in `frontend/src/features/chat/chatApi.ts` and `frontend/src/features/chat/ChatPanel.tsx`.
- [X] T039 [US2] Run backend and frontend US2 tests for grounded follow-ups, session context, unauthorized access, stream interruption, and retry exhaustion in `backend/tests/` and `frontend/tests/`.

**Checkpoint**: P1 review remains usable and chat errors never expose secrets or make partial output appear complete.

---

## Phase 5: User Story 3 - Revisit and Share a Review (Priority: P3)

**Goal**: Users explicitly save, list, reopen, navigate, filter, and export review sessions while keeping each account isolated.

**Independent Test**: Save a review, reopen it from the session list, filter findings, navigate from a finding to its diff location, and export Markdown. Verify that another user cannot view the session. Verify configured retention/deletion behavior.

### Tests for User Story 3

- [ ] T040 [P] [US3] Test account-scoped save/list/reopen/export, session state transitions, retention/deletion rules, and absence of unsaved code after session end in `backend/tests/test_sessions.py`.
- [X] T041 [P] [US3] Test severity/category filtering, finding-to-diff navigation, accessible controls, and active review display in `frontend/tests/session-review.test.tsx`.

### Implementation for User Story 3

- [ ] T042 [US3] Decide the saved-session retention duration and deletion policy with the product owner; then update `specs/001-pull-request-reviewer/spec.md` before implementing persistent saved-session storage.
- [ ] T043 [US3] Implement account-scoped save/list/reopen operations for PR reference, findings, and chat history in `backend/app/services/session_service.py` and `backend/app/api/sessions.py`.
- [X] T044 [US3] Implement authenticated Markdown review export with safe escaping and account ownership checks in `backend/app/services/export_service.py` and `backend/app/api/reviews.py`.
- [X] T045 [P] [US3] Implement accessible severity/category filters and clear-filter behavior in `frontend/src/features/review/FindingsFilters.tsx`.
- [X] T046 [P] [US3] Implement diff display and keyboard-accessible finding-to-changed-line navigation/highlighting in `frontend/src/features/review/DiffViewer.tsx`.
- [ ] T047 [US3] Implement saved-session list, save action, and reopen flow in `frontend/src/features/sessions/SessionsPage.tsx`; active-review Markdown export is implemented in `frontend/src/features/review/ReviewResults.tsx`.
- [ ] T048 [US3] Run backend and frontend US3 tests for saved-session retention, deletion, cross-account saved-session access denial, export contents, filters, and finding navigation in `backend/tests/` and `frontend/tests/`.

**Checkpoint**: Do not begin T043 or save-session UI work that depends on retention semantics until T042 is approved and reflected in the spec.

---

## Final Phase: Polish & Cross-Cutting Concerns

- [X] T049 [P] Add a synthetic review evaluation fixture set with known findings and expected changed-line locations in `backend/tests/fixtures/review_eval/`.
- [X] T050 [P] Document local setup, OAuth registration/callback configuration, server-only AI credentials, privacy behavior, and validation commands in `README.md`.
- [X] T051 Run automated accessibility checks for review input, privacy consent, findings filters, and chat controls; preserve keyboard focus indicators and AA-contrast text colors in `frontend/tests/accessibility.test.tsx` and `frontend/src/App.css`.
- [ ] T052 Measure review completion for up to 500 changed lines and first streamed chat token against specification targets; record conditions and results in `specs/001-pull-request-reviewer/quickstart.md`.
- [ ] T053 Review backend logs, errors, CORS, rate limits, OAuth token handling, active-session isolation, and saved-session retention behavior against the constitution in `backend/tests/` and `specs/001-pull-request-reviewer/`.
- [X] T054 Run the complete backend and frontend test, type-check, lint, and build commands documented in `README.md` and fix regressions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; create both application projects first.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Setup and Foundation; delivers the MVP.
- **User Story 2 (Phase 4)**: Depends on shared identity and review/session identifiers. It can proceed after Foundation; integration requires review context from US1.
- **User Story 3 (Phase 5)**: Depends on shared identity and completed review records. T042 is a product-decision gate before persistent session implementation.
- **Polish (Final Phase)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on later stories.
- **US2 (P2)**: Starts after Phase 2; integrates with review context from US1.
- **US3 (P3)**: Starts after Phase 2; review persistence and export require review models from US1, chat-history persistence requires US2, and saved-session retention decision T042 must precede persistent storage.

### Within Each User Story

- Write and run focused tests alongside behavior changes; the constitution requires tests but does not require a TDD-first sequence.
- Complete schemas/data shape before dependent services, services before endpoints, and API behavior before frontend integration.
- Keep OAuth credentials and all upstream calls server-side.
- Finish each story's independent test criteria before moving its checkpoint to complete.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after repository layout is agreed.
- T007, T012, and T013 can run in parallel after setup; T014 can proceed independently of backend foundation.
- In US1, T017–T021 are separate test files; T022 and T023 are independent service files; T029 and T030 can be developed in separate frontend files.
- In US2, T033 and T034 are independent tests; T037 can be built independently of backend service work.
- In US3, T040 and T041 are independent tests; T045 and T046 are independent UI components.
- US2 and non-persistence portions of US3 may be developed in parallel once foundational models and API contracts are stable; persistent-session work remains gated by T042.

## Parallel Example: User Story 1

```text
Task: T022 Parse unified diffs and map changed lines in backend/app/services/diff_parser.py
Task: T023 Retrieve GitHub PR metadata and diff in backend/app/services/github_client.py
Task: T029 Build first-review privacy-consent gate in frontend/src/components/PrivacyConsent.tsx
Task: T030 Build review form and results states in frontend/src/features/review/ReviewPage.tsx
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation, including GitHub OAuth and account isolation.
3. Complete Phase 3 review submission, retrieval, privacy disclosure, and validated findings.
4. Independently test GitHub PR and pasted-diff reviews, no-findings output, invalid input, oversized diff rejection, and upstream/model failures.
5. Demonstrate P1 before beginning chat or persistent-session features.

### Incremental Delivery

1. Deliver Setup + Foundation.
2. Deliver US1 as the review MVP.
3. Add US2 streaming grounded chat.
4. Resolve retention policy, then add US3 saved sessions, navigation, filters, and export.
5. Complete accessibility, security, evaluation, and measured performance validation.

## Notes

- Every task uses the required checkbox, sequential ID, optional `[P]`, required user-story label in story phases, and exact file path.
- `[P]` marks tasks that touch independent files and have no dependency on unfinished work in their phase.
- User stories are independently validated after shared prerequisites; US2/US3 reuse review data but are not prerequisites for the P1 MVP.
- `plan.md` is currently an unfilled scaffold; complete `/speckit-plan` design artifacts and confirm the proposed file layout before implementation.
