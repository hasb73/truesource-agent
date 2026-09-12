# 3-minute judge demo

## 0:00 Problem

Ask:

"How is Payments deployed?"

Call out that the answer still says EC2 because the current verified knowledge is stale.

## 0:30 Reality changes

Click one of the scenario triggers, for example `Simulate Migration -> EKS`.

Call out that you can also trigger `Simulate DB Modernization`, `Simulate Region Failover`, and `Simulate GitOps Rollout`.

This updates operational and workflow evidence in the AWS, GitLab, Jira, and ServiceNow mock services.

## 0:50 Agent detects drift

Click `Run Scan`.

Highlight the live activity rail:

1. AWS checked
2. GitLab checked
3. Jira checked
4. ServiceNow checked
5. Confluence contradicts operational state
6. SharePoint contradicts operational state

## 1:30 Verify

Open the incident details and show:

1. EC2 -> EKS
2. confidence score
3. supporting and contradicting sources
4. proposed Confluence and SharePoint diffs

## 2:00 Human approval

Click `Approve & refresh verified RAG`.

Show that the documents update and the audit trail records the action.

## 2:20 Ask again

Ask the same question again.

Show the trust card with verified-at time, confidence, sources, and updated docs.

## 2:30 Documentation portal

Open `/portal` and show the Confluence-style mock workspace with searchable pages and SharePoint mirrors.

## 2:40 Closing

"Companies have two realities: what they do and what they say. TrueSource continuously reconciles them before AI consumes them."
