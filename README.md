# TrueSource Agent — Self-Healing, Agent-Safe Enterprise Knowledge

TrueSource Agent is a knowledge control plane that sits between enterprise systems, documentation, and AI. It detects documentation drift, verifies claims against live operational evidence, proposes governed repairs, and exposes only verified knowledge to downstream assistants and RAG.

Its AgentFirewall also protects the agent itself: malicious instructions hidden inside documents or tickets are detected and quarantined before they can influence a model or trigger a tool.

## Problem

Traditional enterprise RAG often treats stale documentation as truth. When Payments has moved from EC2 to EKS but the docs still say EC2, retrieval makes the wrong answer easier to produce, not harder.

## Solution

TrueSource turns that into a governed, agent-safe workflow:

```text
Enterprise systems → AgentFirewall → Verified truth → Documentation → Trusted AI
```

The product collects evidence, blocks unsafe instructions, explains contradictions, proposes fixes, requires human approval, updates stale documents, and refreshes the verified knowledge layer.

## Key capabilities

1. Detect drift between Confluence or SharePoint and AWS, GitLab, Jira, and ServiceNow.
2. Calculate deterministic, authority-weighted confidence before asking a model for an explanation.
3. Generate document repair proposals with evidence and provenance.
4. Require reviewer approval before executing connector writes.
5. Answer questions from verified facts instead of stale documents.
6. Block prompt injection, knowledge manipulation, credential requests, concealment, and destructive instructions.
7. Investigate suspicious edits using author, version, change-request, and operational context.
8. Preserve an audit trail of scans, decisions, containment, and approvals.

## Architecture

The current repo contains:

1. `backend/` FastAPI control plane for scans, incidents, approvals, audit, and verified answers.
2. `frontend/` Next.js dashboard with demo controls, evidence review, trust card, and agent activity.
3. `mocks/` separate FastAPI services for AWS, GitLab, Jira, ServiceNow, Confluence, and SharePoint.
4. `trigger/` Trigger.dev schedule definition plus a lightweight worker container entrypoint.
5. `cloudrun/` Cloud Run manifests.
6. `.kiro/specs/truesource/` requirements, design, and task specs.

Runtime behavior highlights:

1. Scans are deterministic-first: connector evidence and scoring establish drift before any model narrative.
2. External model egress is redacted and provider-routed (OpenAI, OpenRouter, or deterministic fallback).
3. Control-plane state is persisted in PostgreSQL and reloaded on backend startup.
4. Approval decisions are reviewer-gated and recorded in audit history.
5. AgentFirewall makes deterministic `ALLOW`, `REVIEW`, or `BLOCK` decisions before model access and validates document writes before connector execution.

## Sponsor technologies

1. OpenAI for explanation and answer synthesis.
2. OpenRouter as a provider fallback path.
3. CopilotKit-oriented UX structure in the web app.
4. Exa reserved for supplementary public verification.
5. Trigger.dev for scheduled scans.
6. Ambiguous AI represented through adapter-first design.
7. Mozilla-style privacy boundary through redaction and provenance.
8. Google Cloud Run deployment manifests for web and API.

## Local setup

### Environment

```bash
cp .env.example .env
```

Optional keys:

```env
OPENAI_API_KEY=
OPENROUTER_API_KEY=
EXA_API_KEY=
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=
NEXT_PUBLIC_COPILOTKIT_AGENT_ID=truesource_guardian
```

Notes:

1. Development auth mode is always enabled and reviewer actions use the demo actor path.
2. OpenRouter is supported through the same model gateway and can be selected at runtime from the dashboard when configured.
3. CopilotKit is wired into the app shell and will activate its sidebar when `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL` is set.

### Docker Compose

```bash
docker compose up --build
```

Useful lifecycle commands:

```bash
docker compose ps
docker compose logs -f backend frontend
docker compose down
docker compose up --build -d
```

Expected services:

1. `postgres`
2. `mock-aws`
3. `mock-gitlab`
4. `mock-jira`
5. `mock-servicenow`
6. `mock-confluence`
7. `mock-sharepoint`
8. `backend`
9. `frontend`
10. `worker`

Open:

1. Frontend: `http://localhost:3000`
2. Backend docs: `http://localhost:8000/docs`
3. API health: `http://localhost:8000/api/health`

## Recommended demo walkthrough

