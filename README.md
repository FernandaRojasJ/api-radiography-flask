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

## Environment Variables

Create a `.env` file in the project root using `.env.example` as template:

```env
DATABASE_URL=sqlite:///./xray_database.db
SECRET_KEY=your_secret_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Setup

### Windows (PowerShell)

1. Create and activate virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
python -m pip install -r requirements.txt
```

3. Apply database migrations.

```powershell
python -m alembic upgrade head
```

4. Run the API.

```powershell
python -m app.main
```

### Linux/macOS (Non-NixOS)

1. Ensure Python 3.12+ is installed.

2. Create and activate virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Upgrade pip and install dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Apply database migrations.

```bash
python -m alembic upgrade head
```

5. Run the API.

```bash
python -m app.main
```

### Linux/macOS (NixOS with Flake)

This repository includes a simple flake-based dev shell with system dependencies.

1. Enter the dev shell.

```bash
nix develop
```

If you use direnv, allow it once and it will auto-enter:

```bash
direnv allow
```

2. Install dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Apply migrations and run.

```bash
python -m alembic upgrade head
python -m app.main
```

Notes:

- Always run the app with the active venv interpreter (`python`).
- If you still have an old `.venv` from another Python version, recreate it:

```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## API Docs and Test URLs

After starting the server (`python -m app.main`):

- Swagger UI: `http://127.0.0.1:5000/apidocs/`
- OpenAPI JSON: `http://127.0.0.1:5000/apispec_1.json`

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
