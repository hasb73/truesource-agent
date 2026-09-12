# TrueSource Implementation Tasks

## 1. Delivery Strategy

Implementation proceeds in validated phases. Each phase ends with at least one executable verification step before expanding scope.

## 2. Phase Plan

### Phase 1: Specification

1. Create requirements, design, and tasks specs in `.kiro/specs/truesource/`.
2. Validate consistency between requirements, data model, API, and workflows.

Exit criteria:

1. All 16 requested specification areas are covered.
2. The design supports the required demo flow and definition of done.

### Phase 2: Repository Restructure And Shared Configuration

1. Establish target app and package layout under `apps/`, `mocks/`, `packages/`, `tests/`, and `infrastructure/`.
2. Preserve compatibility with the existing repo while moving toward the target structure.
3. Add root environment templates and shared configuration.
4. Align environment variable names such as `NEXT_PUBLIC_API_URL`.

Validation:

1. Static directory structure exists.
2. Compose configuration references all required services.

### Phase 3: Database And Persistence

1. Add PostgreSQL service and API database configuration.
2. Implement SQLAlchemy or SQLModel models for all core entities.
3. Add migrations.
4. Seed demo data automatically.

Validation:

1. Database container starts.
2. Migration command succeeds.
3. Seed data is queryable.

### Phase 4: Mock Enterprise Services

1. Implement separate FastAPI mock services for AWS, GitLab, Jira, ServiceNow, Confluence, and SharePoint.
2. Add health endpoints, seeded data, mutate and reset endpoints, and realistic REST contracts.
3. Ensure Payments migration and reset behavior is deterministic.

Validation:

1. Each mock responds to health and core data endpoints.
2. Integration tests cover representative endpoints.

### Phase 5: Connector Abstractions And Evidence Normalization

1. Create common connector interfaces.
2. Implement mock connector adapters using async HTTP clients.
3. Normalize connector payloads into canonical evidence.
4. Persist evidence by scan.

Validation:

1. Connector integration tests pass.
2. Normalized evidence matches schema.

### Phase 6: Drift Detection And Confidence Engine

1. Implement source authority model.
2. Implement confidence calculation with explainable breakdown.
3. Implement drift detection with unresolved-incident dedupe.
4. Persist incidents and evidence links.

Validation:

1. Unit tests cover confidence and drift outcomes.
2. Repeated scan idempotency test passes.

### Phase 7: Incident Lifecycle And Document Repair

1. Implement proposed change generation.
2. Implement approval, rejection, and rollback flows.
3. Version Confluence and SharePoint documents.
4. Emit audit events for all state changes.

Validation:

1. Approval updates documents and versions.
2. Rollback restores prior versions.

### Phase 8: Agent And Model Gateway

1. Implement LLM provider abstraction with OpenAI and OpenRouter.
2. Add prompt builders for explanation, repair summary, and answer synthesis.
3. Add deterministic fallback behavior for local no-key operation.
4. Capture agent run metadata and errors.

Validation:

1. No-key local flow works.
2. Provider selection is controlled by environment variables.

### Phase 9: Privacy And Security Boundary

1. Implement redaction module.
2. Add auth middleware for dev auth and Auth0.
3. Add role guards for reviewer and administrator actions.
4. Ensure only redacted evidence reaches model providers.

Validation:

1. Redaction unit tests pass.
2. Approval authorization tests pass.

### Phase 10: Scan Orchestration And Trigger.dev

1. Convert scan execution to queued async workflow.
2. Add worker orchestration and status polling.
3. Configure Trigger.dev schedule for periodic scans.
4. Add retry handling and failure states.

Validation:

1. Manual scan returns a scan ID.
2. Background processing completes.
3. Scheduled task configuration exists and is documented.

### Phase 11: Verified Knowledge Layer And Ask Experience

1. Implement verified fact upserts after approval.
2. Build trusted answer service over verified facts.
3. Include trust card metadata and refusal logic for unknown facts.

Validation:

1. Ask returns EC2 before migration and EKS after approval.
2. Low-confidence scenarios return explicit uncertainty.

### Phase 12: Web Experience And CopilotKit UI

1. Build overview dashboard.
2. Build incident detail, evidence explorer, diff viewer, audit panel, and demo controls.
3. Integrate CopilotKit surface for conversational and structured agent actions.
4. Add embedded notification or agent panel simulation.

Validation:

1. Main demo flow is operable entirely from the UI.
2. Responsive behavior is acceptable on laptop widths.

### Phase 13: Notifications And Ambiguous AI Adapter

1. Implement notification abstraction with mock sender.
2. Add Ambiguous AI adapter interface and mock implementation.
3. Surface these integrations in workflow and docs.

Validation:

1. Notification events are emitted on incident detection and approval.
2. Adapter is swappable without API changes.

### Phase 14: Docker, Cloud Run, And Documentation

1. Finalize Dockerfiles and Compose health checks.
2. Add Cloud Run manifests and deployment docs.
3. Update README and architecture docs.
4. Ensure environment variable documentation is complete.

Validation:

1. `docker compose up --build` starts the full stack.
2. Cloud Run manifests reference production environment variables and secrets.

### Phase 15: Test Completion And Demo Validation

1. Add unit, integration, and end-to-end tests.
2. Automate the full demo scenario.
3. Run tests locally.
4. Fix build, runtime, and contract issues.

Validation:

1. Test suite passes.
2. The definition of done is demonstrably satisfied.

## 3. Immediate Execution Backlog

1. Inspect the current implementation and map it to the target architecture.
2. Decide whether to evolve the existing `backend/` and `frontend/` folders in place or introduce `apps/` and migrate incrementally.
3. Add PostgreSQL, mocks, and worker foundations first because they affect API contracts and demo flow.
4. Preserve the existing simplified demo behavior while expanding it to the spec so there is always a runnable baseline.

## 4. Risk Register

1. Full sponsor-grade live integrations are not feasible without credentials; the solution mitigates this by using production-shaped adapters plus mocks.
2. CopilotKit runtime details evolve; the MVP should use a thin compatible integration while keeping the architecture AG-UI-ready.
3. Trigger.dev local orchestration can be heavy; the implementation may use API plus worker queue semantics locally with Trigger.dev configuration included and documented.
4. A monorepo restructuring can break existing run paths; changes should preserve working Docker entrypoints until the new layout is verified.

## 5. Definition Of Done Verification Matrix

1. Startup: compose boots web, api, worker, postgres, and all mocks.
2. Data: seeded applications and stale Payments docs are visible.
3. Demo controls: reset, migrate, scan, approve, ask all function.
4. Incidents: evidence and diffs are visible and explainable.
5. Updates: Confluence and SharePoint versions increment on approval.
6. Knowledge: verified facts update and drive answers.
7. Audit: all major actions appear in history.
8. Reliability: repeated scans are idempotent and failures degrade gracefully.
9. Security: reviewer role is enforced and LLM-bound evidence is redacted.
10. Deployability: Cloud Run manifests and deployment docs are present.
