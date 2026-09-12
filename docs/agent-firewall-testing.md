# AgentFirewall integration testing

## Automated tests

From the repository root, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python3 -m pytest backend/tests/test_firewall.py backend/tests/test_security.py backend/tests/test_agent.py backend/tests/test_api.py
```

The AgentFirewall tests verify:

1. Knowledge-manipulation instructions are detected and blocked.
2. The factual part of a document remains available after sanitization.
3. Malicious instructions never reach the model-provider payload.
4. Safe architecture documents are allowed.
5. Malicious document writes are rejected before connector execution.

## Full local demo

Start the application stack:

```bash
docker compose up --build
```

Make sure Docker Desktop (or another Docker daemon) is running first.

Open <http://localhost:3000>.

### Protected malicious-edit flow

1. Click **Reset Demo**.
2. Click **Simulate Migration → EKS**.
3. Click **Simulate malicious Confluence edit**. This adds a hidden instruction that asks the agent to ignore AWS and GitLab and preserve the stale EC2 claim.
4. Click **Run Scan**.

Expected results:

1. AgentFirewall changes from `EDIT PENDING SCAN` to `THREAT CONTAINED`.
2. The risk score is critical and the decision is `BLOCK`.
3. The source is `confluence://CONF-121`.
4. The contextual investigation shows an external author, an unexpected v17 → v18 change, no linked Jira/ServiceNow request, and matching EKS evidence from AWS and GitLab.
5. The activity timeline reports that malicious instructions were quarantined.
6. TrueSource still detects the legitimate EC2 → EKS documentation drift using trusted evidence.
7. The Payments Confluence document is marked `QUARANTINED`.
8. The proposed repair does not contain the hidden instruction.

### Protected write flow

1. Review the proposed EC2 → EKS changes.
2. Click **Approve & refresh verified RAG**.

Expected results:

1. AgentFirewall validates the reviewer, tenant, diff, and connector target before either document is changed.
2. The safe documentation repair succeeds.
3. The audit trail records the approval.

### API checks

```bash
curl http://localhost:8000/api/firewall/incidents
curl http://localhost:8000/api/audit
```

The firewall endpoint should contain the blocked Confluence incident after the malicious-edit scan.

## Optional model test

The security policy does not need a model key. With no provider key, TrueSource uses its deterministic fallback and AgentFirewall still enforces all blocks.

To test model-generated explanations, configure either `OPENAI_API_KEY` or `OPENROUTER_API_KEY`, restart the stack, and repeat the protected malicious-edit flow. The quarantined instruction must remain absent from model input and the proposed document repair.
