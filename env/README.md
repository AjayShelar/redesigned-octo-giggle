# Environment Files

This project uses env files for local, staging, and production.

## Layout

```
env/
  local.base.env
  local.api.env
  local.admin.env
  local.db.env
  stage.base.env
  stage.api.env
  stage.admin.env
  stage.db.env
  prod.base.env
  prod.api.env
  prod.admin.env
  prod.db.env
```

## Guidance

- `*.base.env` holds shared settings for all services.
- `*.api.env` and `*.admin.env` add service-specific vars.
- `*.db.env` is for DB-only overrides (optional).
- For real deployments, replace placeholder secrets in `stage.*` and `prod.*` files.

## Usage

The compose files load these automatically via `env_file`.

Examples:

```bash
./scripts/run.sh local
./scripts/run.sh stage
./scripts/run.sh prod
```
