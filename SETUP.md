# CAPSTONE Setup Guide

Use this guide to set up the project on a new computer. The commands below assume Linux or macOS; Windows instructions are included near the end.

## Requirements

- Git
- Python 3.11 or newer
- Node.js 22 or newer, including npm
- A GitHub OAuth App
- A Google AI Studio API key

## 1. Get the project

Clone the repository, then change into its directory:

```sh
git clone https://github.com/namithvishwamithra/Capstone_Pull_Request_Reviewer_Chatbot.git
cd Capstone_Pull_Request_Reviewer_Chatbot
```

## 2. Configure backend credentials

Copy the example file and edit the copy:

```sh
cp backend/.env.example backend/.env
```

Create a GitHub OAuth App in GitHub **Settings → Developer settings → OAuth Apps** with:

- **Homepage URL:** `http://localhost:5173`
- **Authorization callback URL:** `http://localhost:8000/api/auth/callback`

Create a Google AI Studio API key at <https://aistudio.google.com/app/apikey>.

Set these values in `backend/.env`:

- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` from the OAuth App
- `GOOGLE_AI_STUDIO_API_KEY` from Google AI Studio
- `SESSION_SECRET_KEY`, generated with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`
- `TOKEN_ENCRYPTION_KEY`, generated after installing backend requirements in step 3 with `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`

Keep the session and encryption keys private and stable across restarts. Never commit `backend/.env`, put provider credentials in frontend files, or paste secrets into chat. The `.gitignore` excludes local environment files.

For local development, leave `COOKIE_SECURE=false` and `PRODUCTION=false`. Do not use those development settings for an HTTPS deployment.

## 3. Install backend dependencies

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Copy the generated Fernet key into `TOKEN_ENCRYPTION_KEY` in `backend/.env`. Return to the repository root after configuring it:

```sh
cd ..
```

## 4. Install frontend dependencies

```sh
cd frontend
npm ci
cd ..
```

The frontend uses the Vite development proxy by default; no frontend secret or `.env` file is needed for the local setup.

## 5. Start the application

From the repository root:

```sh
./run.sh
```

Open <http://localhost:5173>. Use `localhost` consistently for the browser and OAuth callback; do not switch between `localhost` and `127.0.0.1`, because their browser cookies are separate. Press Ctrl+C in the launcher terminal to stop both services.

Before the first review, accept the privacy notice: submitted code is sent to Google AI Studio. Reviews are held in the active process session; the app does not execute submitted code.

## Windows

`run.sh` requires Bash. On Windows, use WSL to follow the Linux steps, or start the services in separate PowerShell terminals:

1. Backend: create and activate a virtual environment (`py -3.11 -m venv .venv`, then `.\.venv\Scripts\Activate.ps1`), install dependencies with `python -m pip install -e ".[dev]"`, then run `uvicorn app.main:app --reload --port 8000` from `backend`.
2. Frontend: run `npm ci` and `npm run dev` from `frontend`.
3. Visit <http://localhost:5173>.

## Checks

With the backend environment active, run the tests and quality checks from the repository root:

```sh
cd backend
pytest -q
ruff check app tests
ruff format --check app tests
cd ../frontend
npm test
npm run build
npm run lint
```

## Troubleshooting

- **GitHub says OAuth state is invalid:** start again from <http://localhost:5173> and keep the callback at `http://localhost:8000/api/auth/callback`. Do not open the app as `127.0.0.1`.
- **`run.sh` reports missing dependencies:** install backend requirements in step 3 and run `npm ci` in `frontend`.
- **A review exceeds the line limit:** the default `MAX_CHANGED_LINES` is 1000. A local override can be set in `backend/.env`; larger reviews may take longer and use more AI quota, and can still encounter provider request or output limits.
- **Credentials or login fail:** verify the OAuth callback URL exactly matches the app, and make sure the Google API key is set only in `backend/.env`.
