from typing import Any, AsyncGenerator
import uuid
import json

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_task_status_update
from a2a.types import TaskStatus

from agent.agent import Agent


class CymbalAirA2AExecutor(AgentExecutor):
    """Bridges A2A task requests to the existing LangGraph ReAct agent."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Use A2A task_id as the LangGraph thread_id for per-conversation memory.
        thread_id: str = context.task_id or str(uuid.uuid4())

        # Ensure the agent session exists.
        fake_session: dict[str, Any] = {"uuid": thread_id, "history": [], "user_info": None}
        await self._agent.user_session_create(fake_session)

        # Extract the user's text from the A2A message parts.
        user_text = context.get_user_input()
        if not user_text:
            await event_queue.enqueue_event(
                new_agent_text_message("Please provide a message.")
            )
            return

        # Use streaming to support Gemini Enterprise "Thoughts" UI.
        async for event in self._agent.user_session_stream(thread_id, user_text):
            # Map LangGraph events to A2A events with 'adk_thoughts' metadata.
            # This is critical for rendering in Gemini Enterprise.
            if event["type"] == "node_start" and event["node"] == "tools":
                await event_queue.enqueue_event(
                    new_task_status_update(
                        status=TaskStatus.RUNNING,
                        message="Consulting database...",
                        metadata={
                            "adk_thoughts": [
                                {
                                    "thought": "I need to check the database for relevant information.",
                                    "state": "thinking"
                                }
                            ]
                        }
                    )
                )
            elif event["type"] == "tool_start":
                await event_queue.enqueue_event(
                    new_task_status_update(
                        status=TaskStatus.RUNNING,
                        message=f"Running tool: {event['tool']}",
                        metadata={
                            "adk_thoughts": [
                                {
                                    "thought": f"Calling tool {event['tool']} with arguments {event['inputs']}",
                                    "state": "thinking"
                                }
                            ]
                        }
                    )
                )
            elif event["type"] == "tool_end":
                await event_queue.enqueue_event(
                    new_task_status_update(
                        status=TaskStatus.RUNNING,
                        message=f"Tool {event['tool']} finished.",
                        metadata={
                            "adk_thoughts": [
                                {
                                    "thought": f"Tool {event['tool']} returned result.",
                                    "state": "thinking"
                                }
                            ]
                        }
                    )
                )
            elif event["type"] == "final_answer":
                output: str = event["output"]
                await event_queue.enqueue_event(new_agent_text_message(output))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")