1. Open the dashboard and ask “How is Payments deployed?” to see the stale EC2 answer.
2. Click `Simulate Migration → EKS`.
3. Click `Run Scan`.
4. Review the knowledge incident, evidence, and proposed diffs.
5. Click `Approve & refresh verified RAG`.
6. Ask the same question again and verify the answer now says EKS with confidence and provenance.
7. Click `Reset Demo` to restore the original scenario.

Additional operational scenarios are available for database modernization, region failover, and GitOps rollout.

### AgentFirewall integration demo

1. Click `Reset Demo`, then `Simulate Migration -> EKS`.
2. Click `Simulate malicious Confluence edit` to add a hidden instruction that tries to keep stale EC2 knowledge verified despite contradictory AWS and GitLab evidence.
3. Click `Run Scan`.
4. AgentFirewall changes from `EDIT PENDING SCAN` to `THREAT CONTAINED` and shows four concise reasons: external author, unexpected version, no linked change request, and live-system evidence.
5. Confirm TrueSource still detects the legitimate EC2 -> EKS drift from trusted evidence.
6. Approve the safe repair; AgentFirewall validates the write before the connector executes.

The incident panel keeps the default explanation simple. Select `Show technical details` to inspect the detection signals and containment trace.

### What AgentFirewall decides

| Decision | Meaning | Result |
| --- | --- | --- |
| `ALLOW` | Content is low risk | Admit it to the evidence pipeline |
| `REVIEW` | Content is ambiguous | Retain it for human review |
| `BLOCK` | Content contains a dangerous instruction | Quarantine it, deny sensitive tools, and continue with trusted evidence |

AgentFirewall enforcement is deterministic and does not require a model key. OpenAI or OpenRouter may generate explanations, but the model does not decide whether a dangerous action executes.

See `docs/agent-firewall-testing.md` for detailed tests and expected results.

## Docs portal mock

1. Open `http://localhost:3000/portal` for a Confluence-style documentation workspace.
2. Browse and search pages from the mock Confluence source.
3. Inspect SharePoint mirror content and version metadata side by side.

## Hackathon materials

1. Pitch deck script and judge talk track: `docs/hackathon-pitch.md`
2. Submission-ready descriptions (short, medium, long): `docs/project-description.md`

## API

Core endpoints:

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
12. `GET /api/demo/scenarios`
13. `POST /api/demo/change`
14. `POST /api/demo/inject-agent-attack`
15. `POST /api/demo/reset`
16. `GET /api/docs/portal`
17. `PUT /api/docs/portal/confluence/{id}`
18. `PUT /api/docs/portal/sharepoint/{id}`
19. `POST /api/ask`
20. `GET /api/audit`
21. `GET /api/firewall/incidents`
22. `GET /api/runtime`
23. `GET /api/auth/me`

## Testing

Run all backend tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python3 -m pytest backend/tests
```

The suite covers scan and approval behavior, security redaction, prompt-injection quarantine, contextual investigation, write authorization, and protection of model input.

For the complete AgentFirewall test flow and expected UI results, see [`docs/agent-firewall-testing.md`](docs/agent-firewall-testing.md).

## Cloud Run deployment

Deployables:

1. `truesource-api`
2. `truesource-web`
3. optional worker runtime depending on Trigger.dev setup

See the docs set for architecture, API, deployment, security, and sponsor integration details.

## Security

Current controls include:

1. Reviewer-only approval and rejection operations.
2. Redaction before outbound model-provider calls.
3. Development-mode actor identity via local headers.
4. Persisted audit trail for scan and decision events.
5. Ingress inspection across Confluence, SharePoint, GitLab, Jira, and ServiceNow.
6. Quarantine before malicious content reaches a model.
7. Pre-execution checks for reviewer identity, tenant, diff, and connector target.
8. Contextual investigation of source ownership, version history, change records, and live evidence.

Remaining hardening roadmap includes tenant isolation and production secret-management posture.

## Validation note

Recent validation includes:

1. Full Docker Compose startup and health verification for frontend, backend, postgres, worker, and mock services.
2. Frontend runtime check returning HTTP 200 after conditional Auth0 integration fixes.
3. Backend tests passing via `pytest backend/tests`.

## Roadmap

1. Expand integration and E2E test coverage across connector and UI workflows.
2. Add migration-managed relational schema evolution and stronger operational observability.
3. Complete production auth hardening (tenant isolation and policy controls).
4. Deepen CopilotKit runtime behaviors and assisted review workflows.
5. Replace mock connectors with live enterprise adapters using the same normalized interfaces.
