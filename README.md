# X-Ray Management API

API backend for managing radiographic records of patients.

This project is being built with Flask and follows a layered architecture.

## Tech Stack

- Flask
- Flask-SQLAlchemy
- Alembic
- SQLite
- Pydantic
- Authlib + PyJWT
- Cloudinary
- Flasgger (Swagger)

## Current Architecture

- `app/routers`: HTTP endpoints (in progress)
- `app/services`: business logic and integrations (in progress)
- `app/repositories`: data access layer (in progress)
- `app/schemas`: request/response validation with Pydantic (in progress)
- `app/models`: SQLAlchemy models (ready)
- `app/core`: shared config and security utilities (partially ready)
- `migrations`: Alembic environment and migration history (ready)

## Technical Decisions

1. **Layered architecture**: routers only handle HTTP concerns, services hold business rules, repositories access DB.
2. **SQLite for local/dev**: simple setup for first delivery and exam demo.
3. **Cloudinary for image storage**: API does not serve binary images directly.
4. **JWT-based protection**: protected routes validate bearer tokens.
6. **Google SSO user model**: a local `users` table stores `google_id`, `email`, `name`, and `created_at`.
7. **Swagger docs with Flasgger**: quick contract visibility for team and evaluators.

## Environment Variables

Create a `.env` file in the project root using `.env.example` as template:

```env
DATABASE_URL=sqlite:///./xray_database.db
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_FOLDER=xray_records
CLOUDINARY_UPLOAD_TYPE=authenticated
CLOUDINARY_SIGNED_URL_TTL_SECONDS=600
SECURE_IMAGE_TOKEN_TTL_SECONDS=600
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/google/callback
GOOGLE_OAUTH_SCOPES=openid email profile
GOOGLE_OAUTH_TIMEOUT_SECONDS=10
```

### Google SSO Setup

1. In Google Cloud Console, create OAuth 2.0 Client ID (Web application).
2. Add authorized redirect URI:

```text
http://127.0.0.1:5000/auth/google/callback
```

3. Set these values in `.env`:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/google/callback
```

4. Restart API server.

5. Verify configuration:

```bash
curl -i "http://127.0.0.1:5000/auth/google/login?mode=json"
```

- If configured: HTTP 200 and JSON with `authorization_url`.
- If not configured: HTTP 500 and `missing_settings` list.

## Setup

### Manage with `uv`

This project now uses `pyproject.toml` and `uv` for dependency / environment management.

1. Install `uv` globally or in a bootstrap environment:

```bash
python -m pip install --upgrade pip
python -m pip install uv
```

2. Install the project dependencies:

```bash
uv install
```

3. Create or refresh the lock file:

```bash
uv lock
```

4. Run the API using the managed environment:

```bash
uv run python -m app.main
```

If you want to get a shell inside the managed environment:

```bash
uv shell
```

## Run with `uv`

Use `uv` to sync, lock, and execute the project without a manual virtual environment.

```bash
uv lock
uv sync
uv run python -m app.main
```

If you prefer a shell inside the managed environment:

```bash
uv shell
```

### NixOS / flake users

If you use Nix, enter the dev shell first:

```bash
nix develop
```

Then install and run with `uv`:

```bash
uv install
uv lock
uv run python -m app.main
```

## API Docs and Test URLs

After starting the server (`python -m app.main`):

- Swagger UI: `http://127.0.0.1:5000/apidocs/`
- OpenAPI JSON: `http://127.0.0.1:5000/apispec_1.json`

## Main Endpoint Examples

### 1) Issue local JWT by user id

```bash
curl -X POST "http://127.0.0.1:5000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

### 2) Start Google SSO

```bash
curl -i "http://127.0.0.1:5000/auth/google/login?mode=json"
```

### 3) Create radiograph (multipart)

```bash
curl -X POST "http://127.0.0.1:5000/radiographs" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "patient_full_name=Juan Perez" \
  -F "patient_identifier=CC-123456" \
  -F "clinical_history_code=HC-2026-001" \
  -F "clinical_description=Dolor toracico persistente" \
  -F "study_date=2026-04-18T10:30:00Z" \
  -F "image_file=@./sample.png;type=image/png"
```


### 4) List with pagination, filters, and sorting

```bash
curl "http://127.0.0.1:5000/radiographs?page=1&size=10&sort=study_date:desc&patient_name=juan"
```


### 5) Get by id (protected)

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  "http://127.0.0.1:5000/radiographs/1"
```


### 6) Update (multipart optional image)

```bash
curl -X PUT "http://127.0.0.1:5000/radiographs/1" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "clinical_description=Descripcion actualizada" \
  -F "image_file=@./sample.png;type=image/png"
```

### 7) Delete by id

```bash
curl -i -X DELETE -H "Authorization: Bearer <JWT_TOKEN>" \
  "http://127.0.0.1:5000/radiographs/1"
```

### 8) Typical auth error example

```bash
curl -i "http://127.0.0.1:5000/radiographs/1"
```

Expected: `401 UNAUTHORIZED`

## CI Pipeline (GitHub Actions)

This project includes a basic CI pipeline in:

- `.github/workflows/ci.yml`

### What this pipeline does

On every push and pull request, it will:

1. Checkout the repository code.
2. Install Python 3.12.
3. Install project dependencies from `requirements.txt`.
4. Run Alembic migrations (`upgrade head`).
5. Check Python syntax with `compileall`.
6. Run smoke tests against Flask test client.

### Why this helps

- Catches broken dependencies quickly.
- Validates database schema/migrations in CI.
- Detects syntax/runtime integration errors before merge.
- Gives confidence that main endpoints still boot and respond.

### How to see pipeline status

1. Push your branch to GitHub.
2. Open your repository in GitHub.
3. Go to the **Actions** tab.
4. Open the latest workflow run (`CI Pipeline`).
5. Expand each step to see logs.

### Optional secret (recommended)

This workflow supports a repository secret named `CI_SECRET_KEY`.

1. Go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Create secret `CI_SECRET_KEY` with a random value.
3. If not set, workflow uses fallback `ci-secret-key` for CI-only checks.

### Common first-time issues

- **Dependency install fails**: check package versions in `requirements.txt`.
- **Migration step fails**: verify Alembic files and model changes are consistent.
- **Smoke tests fail**: inspect endpoint behavior changes and adjust assertions.

## Database And Migrations

### Relevant Files

- `app/models/base.py`: SQLAlchemy base and `db` instance
- `app/models/xray_record.py`: main entity (`xray_records`)
- `migrations/env.py`: Alembic configuration linked to `DATABASE_URL`
- `migrations/versions/`: migration history files

### Migration Commands

Create a new migration after model changes:

```bash
python -m alembic revision --autogenerate -m "describe_change"
```

Apply latest migrations:

```bash
python -m alembic upgrade head
```

Rollback one migration:

```bash
python -m alembic downgrade -1
```

Rollback to base:

```bash
python -m alembic downgrade base
```

Show current revision:

```bash
python -m alembic current
```

Show migration history:

```bash
python -m alembic history
```

## Current Database Status

- Migration cycle was validated successfully (`downgrade base` and `upgrade head`).
- Current head revision:
  - `b5112f27c258_update_xray_records_constraints.py`

## Team Notes

- If a model changes, generate and commit a new migration in `migrations/versions/`.
- Do not edit old migration files after they are shared with the team.
- Keep `DATABASE_URL` consistent in `.env` for all team members.
