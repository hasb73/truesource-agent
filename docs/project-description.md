# Project Description

## Short description (one sentence)

TrueSource continuously reconciles enterprise documentation with live system evidence, then serves only verified knowledge to AI assistants.

## Submission description (about 120 words)

TrueSource is a self-healing knowledge control plane for enterprise AI. It monitors operational sources and documentation sources together, detects drift when they contradict each other, and creates evidence-backed incidents with confidence scoring and proposed document changes. Reviewers approve or reject remediation actions through a governed workflow, and every decision is recorded in an audit trail. Once approved, the verified knowledge layer is refreshed so downstream assistants and RAG pipelines use current, trustworthy context. The architecture is deterministic-first for source authority and model-assisted for explanation quality, with redaction before model egress, runtime provider routing, and dual auth modes for development and production. The result is fewer stale-answer failures and safer AI adoption in enterprise environments.

## Long description (about 250 words)

Enterprise AI systems often fail for a simple reason: retrieval pipelines trust documentation that has drifted away from operational reality. A team may have migrated from EC2 to EKS, yet internal docs still describe the old architecture. Standard RAG then amplifies stale content with high confidence.

TrueSource solves this by introducing a dedicated knowledge control plane. It collects normalized evidence from operational systems and compares that evidence with documentation systems to identify contradictions. When drift is detected, TrueSource generates a knowledge incident that includes supporting evidence, confidence scoring, and proposed edits. A human reviewer can approve or reject each remediation action, ensuring governance and accountability.

After approval, TrueSource updates the verified knowledge layer used by downstream assistants. This closes the loop from reality to documentation to trusted AI response quality. The platform also includes redaction before external model calls, provider routing across OpenAI and OpenRouter, and runtime introspection for operational transparency.

The current implementation includes a FastAPI backend, a Next.js dashboard, trigger-based scan orchestration, PostgreSQL persistence, and mock enterprise connectors for AWS, GitLab, Jira, ServiceNow, Confluence, and SharePoint. This makes the system easy to demo while preserving a production-oriented architecture.

In short, TrueSource helps organizations move from fluent but fragile AI answers to reliable, explainable, and auditable enterprise AI.

## Audience-specific versions

### For business judges

TrueSource reduces costly AI mistakes by ensuring assistants answer from verified, up-to-date enterprise knowledge instead of stale documentation.

### For technical judges

TrueSource combines deterministic contradiction detection, evidence normalization, human approval gates, redaction, model-provider abstraction, and persistent audit-backed workflow state.

### For security and governance judges

TrueSource enforces approval controls, provenance tracking, redaction before model egress, and auditable decision history for compliance-ready AI operations.
