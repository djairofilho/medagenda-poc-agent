"""Application entry point for one durable chat turn."""

from langchain_core.messages import HumanMessage

from app.conversations.graph import build_graph


class ConversationService:
    def __init__(self, *, model, session_factory, checkpointer, tracer=None):
        self.model = model
        self.tracer = tracer
        self.graph = build_graph(model=model, session_factory=session_factory, checkpointer=checkpointer)
        self.checkpointer = checkpointer

    @staticmethod
    def _config(session_id: str, callbacks=None) -> dict:
        config = {"configurable": {"thread_id": session_id}, "run_name": "medagenda-chat"}
        if callbacks:
            config["callbacks"] = callbacks
        return config

    def process_message(self, session_id: str, message: str, channel: str) -> str:
        payload = {"messages": [HumanMessage(content=message)], "channel": channel}
        if not self.tracer:
            result = self.graph.invoke(payload, config=self._config(session_id))
        else:
            with self.tracer.trace_turn(session_id, self.model.model_name) as callbacks:
                result = self.graph.invoke(payload, config=self._config(session_id, callbacks))
                self.tracer.record_result(result)
        return str(result["messages"][-1].content)

    def state(self, session_id: str) -> dict:
        snapshot = self.graph.get_state(self._config(session_id))
        return snapshot.values or {}

    def reset(self, session_id: str) -> None:
        self.checkpointer.delete_thread(session_id)
