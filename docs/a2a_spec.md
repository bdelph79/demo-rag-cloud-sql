# A2A Integration Spec — Cymbal Air App

## Overview

This document specifies the changes needed to expose the Cymbal Air agentic app as an
[Agent-to-Agent (A2A)](https://github.com/a2aproject/A2A) server so that external orchestrators
(e.g. Gemini Enterprise Agent Platform) can invoke it programmatically over the A2A protocol.

**A2A protocol version:** 1.0  
**SDK:** `a2a-sdk==1.0.3` (PyPI, May 2026)  
**Approach:** Mount A2A routes alongside the existing FastAPI routes. No existing routes change.

---

## What Gets Added

Two new HTTP endpoints on the existing Cloud Run service:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent-card.json` | GET | A2A discovery — returns the Agent Card JSON |
| `/` | POST | A2A task endpoint — JSON-RPC 2.0 for `message/send`, `message/stream`, `tasks/get`, `tasks/cancel` |

The existing `POST /chat` route is **unchanged** and continues to serve the browser UI.

---

## Architecture After Change

```
Cloud Run: cymbal-air
├── GET/POST  /                   ← A2A task handler (NEW)
├── GET       /.well-known/agent-card.json  ← A2A discovery (NEW)
├── GET/POST  /  (index)          ← existing browser UI (unchanged)
├── POST      /chat               ← existing browser chat (unchanged)
├── POST      /login/google       ← existing (unchanged)
└── ...

Sidecar: toolbox (port 5000, unchanged)
```

**A2A call flow:**
```
Gemini Enterprise
  │  POST /  {"jsonrpc":"2.0","method":"message/send","params":{…}}
  ▼
CymbalAirA2AExecutor.execute()
  │  await agent.user_session_invoke(task_id, user_text)
  ▼
LangGraph ReAct graph (MemorySaver, thread_id=task_id)
  │  tool calls via MCP Toolbox
  ▼
Cloud SQL (airports / amenities / flights / policies)
  │
  ▼ response text
event_queue.enqueue_event(new_agent_text_message(result))
```

---

## File Changes

### 1. `requirements.txt` — add dependency

```
a2a-sdk==1.0.3
```

### 2. `agent/a2a_executor.py` — new file

```python
from typing import Any
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from agent.agent import Agent


class CymbalAirA2AExecutor(AgentExecutor):
    """Bridges A2A task requests to the existing LangGraph ReAct agent."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Use A2A task_id as the LangGraph thread_id for per-conversation memory.
        # Fall back to a fresh UUID if no task ID is available yet.
        thread_id: str = context.task_id or str(uuid.uuid4())

        # Ensure the agent session exists (loads tools, builds graph on first call).
        fake_session: dict[str, Any] = {"uuid": thread_id, "history": [], "user_info": None}
        await self._agent.user_session_create(fake_session)

        # Extract the user's text from the A2A message parts.
        user_text = context.get_user_input()
        if not user_text:
            await event_queue.enqueue_event(
                new_agent_text_message("Please provide a message.")
            )
            return

        # Invoke the LangGraph agent.
        response = await self._agent.user_session_invoke(thread_id, user_text)
        output: str = response.get("output", "")

        # If the graph paused for a booking confirmation, surface it as text.
        # Full human-in-the-loop via A2A `input_required` state is a follow-up (see §Caveats).
        if response.get("confirmation"):
            conf = response["confirmation"]
            params = conf.get("params", {})
            output = (
                f"{output}\n\n"
                f"**Booking confirmation required.**\n"
                f"Flight: {params.get('airline','')} {params.get('flight_number','')}, "
                f"{params.get('departure_airport','')} → {params.get('arrival_airport','')}, "
                f"departing {params.get('departure_time','')}.\n"
                f"Reply 'confirm' to book or 'cancel' to abort."
            )

        await event_queue.enqueue_event(new_agent_text_message(output))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")
```

### 3. `app.py` — mount A2A routes

Add the following imports at the top of `app.py` alongside existing imports:

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent.a2a_executor import CymbalAirA2AExecutor
```

Add a helper that builds the A2A app and mounts it. Call this inside `init_app()` after
the existing routes are registered, before returning `app`:

```python
def _mount_a2a(app: FastAPI, agent: Agent, base_url: str) -> None:
    """Register A2A discovery and task endpoints on the existing FastAPI app."""
    skills = [
        AgentSkill(
            id="airport_search",
            name="Airport Search",
            description="Search airports by name, city, or country.",
            tags=["airports"],
            examples=["Find airports in Japan", "What is the IATA code for Heathrow?"],
        ),
        AgentSkill(
            id="flight_search",
            name="Flight Search",
            description="List available flights by route and date, or look up a flight by number.",
            tags=["flights"],
            examples=["Flights from SFO to JFK tomorrow", "What gate is CY 0456 departing from?"],
        ),
        AgentSkill(
            id="amenity_search",
            name="SFO Amenity Search",
            description="Find airport amenities at SFO (shops, restaurants, lounges) near a gate.",
            tags=["amenities", "sfo"],
            examples=["Coffee near gate A6", "Luxury shops in Terminal 2"],
        ),
        AgentSkill(
            id="policy_search",
            name="Cymbal Air Policy",
            description="Answer questions about Cymbal Air passenger policies.",
            tags=["policy", "baggage", "check-in"],
            examples=["What is the baggage allowance?", "Can I change my ticket?"],
        ),
    ]

    agent_card = AgentCard(
        name="Cymbal Air Assistant",
        description=(
            "Cymbal Air customer service assistant — answers flight, amenity, "
            "and policy questions, and supports flight booking."
        ),
        url=base_url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
    )

    handler = DefaultRequestHandler(
        agent_executor=CymbalAirA2AExecutor(agent),
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    )
    a2a_app.add_routes_to_app(app)
```

In `init_app()`, after registering the existing router and before `return app`, add:

```python
# A2A: derive base_url from SERVICE_URL env var (set this in Cloud Run env vars).
import os as _os
_base_url = _os.getenv("SERVICE_URL", "http://localhost:8081") + "/"
_mount_a2a(app, agent, _base_url)
```

### 4. `service.yaml` — add `SERVICE_URL` env var

In the `app` container's `env` list, add:

```yaml
- name: SERVICE_URL
  value: "https://cymbal-air-314706382749.us-central1.run.app"
```

---

## New Environment Variable

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `SERVICE_URL` | Yes | `https://cymbal-air-314706382749.us-central1.run.app` | Embedded in Agent Card `url` field so A2A clients know where to POST tasks |

---

## Agent Card (rendered)

`GET /.well-known/agent-card.json` will return:

```json
{
  "protocolVersion": "1.0",
  "name": "Cymbal Air Assistant",
  "description": "Cymbal Air customer service assistant — answers flight, amenity, and policy questions, and supports flight booking.",
  "url": "https://cymbal-air-314706382749.us-central1.run.app/",
  "version": "1.0.0",
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "capabilities": { "streaming": false },
  "skills": [
    {"id": "airport_search",  "name": "Airport Search",     "tags": ["airports"]},
    {"id": "flight_search",   "name": "Flight Search",      "tags": ["flights"]},
    {"id": "amenity_search",  "name": "SFO Amenity Search", "tags": ["amenities","sfo"]},
    {"id": "policy_search",   "name": "Cymbal Air Policy",  "tags": ["policy","baggage"]}
  ]
}
```

---

## Caveats and Known Limitations

### 1. Booking requires login
The `insert_ticket` / `list_tickets` tools require a `user_id`, `user_name`, and `user_email` bound
at tool-call time via LangGraph's auth token getter. An A2A caller (Gemini Enterprise SA) is not a
human user and will not have a Google Sign-In session. Two options:

- **Option A (recommended for Gemini Enterprise):** Remove `insert_ticket` and `list_tickets` from
  the A2A executor's available tools. Keep those skills browser-only.
- **Option B (full A2A booking):** Accept user identity as structured A2A message metadata and pass
  it into the graph config via `fake_session["user_info"]`.

### 2. Booking confirmation loop (A2A `input_required`)
The LangGraph graph uses `interrupt_after=["booking_validation"]` which pauses execution and
expects a human confirmation. In the current executor, confirmation is surfaced as a text message
asking the user to reply "confirm". Full A2A human-in-the-loop support requires:
1. After `booking_validation` interrupt: return `TaskState.input_required` (not `completed`).
2. On the next A2A message to the same task ID: call `user_session_invoke(thread_id, None)` to
   resume the interrupted graph if user confirmed, or reset state if cancelled.
This is a follow-up implementation; the current spec surfaces the confirmation as a text message.

### 3. In-memory task store
`InMemoryTaskStore` does not survive Cloud Run cold starts or scale-out. For production:
- Use Firestore or Cloud SQL as the task store by implementing `a2a.server.tasks.TaskStore`.
- Or pin the Cloud Run service to min-instances=1 if state loss is acceptable.

### 4. Streaming
The Agent Card advertises `streaming: false`. Streaming requires switching from
`message/send` to `message/stream` (SSE) and using `EventQueue` in a background task while
returning a streaming response. This is straightforward to add with `a2a-sdk` once the non-streaming
path is validated.

---

## Verification

After deploying with the changes above:

```bash
URL="https://cymbal-air-314706382749.us-central1.run.app"

# 1. Agent Card discovery
curl -s "$URL/.well-known/agent-card.json" | python3 -m json.tool

# 2. A2A message/send (no auth — service is public for demo)
curl -s -X POST "$URL/" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What flights go from SFO to NYC tomorrow?"}],
        "messageId": "msg-001"
      }
    }
  }' | python3 -m json.tool

# Expected: response with "result.status.state": "completed" and artifact text from Gemini
```
