# Feature Specification: Pull Request Reviewer

**Feature Branch**: `001-pull-request-reviewer`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Create the CAPSTONE pull request reviewer chatbot described in the project PRD, governed by the project constitution."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a Pull Request (Priority: P1)

A developer submits a GitHub pull request link or a unified diff and receives a concise summary of the change and a prioritized set of actionable findings. Each finding identifies its severity, category, affected file and line range, explains the concern, and suggests a fix when possible.

**Why this priority**: A first-pass review is the product's primary value and must stand alone before follow-up features are added.

**Independent Test**: Submit a representative pull request or diff containing known issues and verify that the user receives a summary and evidence-grounded findings, including a useful empty result when no issues are identified.

**Acceptance Scenarios**:

1. **Given** a supported GitHub pull request link and the required access, **When** the developer requests a review, **Then** the product presents a summary and findings tied to changed files and valid line ranges.
2. **Given** a valid unified diff, **When** the developer submits it for review, **Then** the product reviews it without requiring a hosted pull request.
3. **Given** a pull request with no actionable issues, **When** the review completes, **Then** the product presents the summary and clearly states that no findings were identified.
4. **Given** a pull request whose changes span multiple files or exceed the review service's processing capacity, **When** it is reviewed, **Then** the product processes eligible changes in bounded portions or gives a clear explanation that it cannot complete the review.

---

### User Story 2 - Ask Follow-up Questions (Priority: P2)

A developer asks questions about the reviewed changes, findings, risks, or a possible fix and receives a response grounded in that review. Responses appear progressively, and the conversation remains associated with its review session.

**Why this priority**: Conversation adds context-aware explanations and makes findings more useful, but depends on a completed review.

**Independent Test**: Open an existing review, ask about a finding and then ask about the riskiest change; verify that responses refer to the review evidence and that the conversation is available in the session.

**Acceptance Scenarios**:

1. **Given** a completed review, **When** the user asks why a finding is risky, **Then** the response explains the risk using the diff and finding as evidence.
2. **Given** a review session with conversation history, **When** the user asks a follow-up, **Then** the response uses the relevant prior context.
3. **Given** the response service fails or is interrupted, **When** the user is waiting for an answer, **Then** the product reports the interruption and does not present an incomplete response as complete.

---

### User Story 3 - Revisit and Share a Review (Priority: P3)

A developer saves a review session, returns to it later, and exports its review as a readable Markdown document. Within a review, the developer can inspect the changes, filter findings, and navigate from a finding to its cited code.

**Why this priority**: Saved sessions, export, and review navigation support ongoing work, while the core review and chat provide value on their own.

**Independent Test**: Save a completed review, reopen it, filter its findings, navigate to a cited diff location, and export a Markdown report that matches the displayed review.

**Acceptance Scenarios**:

1. **Given** a completed review, **When** the user explicitly saves it, **Then** its pull request reference, findings, and conversation are available in the user's session list.
2. **Given** a saved session, **When** the user reopens it, **Then** the saved review and conversation are restored.
3. **Given** visible findings and a diff, **When** the user selects a finding, **Then** the relevant changed code is highlighted or brought into view.
4. **Given** a review with findings, **When** the user filters by severity or category, **Then** only matching findings are shown and the user can restore the full set.
5. **Given** a completed review, **When** the user exports it, **Then** the resulting Markdown includes the summary and findings in a readable form.

---

### Edge Cases

