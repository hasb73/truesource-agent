from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

APPLICATIONS = [
    "Payments",
    "Customer Portal",
    "Flight Search",
    "Loyalty",
    "Crew Management",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _application_slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def _base_resources() -> list[dict[str, Any]]:
    return [
        {
            "application": "Payments",
            "compute": "EC2",
            "database": "RDS MySQL",
            "region": "me-central-1",
            "deployment": "EC2 deployment scripts",
        },
        {
            "application": "Customer Portal",
            "compute": "ECS",
            "database": "Aurora PostgreSQL",
            "region": "eu-west-1",
            "deployment": "GitLab CI/CD",
        },
        {
            "application": "Flight Search",
            "compute": "EKS",
            "database": "DynamoDB",
            "region": "us-east-1",
            "deployment": "Argo CD",
        },
        {
            "application": "Loyalty",
            "compute": "Lambda",
            "database": "Aurora MySQL",
            "region": "eu-central-1",
            "deployment": "Serverless Framework",
        },
        {
            "application": "Crew Management",
            "compute": "VMware",
            "database": "Oracle",
            "region": "on-prem-dubai-1",
            "deployment": "Jenkins",
        },
    ]


def aws_seed() -> dict[str, Any]:
    return {
        "accounts": [
            {
                "id": "123456789012",
                "name": "demo-enterprise-prod",
                "provider": "aws",
            }
        ],
        "resources": _base_resources(),
        "changes": [
            {
                "id": "aws-change-1000",
                "application": "Payments",
                "summary": "Payments currently runs on EC2",
                "timestamp": "2026-09-10T09:00:00Z",
            }
        ],
    }


def migrate_aws(state: dict[str, Any]) -> dict[str, Any]:
    resources = state["resources"]
    payments = next(item for item in resources if item["application"] == "Payments")
    payments["compute"] = "EKS"
    payments["database"] = "RDS PostgreSQL"
    payments["deployment"] = "GitLab CI/CD"
    if not any(change["id"] == "aws-change-1001" for change in state["changes"]):
        state["changes"].append(
            {
                "id": "aws-change-1001",
                "application": "Payments",
                "summary": "Payments migrated from EC2 to EKS",
                "timestamp": now_iso(),
            }
        )
    return deepcopy(payments)


def gitlab_seed() -> dict[str, Any]:
    return {
        "projects": [
            {
                "id": "payments-api",
                "name": "Payments API",
                "application": "Payments",
                "repository": "gitlab://demo/platform/payments-api",
                "commits": [
                    {
                        "sha": "1000000",
                        "author": "Ava Chen",
                        "timestamp": "2026-09-10T08:30:00Z",
                        "message": "chore: maintain EC2 deployment scripts",
                        "files_changed": ["deploy/ec2/payments.sh"],
                    }
                ],
                "deployments": [
                    {
                        "id": "deploy-2000",
                        "environment": "production",
                        "runtime": "EC2",
                        "status": "success",
                        "timestamp": "2026-09-10T09:00:00Z",
                    }
                ],
            }
        ]
    }


def migrate_gitlab(state: dict[str, Any]) -> dict[str, Any]:
    project = state["projects"][0]
    if not any(commit["sha"] == "a83fd21" for commit in project["commits"]):
        project["commits"].insert(
            0,
            {
                "sha": "a83fd21",
                "author": "Ava Chen",
                "timestamp": now_iso(),
                "message": "feat: migrate Payments from EC2 to EKS",
                "files_changed": [
                    "k8s/payments/deployment.yaml",
                    "infra/eks/payments.tf",
                    "docs/runbooks/payments-runtime.md",
                ],
            },
        )
    if not any(deploy["id"] == "deploy-2001" for deploy in project["deployments"]):
        project["deployments"].insert(
            0,
            {
                "id": "deploy-2001",
                "environment": "production",
                "runtime": "EKS",
                "status": "success",
                "timestamp": now_iso(),
            },
        )
    return deepcopy(project)


def jira_seed() -> dict[str, Any]:
    return {
        "issues": [
            {
                "key": "PAY-4821",
                "title": "Migrate Payments workload to EKS",
                "status": "In Progress",
                "assignee": "Maya Khan",
                "created_at": "2026-09-08T09:00:00Z",
                "updated_at": "2026-09-10T09:15:00Z",
                "comments": [
                    "Preparing infrastructure changes.",
                    "Coordinating deployment window.",
                ],
                "linked_systems": ["AWS", "GitLab", "ServiceNow"],
                "application": "Payments",
            }
        ]
    }


def migrate_jira(state: dict[str, Any]) -> dict[str, Any]:
    issue = state["issues"][0]
    issue["status"] = "Done"
    issue["updated_at"] = now_iso()
    if "Migration validated in production." not in issue["comments"]:
        issue["comments"].append("Migration validated in production.")
    return deepcopy(issue)


def servicenow_seed() -> dict[str, Any]:
    return {
        "changes": [
            {
                "number": "CHG003421",
                "title": "Payments EKS Migration",
                "status": "Scheduled",
                "implementation_plan": "Cut traffic to EC2, deploy workloads to EKS, validate service health.",
                "created_at": "2026-09-08T08:00:00Z",
                "updated_at": "2026-09-10T09:00:00Z",
                "affected_application": "Payments",
            }
        ]
    }


def migrate_servicenow(state: dict[str, Any]) -> dict[str, Any]:
    change = state["changes"][0]
    change["status"] = "Closed"
    change["updated_at"] = now_iso()
    return deepcopy(change)


def confluence_seed() -> dict[str, Any]:
    pages = []
    for index, app_name in enumerate(APPLICATIONS, start=1):
        compute = "EC2" if app_name == "Payments" else _base_resources()[index - 1]["compute"]
        database = "RDS MySQL" if app_name == "Payments" else _base_resources()[index - 1]["database"]
        deployment = "EC2 deployment scripts" if app_name == "Payments" else _base_resources()[index - 1]["deployment"]
        pages.append(
            {
                "id": f"CONF-{120 + index}",
                "application": app_name,
                "title": f"{app_name} Architecture",
                "version": 17 if app_name == "Payments" else 3,
                "author": "TrueSource Seeder",
                "last_modified": "2026-09-10T09:00:00Z",
                "labels": ["architecture", _application_slug(app_name)],
                "content": (
                    f"{app_name} Architecture\n\n"
                    f"Compute: {compute}\n"
                    f"Database: {database}\n"
                    f"Deployment: {deployment}"
                ),
            }
        )
    return {"pages": pages}


def sharepoint_seed() -> dict[str, Any]:
    documents = []
    for index, app_name in enumerate(APPLICATIONS, start=1):
        compute = "EC2" if app_name == "Payments" else _base_resources()[index - 1]["compute"]
        database = "MySQL" if app_name == "Payments" else _base_resources()[index - 1]["database"]
        documents.append(
            {
                "id": f"SP-{440 + index}",
                "application": app_name,
                "title": f"{app_name} Platform Architecture",
                "version": 4 if app_name == "Payments" else 2,
                "author": "TrueSource Seeder",
                "last_modified": "2026-09-10T09:00:00Z",
                "content": (
                    f"{app_name} Platform Architecture\n\n"
                    f"Runtime: {compute}\n"
                    f"Database: {database}"
                ),
            }
        )
    return {"documents": documents}


def clone_seed(factory: Any) -> dict[str, Any]:
    return deepcopy(factory())
