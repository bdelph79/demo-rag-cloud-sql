# Registering Cymbal Air as an A2A Agent in Gemini Enterprise

## Overview

This guide covers registering the deployed Cymbal Air Cloud Run service as an external A2A agent
inside **Gemini Enterprise Agent Platform** (formerly Vertex AI Agents + Agentspace, unified at
Google Cloud Next 2026). Once registered, Gemini Enterprise can route queries to Cymbal Air,
orchestrate it alongside other agents, and surface its answers in the Gemini Enterprise chat UI.

**Prerequisites:**
- Cymbal Air deployed to Cloud Run with A2A routes enabled (see `a2a_spec.md`).
- Agent Card accessible at `GET https://cymbal-air-314706382749.us-central1.run.app/.well-known/agent-card.json`.
- A Gemini Enterprise app already created in project `gemini-enterprise-496008`.
- GCP user account with role **Gemini Enterprise Admin** (`discoveryengine.agentSpaceAdmin`) on the project.

---

## Architecture

```
User (Gemini Enterprise chat UI or API)
  │
  ▼
Gemini Enterprise Agent Platform
  ├── Reads Agent Card from Discovery Engine registry
  │
  ├── POST https://cymbal-air-314706382749.us-central1.run.app/
  │   Authorization: Bearer <SA token>    ← Gemini Enterprise SA
  │   Body: { "jsonrpc":"2.0", "method":"message/send", "params":{…} }
  │
  ▼
Cymbal Air Cloud Run (A2A endpoint)
  ├── CymbalAirA2AExecutor → LangGraph → MCP Toolbox → Cloud SQL
  └── Returns A2A task result
```

---

## Step 1 — Grant Gemini Enterprise SA access to Cloud Run

Gemini Enterprise calls your Cloud Run service using the GCP-managed service account
`service-{PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
It must have `roles/run.invoker` on the Cymbal Air service.

```bash
PROJECT_NUMBER=314706382749   # project number for gemini-enterprise-496008
REGION=us-central1

gcloud run services add-iam-policy-binding cymbal-air \
  --region=$REGION \
  --project=gemini-enterprise-496008 \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

> **Note:** If the service is currently `allUsers` (public, as deployed in this demo), this step
> is not strictly required. For production, remove `allUsers` and keep only the Gemini Enterprise SA.

---

## Step 2 — Verify the Agent Card is reachable

```bash
curl -s https://cymbal-air-314706382749.us-central1.run.app/.well-known/agent-card.json \
  | python3 -m json.tool
```

Confirm that `url`, `name`, `skills`, and `capabilities` are correct. The Gemini Enterprise
platform reads this document to populate the agent registry entry.

---

## Step 3 — Find your Gemini Enterprise App ID

You need the Engine ID of your Gemini Enterprise app:

```bash
gcloud alpha discovery-engine engines list \
  --project=gemini-enterprise-496008 \
  --location=global \
  --format="table(name,displayName,solutionType)"
```

The `name` field looks like:
`projects/gemini-enterprise-496008/locations/global/collections/default_collection/engines/YOUR_APP_ID`

The last segment (`YOUR_APP_ID`) is what you need below.

---

## Step 4A — Register via Cloud Console (UI)

