from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PAYMENTS_SCENARIOS = {
    "eks_migration": {
        "name": "EKS Migration",
        "summary": "Move Payments compute from EC2 to EKS and align deployment tooling.",
    },
    "database_modernization": {
        "name": "Database Modernization",
        "summary": "Upgrade Payments database from RDS MySQL to Aurora PostgreSQL.",
    },
    "region_failover": {
        "name": "Region Failover",
        "summary": "Fail over Payments from me-central-1 to eu-west-1.",
    },
    "gitops_rollout": {
        "name": "GitOps Rollout",
        "summary": "Switch Payments deployment flow from scripts to Argo CD.",
    },
}

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
    return apply_aws_scenario(state, "eks_migration")


def list_scenarios() -> list[dict[str, str]]:
    return [
        {"id": scenario_id, "name": data["name"], "summary": data["summary"]}
        for scenario_id, data in PAYMENTS_SCENARIOS.items()
    ]


def apply_aws_scenario(state: dict[str, Any], scenario: str) -> dict[str, Any]:
    resources = state["resources"]
    payments = next(item for item in resources if item["application"] == "Payments")

    change_summary = "Payments infrastructure updated"
    if scenario == "eks_migration":
        payments["compute"] = "EKS"
        payments["database"] = "RDS PostgreSQL"
        payments["deployment"] = "GitLab CI/CD"
        change_summary = "Payments migrated from EC2 to EKS"
    elif scenario == "database_modernization":
        payments["database"] = "Aurora PostgreSQL"
        change_summary = "Payments database modernized to Aurora PostgreSQL"
    elif scenario == "region_failover":
        payments["region"] = "eu-west-1"
        change_summary = "Payments failed over from me-central-1 to eu-west-1"
    elif scenario == "gitops_rollout":
        payments["deployment"] = "Argo CD"
        change_summary = "Payments deployment flow migrated to Argo CD"
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    change_id = f"aws-change-{scenario}"
    if not any(change["id"] == change_id for change in state["changes"]):
        state["changes"].append(
            {
                "id": change_id,
                "application": "Payments",
                "summary": change_summary,
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
    return apply_gitlab_scenario(state, "eks_migration")


def apply_gitlab_scenario(state: dict[str, Any], scenario: str) -> dict[str, Any]:
    project = state["projects"][0]
    if scenario == "eks_migration":
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
    elif scenario == "database_modernization":
        project["commits"].insert(
            0,
            {
                "sha": "b91ca42",
                "author": "Ava Chen",
                "timestamp": now_iso(),
                "message": "feat: move Payments database to Aurora PostgreSQL",
                "files_changed": [
                    "infra/rds/payments-aurora.tf",
                    "app/config/database.yaml",
                ],
            },
        )
    elif scenario == "region_failover":
        project["commits"].insert(
            0,
            {
                "sha": "c73fd14",
                "author": "Ava Chen",
                "timestamp": now_iso(),
                "message": "ops: fail over Payments to eu-west-1",
                "files_changed": [
                    "infra/regions/payments-eu-west-1.tf",
                    "runbooks/failover.md",
                ],
            },
        )
    elif scenario == "gitops_rollout":
        project["commits"].insert(
            0,
            {
                "sha": "d32ee8a",
                "author": "Ava Chen",
                "timestamp": now_iso(),
                "message": "feat: adopt Argo CD for Payments deployments",
                "files_changed": [
                    "argocd/payments/application.yaml",
                    "deploy/ec2/payments.sh",
                ],
            },
        )
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
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
    return apply_jira_scenario(state, "eks_migration")


def apply_jira_scenario(state: dict[str, Any], scenario: str) -> dict[str, Any]:
    issue = state["issues"][0]
    issue["status"] = "Done"
    issue["updated_at"] = now_iso()
    if scenario == "eks_migration":
        comment = "Migration validated in production."
    elif scenario == "database_modernization":
        comment = "Aurora PostgreSQL cutover validated in production."
    elif scenario == "region_failover":
        comment = "Regional failover to eu-west-1 validated by on-call."
    elif scenario == "gitops_rollout":
        comment = "Argo CD rollout completed and validated."
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    if comment not in issue["comments"]:
        issue["comments"].append(comment)
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
    return apply_servicenow_scenario(state, "eks_migration")


def apply_servicenow_scenario(state: dict[str, Any], scenario: str) -> dict[str, Any]:
    change = state["changes"][0]
    change["status"] = "Closed"
    if scenario == "eks_migration":
        change["implementation_plan"] = "Cut traffic to EC2, deploy workloads to EKS, validate service health."
    elif scenario == "database_modernization":
        change["implementation_plan"] = "Migrate database from RDS MySQL to Aurora PostgreSQL and validate replication."
    elif scenario == "region_failover":
        change["implementation_plan"] = "Shift production traffic from me-central-1 to eu-west-1 and validate latency."
    elif scenario == "gitops_rollout":
        change["implementation_plan"] = "Replace script-based deployments with Argo CD sync waves."
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
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
                    f"Region: {_base_resources()[index - 1]['region']}\n"
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
                    f"Database: {database}\n"
                    f"Region: {_base_resources()[index - 1]['region']}"
                ),
            }
        )
    return {"documents": documents}


def clone_seed(factory: Any) -> dict[str, Any]:
    return deepcopy(factory())
