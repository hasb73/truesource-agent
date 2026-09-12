# Security

## Trust boundary

Enterprise evidence is collected from source systems, redacted, normalized, and only then made available to external model providers.

## Current controls

1. Development authentication mode with role headers.
2. Reviewer-only approval and rejection endpoints.
3. Regex-based redaction for access keys, JWTs, API keys, passwords, private keys, and credential-bearing connection strings.
4. Audit events for reset, scan queueing, detection, and approval actions.
5. AgentFirewall inspection of untrusted document and ticket content before model access.
6. Quarantine of indirect prompt injections while preserving safe factual content.
7. Pre-execution authorization of Confluence and SharePoint document writes.
8. Security incident traces describing the selected checks, signals, decision, and containment actions.

## AgentFirewall boundaries

1. Ingress guard: inspects Confluence, SharePoint, GitLab, Jira, and ServiceNow evidence.
2. Model-context guard: removes blocked instructions before the provider adapter receives evidence.
3. Action guard: validates reviewer role, tenant, diff content, and connector target before a write.
4. Verification trail: records blocked attacks and authorized writes in the audit history.

Enforcement is deterministic-first and works when no external model provider is configured. Models may explain verified findings, but do not decide whether a dangerous action executes.

## Production path

1. Persist audit events in PostgreSQL.
2. Add tenant-scoped authorization and source-level access control.
3. Move secrets to a managed secret store.