1. Open [Cloud Console](https://console.cloud.google.com) → **Gemini Enterprise** (left nav).
2. Select project **gemini-enterprise** / **gemini-enterprise-496008**.
3. Open your app → click **Agents** tab → **Add agent**.
4. Select **"Custom agent via A2A"**.
5. In the **Agent Card URL** field paste:
   ```
   https://cymbal-air-314706382749.us-central1.run.app/.well-known/agent-card.json
   ```
6. Click **Preview agent details** — verify name, description, and skills load from the card.
7. **Authentication** section:
   - If Cloud Run service is IAM-protected (recommended for production): leave blank — the
     platform uses its managed SA automatically.
   - If you need OAuth: fill in Client ID, Client Secret, Auth URI, Token URI, Scopes.
8. Click **Finish**.

The agent now appears under **Agents** with status **Active**.

---

## Step 4B — Register via REST API

Use this to automate registration in CI/CD or via `gcloud`-authenticated scripts.

```bash
APP_ID="YOUR_APP_ID"   # from Step 3
PROJECT="gemini-enterprise-496008"
LOCATION="global"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT}/locations/${LOCATION}/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents" \
  -d '{
    "displayName": "Cymbal Air Assistant",
    "description": "Handles Cymbal Air flight, amenity, and policy queries via A2A.",
    "a2aAgentDefinition": {
      "agentCardUri": "https://cymbal-air-314706382749.us-central1.run.app/.well-known/agent-card.json"
    }
  }'
```

**Response** includes an `name` field like:
```
projects/gemini-enterprise-496008/locations/global/collections/default_collection/engines/YOUR_APP_ID/assistants/default_assistant/agents/AGENT_ID
```

Save `AGENT_ID` — you need it to update or delete the registration later.

---

## Step 5 — Test from Gemini Enterprise Chat

1. In Cloud Console → **Gemini Enterprise** → your app → **Preview** tab.
2. Type: `"What flights are available from SFO to NYC tomorrow?"`
3. Gemini Enterprise should route the query to Cymbal Air and display the Gemini-generated answer.
4. Check Cloud Logging to confirm the A2A call arrived at Cloud Run:
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision" resource.labels.service_name="cymbal-air" httpRequest.requestUrl:"/"' \
     --project=gemini-enterprise-496008 \
     --limit=5 \
     --format="table(timestamp,httpRequest.requestUrl,httpRequest.status)"
   ```

---

## Step 6 — Optional: Configure as Default Agent for Specific Skills

In the Gemini Enterprise app settings, you can configure **skill routing** to direct queries
matching certain tags (`flights`, `amenities`, `policy`) to Cymbal Air automatically:

1. **Agents** tab → click **Cymbal Air Assistant** → **Edit routing**.
2. Add intent patterns:
   - `flight*`, `airport*`, `book*` → route to Cymbal Air.
3. Save. Gemini Enterprise will now prefer Cymbal Air for matching queries.

---

## Update or Delete Registration

**Update** (e.g. after re-deploying with a new Agent Card):
```bash
curl -X PATCH \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT}/locations/global/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents/${AGENT_ID}?updateMask=a2aAgentDefinition" \
  -d '{
    "a2aAgentDefinition": {
      "agentCardUri": "https://cymbal-air-314706382749.us-central1.run.app/.well-known/agent-card.json"
    }
  }'
```

**Delete:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT}/locations/global/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents/${AGENT_ID}"
```

---

## IAM Roles Summary

| Principal | Role | Scope | Purpose |
|-----------|------|-------|---------|
| `service-314706382749@gcp-sa-discoveryengine.iam.gserviceaccount.com` | `roles/run.invoker` | `cymbal-air` Cloud Run service | Gemini Enterprise calls Cloud Run |
| Your admin account (`teachhubpro@gmail.com`) | `discoveryengine.agentSpaceAdmin` | Project | Register/manage agents in Gemini Enterprise |
| Cloud Run compute SA (`314706382749-compute@developer.gserviceaccount.com`) | `roles/aiplatform.user` | Project | Cymbal Air app calls Vertex AI Gemini |

---

## Sequence Diagram

```
User
 │  asks: "Flights from SFO to NYC tomorrow?"
 ▼
Gemini Enterprise Agent Platform
 │  1. Looks up registered agents in Discovery Engine
 │  2. Selects Cymbal Air (skill tag: "flights")
 │  3. POST https://cymbal-air-314706382749.us-central1.run.app/
 │     Authorization: Bearer <gcp-sa-discoveryengine token>
 │     {
 │       "jsonrpc": "2.0", "method": "message/send",
 │       "params": {
 │         "message": {
 │           "role": "user",
 │           "parts": [{"kind": "text", "text": "Flights from SFO to NYC tomorrow?"}]
 │         }
 │       }
 │     }
 ▼
Cymbal Air Cloud Run — A2A endpoint (POST /)
 │  CymbalAirA2AExecutor.execute()
 │  thread_id = task_id from context
 │  agent.user_session_invoke(thread_id, "Flights from SFO to NYC tomorrow?")
 ▼
LangGraph ReAct graph
 │  → model: ChatVertexAI (gemini-2.5-flash)
 │  → tool call: list_flights(departure="SFO", arrival="NYC", date="2026-05-19")
 ▼
MCP Toolbox (sidecar, port 5000)
 │  → SQL: SELECT * FROM flights WHERE departure_airport='SFO' AND DATE(departure_time)='2026-05-19'
 ▼
Cloud SQL MySQL — flights table
 │  returns matching rows
 ▼
LangGraph → formats answer
 ▼
CymbalAirA2AExecutor
 │  event_queue.enqueue_event(new_agent_text_message(formatted_answer))
 ▼
A2A JSON-RPC response:
 │  { "result": { "id": "task-uuid", "status": {"state": "completed"},
 │    "artifacts": [{"parts": [{"kind": "text", "text": "Here are the flights…"}]}] }}
 ▼
Gemini Enterprise
 │  surfaces answer in chat UI
 ▼
User sees: "Here are the available flights from SFO to NYC tomorrow: …"
```

---

## References

- [A2A protocol spec](https://a2a-protocol.org/latest/)
- [a2a-sdk Python SDK](https://github.com/a2aproject/a2a-python)
- [Register and manage A2A agents — Gemini Enterprise docs](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent)
- [Use an A2A agent — Gemini Enterprise Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/use-an-a2a-agent)
- [Cymbal Air A2A implementation spec](a2a_spec.md)
