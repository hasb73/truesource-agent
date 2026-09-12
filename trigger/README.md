# Trigger.dev integration

Install the current Trigger.dev CLI/SDK following the sponsor's current docs, then deploy `tasks.ts`.
The task calls `POST /api/scan` every 15 minutes.

For the hackathon, the dashboard UI in `frontend/app/page.tsx` is intentionally framework-light.
To use the full CopilotKit/AG-UI runtime, add the current CopilotKit runtime endpoint and wrap the app
with the current provider/runtime components from the sponsor documentation.
