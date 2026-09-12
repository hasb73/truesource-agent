from backend.app import agent


def test_deterministic_analysis_detects_migration(monkeypatch):
    monkeypatch.setattr(
        agent,
        "collect_evidence",
        lambda application="Payments": {
            "application": application,
            "collected_at": "2026-09-12T10:00:00Z",
            "aws": {"compute": "EKS", "database": "RDS PostgreSQL"},
            "gitlab_commits": [{"message": "feat: migrate Payments from EC2 to EKS"}],
            "gitlab_deployments": [{"runtime": "EKS", "timestamp": "2026-09-12T10:00:00Z"}],
            "jira": {"status": "Done", "updated_at": "2026-09-12T10:00:00Z"},
            "servicenow": {"status": "Closed", "updated_at": "2026-09-12T10:00:00Z"},
            "confluence": {
                "id": "CONF-121",
                "title": "Payments Architecture",
                "content": "Payments Architecture\n\nCompute: EC2\nDatabase: RDS MySQL\nDeployment: EC2 deployment scripts",
                "last_modified": "2026-09-10T10:00:00Z",
            },
            "sharepoint": {
                "id": "SP-441",
                "title": "Payments Platform Architecture",
                "content": "Payments Platform Architecture\n\nRuntime: EC2\nDatabase: MySQL",
                "last_modified": "2026-09-10T10:00:00Z",
            },
        },
    )
    monkeypatch.setattr(agent, "run_json_prompt", lambda *args, **kwargs: None)

    result = agent.deterministic_analysis()

    assert result["drift_detected"] is True
    assert result["observed_value"] == "EKS"
    assert result["documented_value"] == "EC2"
    assert result["confidence"] >= 0.85
    assert len(result["proposed_changes"]) == 2
