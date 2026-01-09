# Backend

Django backend for the workflow engine.

## Tech Stack (MVP)

- Python 3.12 — runtime for the backend service
- Django 5.x — core web framework and ORM
- Django REST Framework — API layer for clients
- Postgres 15+ — relational store for entities, rules, and audit logs
- Auth: Django auth + role model — access control foundation
- Rules Engine: in-process deterministic evaluator (Python) — enforces rule logic without scripting

## Docker Dev Setup

This repo uses one Postgres container and two Django containers:

- API: http://localhost:8000
- Admin: http://localhost:8001/admin

Environment variables are loaded from files in `env/`.

From the repo root:

```bash
docker compose up --build
```

Or use the helper script:

```bash
./scripts/run.sh local
```

Initialize the database (first time):

```bash
docker compose exec api python manage.py migrate
```

To create a superuser:

```bash
docker compose exec api python manage.py createsuperuser
```

For staging/production templates and env file layout, see `env/README.md`.