- The pull request link is malformed, points to an unsupported host, or cannot be accessed with the supplied credentials.
- The user submits an empty, malformed, truncated, or unsupported diff.
- A diff includes deleted files, renames, binary content, generated files, or lockfiles; excluded files are identified or otherwise clearly handled.
- A finding cites a file or line range not present in the submitted changes; it is rejected or corrected before display.
- The diff is too large for available review capacity, or only some files can be processed.
- The upstream source or review service times out, rate-limits the request, returns invalid output, or becomes unavailable.
- The user declines the first-review notice, cancels a request, reloads during streaming, or loses connectivity.
- A session is not saved; submitted code must not remain available after the session ends.
- A saved session is missing or no longer accessible when the user attempts to reopen it.
- Filters match no findings, or the review contains no findings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST accept a GitHub pull request link or a raw unified diff as a review input.
- **FR-002**: For a pull request link, the product MUST retrieve the pull request title, description, author, changed files, and diff using GitHub access authorized by the user through GitHub OAuth.
- **FR-003**: The product MUST explain invalid, inaccessible, unsupported, or incomplete review inputs in user-understandable terms and allow correction or retry.
- **FR-004**: The product MUST present a summary describing the pull request's purpose, key changes, and affected areas.
- **FR-005**: Each finding MUST include severity (critical, major, minor, or nit), category, changed file, line range, title, explanation, and a suggested fix when one can be supported.
- **FR-006**: The product MUST validate that each finding's cited file and line range are grounded in the submitted diff before presenting it as a finding.
- **FR-007**: The product MUST group or order findings so that higher-severity issues are readily distinguishable from lower-severity issues.
- **FR-008**: The product MUST process large reviews in bounded portions and combine their results into a coherent review. It MUST skip lockfiles, binary files, and generated files by default.
- **FR-009**: The product MUST provide a chat experience for follow-up questions grounded in the current pull request diff, review findings, and relevant session conversation.
- **FR-010**: The product MUST present chat responses progressively and MUST indicate when an answer fails or is interrupted.
- **FR-011**: The product MUST maintain conversation history for a review session.
- **FR-012**: The product MUST display a review workspace containing the summary, findings, relevant diff, and chat, with clear loading, error, empty, and completed states.
- **FR-013**: The user MUST be able to select a finding and navigate to or highlight its cited code in the diff.
- **FR-014**: The user MUST be able to filter findings by severity and category and clear those filters.
- **FR-015**: The product MUST inform the user before their first review that submitted code is sent to Google AI Studio for inference. A declined notice MUST prevent review submission.
- **FR-016**: The product MUST NOT retain submitted code beyond the active session unless the user explicitly saves the session.
- **FR-017**: The user MUST be able to explicitly save a review session and later list and reopen saved sessions. A saved session MUST include the pull request reference, findings, and chat history.
- **FR-018**: The user MUST be able to export a completed review as readable Markdown.
- **FR-019**: The product MUST NOT execute submitted code or its tests.
- **FR-020**: The product MUST NOT approve, merge, or post comments to a pull request by default. Posting selected findings is outside the initial release scope and requires an explicit product decision before implementation.
- **FR-021**: The product MUST protect GitHub and Google AI Studio credentials from browser exposure and logs, restrict cross-origin access to the frontend origin, and use least-privilege GitHub access.
- **FR-022**: The product MUST handle upstream timeouts and rate limits with bounded retries and increasing delays, and MUST provide a clear failure state when retries are exhausted.
- **FR-023**: The product MUST provide keyboard-operable controls, visible focus, and sufficient text and control contrast for users with disabilities.
- **FR-024**: The product MUST enforce a maximum review size of 1,000 changed lines per submitted pull request or diff and per-user request limits. Reviews exceeding the size limit MUST be rejected with an actionable explanation; the product MUST NOT present a partial review as complete.
- **FR-025**: The product MUST support separate user accounts authenticated through GitHub OAuth and MUST isolate each user's credentials, saved sessions, and request limits from other users.

### Key Entities *(include if feature involves data)*

- **Pull Request Review**: A review request and result, including its pull request reference or submitted diff, summary, eligible changed files, and findings.
- **Finding**: An actionable review observation containing severity, category, changed-file location, title, explanation, and suggested fix.
- **Review Session**: A review and its associated conversation, optionally saved for later access.
- **Chat Message**: A user question or assistant response associated with a review session and grounded in the review context.
- **User Access Credential**: A user-provided credential used to retrieve a GitHub pull request; it is sensitive and must not be exposed or logged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For supported reviews of pull requests with up to 500 changed lines, at least 90% complete within 60 seconds under the agreed test conditions.
- **SC-002**: In a representative evaluation set, fewer than 3% of displayed finding locations refer to a file or line not present in the submitted changes.
- **SC-003**: At least 60% of users who rate a finding mark it useful.
- **SC-004**: At least 90% of first-time users who begin with a valid input can identify the review summary and open a cited finding without assistance.
- **SC-005**: In evaluation runs, at least 98% of generated reviews are available in the required structured form after validation or the defined repair attempt.
- **SC-006**: Users can receive the beginning of a follow-up answer within 3 seconds for at least 90% of supported requests under the agreed test conditions.
- **SC-007**: Every saved session in a retention verification sample can be reopened with its associated findings and conversation intact; unsaved code is unavailable after its session ends.
- **SC-008**: In account-isolation tests, no user can retrieve another user's credentials, saved sessions, or request-limit state.

## Assumptions

- The initial product supports GitHub only; other source-hosting services are out of scope.
- Users authorize GitHub access through GitHub OAuth. Resulting credentials are used only on the server and are not logged or returned to the browser.
- Review inference uses Google AI Studio and the configured Gemma model. The interface clearly discloses this before a user's first review.
- The initial review experience includes pull request summary, findings, diff navigation, filtering, and chat; selected-finding comment posting is excluded from the initial release.
- The user explicitly saves a session to retain it beyond the active session. Session retention duration and deletion controls are not specified in the PRD and require product definition before persistent-session release.
- The initial release supports separate user accounts through GitHub OAuth, as selected during planning clarification.
- The 1,000-line limit counts changed lines in the submitted pull request or unified diff. The existing under-60-second performance target continues to apply to pull requests with up to 500 changed lines.
- If an input exceeds the 1,000 changed-line limit, the product refuses it with an actionable explanation rather than implying that a partial review is complete.
- Users can access the product using a modern browser and a network connection; offline review is out of scope.
