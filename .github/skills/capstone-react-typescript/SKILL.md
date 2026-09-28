---
name: capstone-react-typescript
description: 'Implement, debug, or test the CAPSTONE pull request reviewer frontend in React and TypeScript with Vite. Use for review/chat flows, diff and findings panels, API/SSE integration, accessibility, frontend state, or UI tests.'
argument-hint: 'Describe the frontend feature, bug, or test to address.'
---

# CAPSTONE React and TypeScript Frontend

Implement frontend changes for the CAPSTONE pull request reviewer while preserving the PRD's product scope and backend contracts.

## Workflow

1. Read the relevant requirements in `prd.md` and the CAPSTONE project instructions. Treat the PRD as authoritative; do not decide its open product questions by assumption.
2. Inspect the existing frontend structure, package scripts, API types, and established component/state conventions before editing. If the frontend is not yet scaffolded, do not invent a new architecture or dependencies without need; keep the requested implementation aligned with React, TypeScript, and Vite.
3. Trace the user flow and data contract before changing UI behavior. The app accepts a GitHub PR URL or unified diff, displays a summary/findings and diff, supports severity/category filters, highlights finding locations, and grounds chat follow-ups in the current review. Follow the APIs and event format actually present in the project.
4. Keep GitHub credentials, Google AI Studio credentials, and direct third-party service access out of browser code. Call the FastAPI service using its documented interface. Never put secrets in client environment variables, logs, or rendered errors.
5. Implement explicit loading, error, empty, and success states. Preserve SSE streaming for chat when changing that flow; handle connection failure and cancellation without presenting partial output as a completed response.
6. Maintain keyboard navigation, visible focus, semantic controls, and WCAG AA contrast. Ensure that selecting a finding can navigate to/highlight its diff location and that filters remain usable by keyboard and assistive technology.
7. Add or update focused tests for the changed behavior, including invalid or missing API data, stream errors, loading/empty states, and finding-to-diff navigation where relevant. Use the repository's existing test tools and scripts.
8. Run the narrowest relevant tests and available typecheck/lint/build checks. Report what was run and any failures; do not claim accessibility, performance, or quality targets without evidence.

## Guardrails

- Do not add approval, merge, or PR-comment posting behavior unless explicitly requested; comment posting is a stretch requirement.
- Do not retain review code on the client beyond the session unless the user explicitly saves the session through the product flow.
- Show the required notice that code is sent to Google AI Studio before the user's first review; do not hide or weaken the disclosure.
- Keep UI feedback tied to API data. Do not fabricate findings, file paths, line references, or chat context.
- Ask before making product-level decisions about account/authentication approach, maximum PR size, custom team rules, or model self-hosting.
