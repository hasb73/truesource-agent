# Deployment

## Local

The local stack is designed to start with Docker Compose and includes:

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

## Cloud Run

Deploy at minimum:

1. `truesource-api`
2. `truesource-web`

Optional:

1. `truesource-worker` or hosted Trigger.dev worker runtime
2. Cloud SQL Postgres instance

## Environment variables

Use `.env.example` as the local source of truth for LLM provider selection, mock service URLs, and development auth.

## Known gap

Docker build and startup could not be executed in this environment because the local Docker daemon was unavailable during validation.
