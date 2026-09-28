# Implementation Plan: Pull Request Reviewer

**Branch**: `001-pull-request-reviewer` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-pull-request-reviewer/spec.md`

## Summary

Build an authenticated GitHub pull-request review chatbot that accepts a GitHub PR URL or unified diff, presents a concise summary and validated actionable findings, and supports grounded streaming follow-up chat. The implementation follows the selected React + TypeScript + Vite frontend and Python + FastAPI backend, uses GitHub OAuth for separate accounts, calls Google AI Studio only from the server, validates findings with Pydantic, and uses SQLite as the initial storage choice. The P1 review flow is the MVP. Persistent saved-session work remains gated on a user decision about retention and deletion.

## Technical Context

**Language/Version**: Python 3.14.4 in the current environment (target Python 3.11+); TypeScript with Node.js 22.22.2 in the current environment

**Primary Dependencies**: FastAPI, Pydantic, httpx, Authlib, React, Vite, TypeScript; Gemma `gemma-4-26b-a4b-it` through Google AI Studio

**Storage**: SQLite for account data and explicitly saved review sessions; transient unsaved review code and conversation context must not be durably stored

**Testing**: pytest for backend; Vitest and React Testing Library for frontend; mocked upstream clients for GitHub and Google AI Studio

**Target Platform**: Modern desktop/mobile browsers and a Linux-hosted Python API service

**Project Type**: Web application with separate `backend/` and `frontend/` projects

**Performance Goals**: At least 90% of supported reviews with up to 500 changed lines complete within 60 seconds; first follow-up response content within 3 seconds for at least 90% of supported requests, subject to measured test conditions

**Constraints**: Reject PR/diff input over 1,000 changed lines; GitHub and AI credentials are server-only; disclose Google AI Studio processing before first review; bounded upstream retries; no submitted code execution; no comments, approvals, or merges; accessible keyboard operation and WCAG AA contrast; session-retention policy must be decided before persistent saved-session implementation

**Scale/Scope**: Separate GitHub OAuth accounts; GitHub only; initial review capped at 1,000 changed lines; three user stories (review, streaming chat, saved/reopened/exported sessions)

## Constitution Check

- **Diff-grounded reviews**: Pass. Validate model output and every changed-file line range before returning findings.
- **Privacy and security**: Pass with implementation gates. Server-side secrets only, first-review disclosure and consent, restrictive CORS, least-privilege GitHub scopes, no execution, and no durable storage of unsaved code.
- **Human-controlled GitHub actions**: Pass. No posting, approving, or merging in v1.
- **Contract-first architecture**: Pass. React/TypeScript/Vite, Python/FastAPI, REST/SSE, Pydantic validation, and coordinated API schemas.
- **Evidence-based quality**: Pass with verification required. Focused tests and measurable validation are planned; no target is claimed without evidence.
- **Open product decision**: Saved-session retention/deletion is unresolved. Do not implement persistent saved-session behavior (US3 storage/UI) until the user decides it and the spec is updated.

## Project Structure

### Documentation (this feature)

```text
specs/001-pull-request-reviewer/
├── plan.md
├── spec.md
├── tasks.md
├── checklists/requirements.md
├── research.md                 # Optional planning artifact; not present yet
├── data-model.md               # Optional planning artifact; not present yet
├── quickstart.md               # Validation guide produced during polish
└── contracts/                  # API contract documents produced during planning
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── .env.example
├── app/
│   ├── main.py
│   ├── api/                    # auth, reviews, chat, sessions, health
│   ├── core/                   # settings and safe errors
│   ├── db/                     # SQLite connections and schema
│   ├── schemas/                # Pydantic request/response contracts
│   └── services/               # OAuth, GitHub, diff, model, review, chat, storage
└── tests/

frontend/
├── package.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   ├── features/               # auth, review, chat, sessions
│   └── lib/                    # typed API client and shared types
└── tests/
```

**Structure Decision**: Use the two-project web-application layout above. It matches the PRD architecture and preserves a server-only boundary for OAuth, GitHub API calls, Google AI Studio credentials, validation, and storage. The workspace currently contains product/spec documentation only; implementation will scaffold this layout.

## Complexity Tracking

No constitution violations are proposed. Separate frontend and backend are required by the PRD; no additional deployable service is planned. Saved-session retention remains an explicit blocker rather than a justified assumption.
