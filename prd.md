Product Requirements Document: Pull Request Reviewer Chatbot
Status: Draft v0.1 | Owner: TBD | Last updated: 28 Sep 2026

1. Overview
A chatbot that helps developers review pull requests. A user connects a PR (via URL or pasted diff), and the assistant summarizes the change, flags bugs, security and style issues, and answers follow-up questions about the code in a conversational interface.

Tech stack

Layer	Choice
Frontend	React + TypeScript
API	FastAPI
Backend	Python
AI model	gemma-4-26b-a4b-it via Google AI Studio
2. Problem Statement
Code review is slow and inconsistent. Reviewers are overloaded, large diffs hide bugs, and authors wait hours or days for feedback. Existing tools either post noisy automated comments or lack context for follow-up questions.

3. Goals and Non-Goals
Goals

Deliver a useful first-pass review of a PR in under 60 seconds for typical diffs.
Let users ask follow-up questions ("Why is this a risk?", "Suggest a fix for file X").
Produce structured, actionable feedback grouped by severity.
Non-Goals (v1)

Auto-merging or approving PRs.
Running the code or tests.
Supporting non-GitHub platforms (GitLab, Bitbucket) at launch.
Fine-tuning the model.
4. Target Users
Primary: Individual developers wanting a quick self-review before requesting human review.
Secondary: Reviewers and tech leads who want a fast summary of large PRs.
5. User Stories
As a developer, I paste a PR URL and get a summary of what changed and why it matters.
As a developer, I get a list of issues (bugs, security, performance, style, missing tests) with file and line references.
As a reviewer, I ask "What are the riskiest changes here?" and get a ranked answer.
As a developer, I ask the bot to suggest a code fix for a flagged issue.
As a user, I can revisit a previous review session.
As a user, I can optionally post selected findings back to the PR as comments.
6. Functional Requirements
6.1 PR Ingestion
FR-1: Accept a GitHub PR URL or a raw unified diff.
FR-2: Fetch PR metadata (title, description, author, changed files, diff) through the GitHub API using a user-provided token.
FR-3: Chunk large diffs by file and hunk to fit the model's context window; skip lockfiles, binaries and generated files by default.
6.2 Review Engine
FR-4: Generate a PR summary (purpose, key changes, affected areas).
FR-5: Generate findings, each with: severity (critical / major / minor / nit), category, file, line range, explanation, and suggested fix.
FR-6: Return findings as validated structured JSON (Pydantic schema) so the UI can render them reliably.
FR-7: For multi-chunk PRs, run per-file reviews and a final synthesis pass.
6.3 Chat
FR-8: Conversational Q&A grounded in the PR diff and prior findings.
FR-9: Streaming responses (SSE) for a responsive feel.
FR-10: Maintain conversation history per session.
6.4 Frontend
FR-11: Chat panel plus a side panel showing the diff and findings.
FR-12: Clicking a finding highlights the relevant code in the diff view.
FR-13: Filter findings by severity and category.
FR-14: Loading, error and empty states for every flow.
6.5 Session and Output
FR-15: Persist sessions (PR reference, findings, chat history).
FR-16: Export a review as Markdown.
FR-17 (stretch): Post selected findings as GitHub PR review comments.
7. Non-Functional Requirements
Performance: First streamed token within 3 s; full review of a ≤500-line diff within 60 s.
Reliability: Graceful handling of API rate limits and timeouts, with retry and exponential backoff.
Security: GitHub tokens and the Google AI Studio API key are never logged or exposed to the frontend; all secrets live in server-side environment variables; CORS restricted to the frontend origin.
Privacy: Code is sent to Google AI Studio for inference. Users must be told this clearly before their first review. No code retained beyond the session unless the user saves it.
Cost control: Per-user rate limits and a maximum diff size.
Accessibility: Keyboard navigable UI, WCAG AA contrast.
8. System Architecture
React + TS (Vite)
      │  REST + SSE
      ▼
FastAPI  ── routers: /reviews, /chat, /sessions
      │
      ├── GitHub client (httpx)      → GitHub API
      ├── Diff parser / chunker
      ├── Review service (prompts + schema validation)
      ├── LLM client                 → Google AI Studio (Gemma)
      └── Storage (SQLite → Postgres later)
Proposed API
Method	Endpoint	Purpose
POST	/api/reviews	Start a review from PR URL or diff
GET	/api/reviews/{id}	Get summary and findings
POST	/api/reviews/{id}/chat	Send a message; streams the reply
GET	/api/sessions	List past sessions
POST	/api/reviews/{id}/export	Export as Markdown
GET	/api/health	Health check
Finding schema (example)
{
  "severity": "major",
  "category": "security",
  "file": "app/auth.py",
  "line_start": 42,
  "line_end": 48,
  "title": "Unsanitized input in SQL query",
  "explanation": "...",
  "suggested_fix": "..."
}
9. AI and Prompting Considerations
Use a system prompt defining the reviewer role, severity rubric, and strict JSON output format.
Include PR title and description as context so feedback reflects intent.
Use low temperature for findings; slightly higher for conversational answers.
Validate output with Pydantic; on failure, retry once with a repair prompt.
Ground every finding in a real file and line from the diff to limit hallucinated locations.
Verify the model's context limit and rate limits in Google AI Studio and size chunks accordingly.
Build a small evaluation set of PRs with known issues to track precision and recall across prompt changes.
10. Success Metrics
Metric	Target
Time to first review	< 60 s (p90) for ≤500-line diffs
Finding usefulness (thumbs up rate)	≥ 60%
Valid structured output rate	≥ 98%
Hallucinated file/line references	< 3%
Weekly returning users	Track from launch
11. Milestones
Phase	Scope
M1: Prototype	FastAPI endpoint, diff input, Gemma call, JSON findings, CLI/Swagger testing
M2: MVP	React chat UI, diff viewer, findings panel, GitHub URL ingestion, streaming
M3: Beta	Sessions, Markdown export, chunking for large PRs, rate limiting, eval set
M4: Launch	Post comments to GitHub, auth, deployment, docs
12. Risks and Mitigations
Risk	Mitigation
Hallucinated or low-quality findings	Schema validation, line grounding, eval set, user feedback buttons
Context limit exceeded on large PRs	Chunking, file filtering, synthesis pass
Free-tier rate limits on AI Studio	Queueing, backoff, request caps
Sensitive code sent to a third party	Clear consent notice; option to self-host the model later
GitHub token misuse	Least-privilege (read-only) tokens, server-side storage only
13. Open Questions
Will v1 require user accounts, or is it a single-user tool?
Should GitHub OAuth replace personal access tokens?
What is the maximum supported PR size?
Should custom review rules (team style guides) be supported?
Is self-hosting the model a future requirement?