from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class ConversationState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    intent: str
    next_node: str
    phase: str
    draft: dict
    appointment_id: int | None
    confirmation_key: str | None
    channel: str
    current_agent: str
