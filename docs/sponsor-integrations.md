# Sponsor Integrations

## OpenAI

Used for optional explanation and answer synthesis through the Responses API.

## OpenRouter

Supported through the same provider gateway, using a configurable base URL and model.

## CopilotKit

Represented in the current frontend architecture as the agent-facing UX surface; the UI is structured around agent actions, activity, and reviewable state.

## Exa

Reserved for external verification where public vendor documentation is useful, but never as the primary source of enterprise truth.

## Trigger.dev

The `trigger/tasks.ts` schedule posts scans every 15 minutes, and the local `worker.mjs` provides a Dockerized background-worker placeholder.

## Ambiguous AI

Included in the design as an adapter surface for future enterprise workspace integration.

## Mozilla

Reflected through the privacy boundary and redaction-first evidence pipeline.

## Google Cloud Run

Deployment manifests are provided for API and web services, with a documented path for the worker.
