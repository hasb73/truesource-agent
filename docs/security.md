# Security

## Trust boundary

Enterprise evidence is collected from source systems, redacted, normalized, and only then made available to external model providers.

## Current controls

1. Development authentication mode with role headers.
2. Reviewer-only approval and rejection endpoints.
3. Regex-based redaction for access keys, JWTs, API keys, passwords, private keys, and credential-bearing connection strings.
4. Audit events for reset, scan queueing, detection, and approval actions.

## Production path

1. Persist audit events in PostgreSQL.
2. Add tenant-scoped authorization and source-level access control.
3. Move secrets to a managed secret store.
