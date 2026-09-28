<!--
Sync Impact Report
Version change: unratified scaffold → 1.0.0 (initial project constitution)
Modified principles: five scaffold placeholders resolved as Diff-Grounded Reviews,
Privacy and Security, Human-Controlled GitHub Actions, Contract-First Architecture,
and Evidence-Based Quality.
Added sections: Technology and Product Boundaries; Development and Review Workflow.
Removed sections: none.
Follow-up TODO: confirm the original ratification date.
This report is temporary and should be removed before committing the amended constitution.
-->

# CAPSTONE Pull Request Reviewer Constitution

## Core Principles

### I. Diff-Grounded, Actionable Reviews
Every review summary and finding MUST be grounded in the submitted pull request metadata
and diff. Each finding MUST use a supported severity and category and cite a real changed
file and valid line range. Findings MUST explain the risk and provide an actionable fix
when one can be supported by the evidence. Model output MUST be validated against the
backend schema before it is shown as structured review data. This limits hallucinated,
unverifiable feedback.

### II. Privacy and Security by Default
Credentials MUST remain in server-side environment configuration and MUST NOT be exposed
to the browser or written to logs. CORS MUST be restricted to the frontend origin; GitHub
access MUST use least privilege. Before a user's first review, the product MUST disclose
that code is sent to Google AI Studio. Review code MUST NOT be retained beyond the session
unless the user saves that session. Submitted code and tests MUST never be executed.
These rules protect user code, credentials, and trust.

### III. Human-Controlled GitHub Actions
The product MUST NOT approve, merge, or post review comments to a pull request unless the
user explicitly requests the applicable behavior. Posting selected findings remains a
stretch capability, not default behavior. GitHub operations MUST be attributable to
explicit user intent and constrained by least-privilege credentials. The user remains the
decision-maker for code changes and review outcomes.

### IV. Contract-First Architecture
The frontend MUST use React, TypeScript, and Vite; the API/backend MUST use Python and
FastAPI. Browser-to-server communication MUST follow documented REST and SSE contracts.
Review findings and other structured model output MUST be validated with Pydantic models.
Contract changes MUST be coordinated across callers, server behavior, and tests. This
keeps the independently developed frontend and backend interoperable.

### V. Evidence-Based Quality
Behavior changes MUST include focused tests for relevant contracts and risks, particularly
input validation, finding locations, secret handling, and upstream failure/retry paths.
Frontend changes MUST preserve keyboard navigation, accessible contrast, and clear
loading, error, and empty states. Claims that performance, reliability, accessibility, or
quality targets are met MUST be supported by measurements or validation results. Tests
and evidence are required to keep quality claims trustworthy.

## Technology and Product Boundaries

- The review model is `gemma-4-26b-a4b-it` through Google AI Studio. Model access MUST be
  implemented server-side. Review generation SHOULD use low temperature; conversational
  answers may use the separately configured chat settings.
- The product accepts GitHub pull request URLs or raw unified diffs. GitHub is the only
  supported hosting platform at launch. Large diffs MUST be processed by file and hunk;
  generated files, binaries, and lockfiles MUST be skipped by default.
- Structured findings MUST include severity, category, file, line range, title,
  explanation, and suggested fix as defined by the API contract. Every referenced file
  and line MUST be validated against the submitted diff.
- Chat answers MUST be grounded in the current diff and prior findings. Chat streaming
  MUST remain available through SSE. Upstream timeouts and rate limits MUST be handled
  with bounded retries and exponential backoff.
- SQLite is the initial storage target; a move to Postgres is future work, not permission
  to silently change the storage choice. Saved sessions may retain the PR reference,
  findings, and chat history; unsaved code MUST not outlive the session.
- Auto-merge, auto-approval, executing submitted code, and model fine-tuning are outside
  v1 scope. Questions about accounts, OAuth versus personal tokens, maximum PR size,
  custom team rules, or model self-hosting remain undecided and require a product decision.

## Development and Review Workflow

- Before changing behavior, consult the relevant product requirements and this
	constitution. Product-level changes MUST update the specification before they are
	implemented.
- Before implementation, inspect existing module boundaries, API contracts, dependencies,
	and test conventions. Do not introduce technologies or dependencies without a concrete
	need and compatibility review.
- For changes crossing the frontend/backend boundary, update or verify both sides of the
	contract and add focused integration coverage where practical. Failure paths, malformed
	upstream responses, and cancellation of streamed responses MUST be considered when
	relevant.
- Pull request review MUST verify constitution compliance, security and privacy impact,
	diff-grounded finding locations, accessibility impact, and test evidence. Unmet
	performance or quality targets MUST be reported as unverified rather than asserted.

## Governance

This constitution governs CAPSTONE product and engineering decisions. The PRD supplies
product requirements and may be refined only through an explicit product decision; an
implementation detail MUST NOT silently resolve an open product question. The workspace
instructions at `.github/instructions/capstone-reviewer.instructions.md` provide
operational guidance and MUST remain consistent with this constitution.

Amendments MUST state the rationale, affected principles or sections, compatibility
impact, and any required follow-up. Changes require project-owner review before adoption.
The constitution version MUST follow semantic versioning: MAJOR for incompatible
governance changes, MINOR for new or materially expanded principles or sections, and
PATCH for clarifications that do not change obligations. Every adopted amendment MUST
update the last-amended date and version. Feature specifications, plans, implementation
reviews, and pull requests MUST check compliance; any conflict MUST be resolved by
revising the proposal or formally amending this constitution, not by ignoring it.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-09-28
