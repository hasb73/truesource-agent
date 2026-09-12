# TrueSource Requirements Specification

## 1. Product Summary

TrueSource is an enterprise knowledge control plane that continuously reconciles what the company says in documentation with what the company actually does in operational systems. It detects knowledge drift, verifies contradictions using authoritative evidence, proposes safe documentation repairs, requires human approval by default, and publishes only verified facts to downstream AI and retrieval systems.

Core product principle:

> AI should not merely retrieve enterprise knowledge. TrueSource continuously verifies whether that knowledge is still true.

Primary hackathon narrative:

> The agent that keeps your company's knowledge truthful.

## 2. Goals

1. Detect stale enterprise documentation before humans or AI consume it as truth.
2. Use deterministic evidence collection, source authority scoring, and explainable confidence before LLM reasoning.
3. Keep enterprise documentation synchronized with authoritative operational reality through human-approved fixes.
4. Expose a verified knowledge layer suitable for trusted RAG and AI assistants.
5. Deliver a polished, repeatable three-minute demo centered on the Payments EC2 to EKS migration scenario.
6. Run locally with Docker Compose and have a clear path to Google Cloud Run deployment.

## 3. Non-Goals

1. Full production-grade enterprise connector coverage beyond the defined mock systems.
2. Automatic document modification without explicit human approval in the default configuration.
3. General-purpose chat assistant behavior over raw documents.
4. Deep bidirectional synchronization with every enterprise system beyond the MVP update flow for Confluence and SharePoint.

## 4. Assumptions And Engineering Decisions

1. The MVP uses PostgreSQL as the primary relational store for incidents, facts, audit events, and scan history.
2. Mock systems run as separate HTTP services to preserve realistic integration boundaries.
3. Development authentication mode is provided locally; Auth0 is optional for local startup but mandatory in the production architecture.
4. Trigger.dev is used for scheduled scans and asynchronous scan execution, while the API remains the control plane.
5. OpenAI is the preferred reasoning provider; OpenRouter is the configurable fallback; deterministic logic remains authoritative for evidence handling, confidence, and approvals.
6. Exa is used only for supplementary external verification, never as the primary authority for enterprise truth.
7. Ambiguous AI is integrated through an adapter interface with a mock implementation when live credentials are unavailable.
8. Secret and PII redaction is mandatory before sending evidence to any external model provider.
9. The initial implementation is single-tenant in local demo mode but the schema and auth model remain tenant-aware.
10. Documentation updates are versioned and rollbackable.

## 5. Personas

1. Viewer: can inspect dashboard state, evidence, incidents, and verified answers.
2. Reviewer: can review incidents and approve or reject documentation changes.
3. Administrator: can configure sources, reset demo data, trigger rescans, and perform rollbacks.
4. AI Consumer: a downstream assistant or retrieval system that reads only verified knowledge facts.
5. Judge Or Demo Audience: needs to understand the value proposition in under three minutes.

## 6. User Stories

### 6.1 Detection And Review

1. As a reviewer, I want TrueSource to tell me when documentation contradicts operational systems so I can prevent stale guidance from spreading.
2. As a reviewer, I want to see structured evidence from AWS, GitLab, Jira, ServiceNow, Confluence, and SharePoint so I can understand why drift was detected.
3. As a reviewer, I want to see a confidence explanation driven by authority, recency, and agreement so I can decide whether to approve a fix.
4. As an administrator, I want repeated scans to avoid creating duplicate incidents for the same unresolved drift so the review queue stays actionable.

### 6.2 Repair And Verification

1. As a reviewer, I want proposed documentation diffs before anything changes so I can approve with confidence.
2. As a reviewer, I want approval to update Confluence and SharePoint and refresh verified knowledge so downstream AI receives current facts.
3. As an administrator, I want rollback support so an incorrect approved change can be undone safely.
4. As a security-conscious user, I want secrets and PII redacted before model calls so sensitive data is not exposed.

### 6.3 Consumption And Trust

1. As an employee, I want to ask "How is Payments deployed?" and receive an answer that includes confidence, provenance, and verification time.
2. As a downstream AI team, I want verified knowledge records with metadata such as verified status, timestamp, confidence, and sources so trusted RAG can use them safely.
3. As a judge, I want the UI to make the agent activity obvious so I can see this is more than a static dashboard.

### 6.4 Demo Mode

1. As a presenter, I want one-click controls to reset the demo, simulate migration, run scan, approve fix, and ask a question so the demo is repeatable.
2. As a presenter, I want the Payments migration scenario to complete in under three minutes from stale answer to verified answer.

## 7. Functional Requirements

### 7.1 Authentication And Authorization

1. The system shall support Auth0-based authentication for production.
2. The system shall provide a development authentication mode for local startup without Auth0.
3. The system shall assign users one of the roles `viewer`, `reviewer`, or `administrator`.
4. The approval endpoint shall require `reviewer` or `administrator` privileges.
5. All user actions shall capture user identity, role, and tenant context.

### 7.2 Mock Enterprise Systems

