# Shared contracts

v0 keeps types next to each app:

- API: Pydantic schemas in `apps/api/app/schemas.py` (source of truth)
- Desk: TypeScript types in `apps/desk/lib/types.ts` (mirror)

Live machine-readable contract: `GET http://localhost:8000/openapi.json` and the Swagger UI at `/docs`.

A future `packages/openapi` extract can be generated from FastAPI once more clients (regional desks, mobile) exist. Do not add a second conflicting schema.
