# API

## Core endpoints

1. `GET /api/health`
2. `GET /api/dashboard`
3. `GET /api/documents`
4. `GET /api/knowledge`
5. `GET /api/drift`
6. `GET /api/drift/{id}`
7. `GET /api/drift/{id}/evidence`
8. `GET /api/scans/{id}`
9. `POST /api/scan`
10. `POST /api/drift/{id}/approve`
11. `POST /api/drift/{id}/reject`
12. `POST /api/demo/migrate`
13. `POST /api/demo/reset`
14. `POST /api/ask`
15. `GET /api/audit`

## Scan contract

`POST /api/scan`

```json
{
  "scope": ["Payments"],
  "trigger": "manual"
}
```

Response:

```json
{
  "scan_id": "scan_ab12cd34",
  "status": "queued"
}
```

## Development auth

Development mode uses `X-Demo-User`, `X-Demo-Role`, and `X-Demo-Tenant` headers when you need to simulate different roles.
