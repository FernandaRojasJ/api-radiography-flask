---
name: radiography-api
description: "Optimized agent for Flask X-Ray API. Fast navigation of layered architecture: routers→services→repositories→models. Handles SQLAlchemy, Alembic migrations, Pydantic schemas, JWT auth, Cloudinary integration. Minimal context overhead."
applyTo: ["**/*.py", "alembic.ini", "requirements.txt"]
---

# Radiography API Agent

## Project Context (Compact)

**Stack**: Flask 3.0 + SQLAlchemy + Alembic + Pydantic + JWT + Cloudinary + Flasgger

**Architecture**:
- `routers/` → HTTP endpoints (auth_router, radiographs_router)
- `services/` → business logic (xray_service, cloudinary_service)
- `repositories/` → data access (xray_repository)
- `models/` → SQLAlchemy ORM (xray_record)
- `schemas/` → Pydantic validation (xray_schema)
- `core/` → config, security, scheduler
- `migrations/` → Alembic version control

## Token Optimization Rules

1. **No intro fluff**: Skip "Here's how", "Let me help", verbose explanations
2. **Direct code**: Show only changed/relevant code
3. **Paths as links**: Always use `[file.py](file.py#L10)` format
4. **List format**: Use bullets for changes, skip narrative prose
5. **No summaries**: Skip "I've completed X steps" recaps
6. **Abbreviations**: Use `repo` for repository, `svc` for service, `schema` for Pydantic schema
7. **One-liner context**: "Fixed X in Y" vs full explanation
8. **Tool minimalism**: Only read/search needed context; no exploratory reads

## Navigation Shortcuts

- **Auth flow**: `auth_router.py` → `security.py` (JWT/auth logic)
- **X-Ray CRUD**: `radiographs_router.py` → `xray_service.py` → `xray_repository.py` → `xray_record.py`
- **Image privacy**: `xray_service.py` (enforce_private_images) + scheduler in `main.py`
- **Database changes**: `migrations/versions/` (Alembic applied migrations)
- **Config**: `core/config.py` (env vars, database URL, Cloudinary keys)
- **Validation**: `schemas/xray_schema.py` (Pydantic models)

## Search Strategy (Token-Efficient)

- **Find endpoint**: `grep_search` for `@radiographs_bp.route` or `@auth_bp.route`
- **Find service method**: Locate in `services/xray_service.py` by class/method name
- **Find model field**: Grep `models/xray_record.py` for column definition
- **Check schema**: See `schemas/xray_schema.py` for validation rules
- **Database queries**: View `repositories/xray_repository.py` for SQL patterns

## Common Tasks (Pre-Cached)

| Task | Path | Note |
|------|------|------|
| Add endpoint | `routers/radiographs_router.py` | HTTP layer |
| Add business logic | `services/xray_service.py` | Cloudinary calls here |
| Add repo query | `repositories/xray_repository.py` | SQLAlchemy pattern |
| Add field to X-Ray | `models/xray_record.py` + migration | Use Alembic autogenerate |
| Add validation | `schemas/xray_schema.py` | Pydantic Fields |
| Modify scheduler | `core/scheduler.py` | APScheduler config |
| Fix auth | `core/security.py` | JWT token decode/encode |
| Upload flow | `services/cloudinary_service.py` | Media handling |

## Constraints (Auto-Applied)

- No file creation unless explicitly requested
- No exploratory reads; only target needed files
- No long explanations; state facts + code
- Inline code snippets; link to files for full context
- Use `read_file` with precise line ranges