1. The system shall include separate mock services for AWS, GitLab, Jira, ServiceNow, Confluence, and SharePoint.
2. Each mock service shall expose REST APIs over HTTP and maintain its own mutable state.
3. The mock services shall seed realistic demo data for Payments, Customer Portal, Flight Search, Loyalty, and Crew Management.
4. The Payments application shall support an initial EC2 state and a simulated EKS migration state.
5. Confluence and SharePoint mocks shall support versioned document updates.

### 7.3 Connectors And Evidence Collection

1. The backend shall communicate with mock systems via HTTP, not direct imports.
2. Every source integration shall implement a common connector interface for health, entity retrieval, and evidence collection.
3. Evidence shall be normalized into a shared schema with provenance, timestamps, source references, source type, confidence, and collected-at metadata.
4. The system shall store evidence associated with scan runs and incidents.
5. Missing evidence shall be treated as unknown, not as contradicting evidence.

### 7.4 Drift Detection And Confidence

1. The system shall detect drift by comparing documented facts against authoritative operational and workflow evidence.
2. The system shall not create high-confidence drift from a single source alone.
3. The system shall calculate deterministic confidence using source authority, evidence agreement, recency, source reliability, and documentation age.
4. The confidence result shall be explainable with factor breakdowns.
5. The system shall assign incident statuses from `detected`, `investigating`, `pending_review`, `approved`, `rejected`, `resolved`, and `failed`.
6. Repeated scans shall be idempotent and reuse an existing open incident when the drift signature is unchanged.

### 7.5 Agent Functions

1. The system shall expose logical agent capabilities for discovery, evidence normalization, verification, knowledge understanding, repair proposal, and answer generation.
2. Deterministic code shall control evidence collection, authority scoring, confidence, diff generation, authorization, approvals, and document updates.
3. LLMs shall be used for contradiction explanation, human-readable summaries, answer generation, and alternative wording for document repairs.
4. The answer agent shall answer only from verified knowledge and shall refuse to invent unknown facts.
5. The UI shall display live agent activity states during scans and review.

### 7.6 Incident Lifecycle And Repair

1. A scan shall create or update a `ScanRun` record and progress asynchronously.
2. Drift detection shall create a `KnowledgeIncident` with structured evidence and affected documents.
3. Repair generation shall produce proposed document changes and human-readable rationale.
4. Approval shall create an audit event, update documents, create new document versions, refresh verified knowledge, and mark the incident resolved.
5. Rejection shall create an audit event and preserve the incident history.
6. Rollback shall restore the previous document version and emit audit events.

### 7.7 Verified Knowledge And Ask Experience

1. The system shall publish a verified knowledge record per application/entity and attribute.
2. Each fact shall include value, confidence, verified timestamp, provenance, version, and status.
3. The ask endpoint shall answer from verified knowledge only.
4. The ask response shall include a trust card with confidence, verification freshness, number of sources, and documentation update status.
5. If confidence is low or the fact is unavailable, the answer shall explicitly state the verification gap.

### 7.8 Demo Controls

1. The API shall support reset-demo, simulate-migration, run-scan, approve-fix, reject-fix, and ask flows.
2. Reset shall restore all mocks, database state, incidents, and verified knowledge to the initial seed state.
3. The demo shall remain usable with or without OpenAI credentials.

### 7.9 Notifications And Embedding

1. The system shall include a notification abstraction with a mock implementation.
2. Notifications shall support knowledge drift alerts that can later be routed to Slack, Teams, or email.
3. The dashboard shall be the control plane, but the design shall support embedded agent experiences in other enterprise tools.

## 8. Non-Functional Requirements

1. Local startup shall work with `docker compose up --build`.
2. The demo flow shall be completable in under three minutes on a typical developer machine after startup.
3. API contracts shall be typed, validated, and documented in OpenAPI.
4. All network interactions shall use timeouts, structured error handling, and observable request or scan identifiers.
5. The system shall produce structured logs for requests, scans, incidents, connector calls, and model calls.
6. The system shall avoid hard-coded secrets and shall rely on environment variables.
7. The UI shall be responsive and usable on desktop and laptop demo screens.
8. The system shall remain partially functional when the LLM provider is unavailable.
9. Connector failures shall degrade confidence rather than cause false certainty.
10. The codebase shall preserve clean separation between domain logic, infrastructure, and transport.

## 9. Acceptance Criteria

1. Frontend, API, worker, PostgreSQL, and all six mock services start via Docker Compose.
2. Seeded dashboard data is visible at startup.
3. Payments starts with EC2 in documentation and verified knowledge.
4. Simulate migration changes AWS, GitLab, Jira, and ServiceNow but leaves Confluence and SharePoint stale.
5. A scan produces a knowledge incident with evidence, confidence explanation, and proposed diffs.
6. The reviewer can approve the incident and trigger document updates.
7. Confluence and SharePoint document versions increment and record diffs.
8. Verified knowledge updates to EKS and RDS PostgreSQL with provenance.
9. The ask flow returns EKS with confidence and source references.
10. Audit history records detection, proposal, approval, updates, and knowledge refresh.
11. Reset restores the initial state.
12. Automated unit, integration, and end-to-end tests pass.
13. Cloud Run deployment manifests exist for web and API services, with a clear worker deployment path.

## 10. Traceability To Definition Of Done

The implementation is complete only when every definition-of-done item maps to at least one automated or manual validation step in the implementation task plan and test suite.
