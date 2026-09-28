# CAPSTONE Pull Request Reviewer

A GitHub PR review assistant that summarizes diffs, returns evidence-grounded findings, and supports follow-up chat. The current implementation supports GitHub OAuth, PR URLs and unified diffs, review summaries/findings, and streamed chat for the active session.

## Requirements

- Python 3.11 or newer (developed with Python 3.14)
- Node.js 22 or newer and npm
- A GitHub OAuth application configured with callback URL `http://localhost:8000/api/auth/callback`
- A Google AI Studio API key for server-side inference

For a full fresh-machine setup walkthrough, see [SETUP.md](SETUP.md).

## Local setup

1. Create `backend/.env` from `backend/.env.example` and set OAuth client ID/secret, model API key, and secure random values for `SESSION_SECRET_KEY` and `TOKEN_ENCRYPTION_KEY`. Never commit this file or place credentials in frontend environment variables.
2. Generate a Fernet-compatible token encryption key in the Python environment with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`; store the output in `TOKEN_ENCRYPTION_KEY`.
3. Install and start the API:

   ```sh
   cd backend
   python -m pip install -e '.[dev]'
   uvicorn app.main:app --reload --port 8000
   ```

4. In a second terminal, install and start the frontend:

   ```sh
   cd frontend
   cp .env.example .env
   npm ci
   npm run dev
   ```

5. Open the Vite URL (normally `http://localhost:5173`) and sign in with GitHub. By default, OAuth uses least-privilege `read:user user:email` scopes; the app currently reviews public pull requests accessible to that account.

## Configuration and privacy

- GitHub OAuth credentials, encrypted access tokens, and the Google AI Studio API key are handled server-side.
- `TOKEN_ENCRYPTION_KEY` must remain stable across restarts to decrypt stored GitHub credentials.
- `SESSION_SECRET_KEY` must remain stable across restarts to preserve signed login sessions. Production deployments must set both keys and enable secure cookies behind HTTPS.
- The frontend discloses Google AI Studio processing before a first review and requires consent before submission.
- Unsaved diff/review/chat data is held in process memory only and is cleared on sign-out or when the user starts a new review; idle active reviews expire after 30 minutes. SQLite currently stores account credentials and daily usage counters only.
- The product does not execute submitted code, post comments, approve PRs, or merge branches.
- Saved-session persistence, retention, and deletion are not implemented pending the product retention decision. A single-process API is required for transient review state in this version; multi-worker deployment needs shared temporary session storage before launch.

## Validation

From the repository root, run the backend and frontend checks:

```sh
cd backend && pytest -q && ruff check app tests && ruff format --check app tests
cd ../frontend && npm test && npm run build && npm run lint
```

The tests mock upstream services and require no production credentials. Live OAuth/AI flows need the local environment variables and a registered GitHub OAuth app. Performance targets require explicit measurement with a representative review set; they are not inferred from unit tests.
