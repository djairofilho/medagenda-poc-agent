"""Langfuse integration. Free-text span attributes never leave this process."""

import hashlib
from contextlib import contextmanager

from app import config

SAFE_STRING_ATTRIBUTES = {
    "langfuse.trace.name",
    "langfuse.trace.session_id",
    "langfuse.trace.version",
    "langfuse.observation.name",
    "langfuse.trace.metadata.model",
    "langfuse.trace.metadata.prompt_version",
    "langfuse.observation.metadata.model",
    "langfuse.observation.metadata.prompt_version",
    "langfuse.observation.metadata.route",
    "langfuse.observation.metadata.phase",
    "langfuse.observation.metadata.booking_status",
}


def should_export_span(span) -> bool:
    """OpenTelemetry events cannot be masked by the SDK; discard text-bearing ones."""
    for event in span.events or ():
        if any(
            isinstance(value, str) or isinstance(value, (tuple, list)) and any(isinstance(item, str) for item in value)
            for value in (event.attributes or {}).values()
        ):
            return False
    return True


def mask_otel_spans(*, params):
    """Allowlist safe dimensions and preserve numeric token/cost/duration fields."""
    from langfuse.types import MaskOtelSpansResult, OtelSpanPatch

    patches = {}
    for identifier, span in params.spans.items():
        sensitive = tuple(
            key for key, value in span.attributes.items()
            if (isinstance(value, str) or
                isinstance(value, (tuple, list)) and any(isinstance(item, str) for item in value))
            and key not in SAFE_STRING_ATTRIBUTES
        )
        if sensitive:
            patches[identifier] = OtelSpanPatch(
                delete_attributes=sensitive, set_attributes={"medagenda.masking.applied": True}
            )
    return MaskOtelSpansResult(span_patches=patches)


class LangfuseTracer:
    def __init__(self):
        from langfuse import Langfuse

        self.client = Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            base_url=config.LANGFUSE_BASE_URL,
            mask_otel_spans=mask_otel_spans,
            should_export_span=should_export_span,
        )

    @contextmanager
    def trace_turn(self, session_id: str, model_name: str):
        from langfuse import propagate_attributes
        from langfuse.langchain import CallbackHandler

        safe_session = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        with self.client.start_as_current_observation(as_type="span", name="medagenda-chat"):
            with propagate_attributes(
                trace_name="medagenda-chat", session_id=safe_session,
                metadata={"model": model_name, "prompt_version": config.PROMPT_VERSION},
            ):
                yield [CallbackHandler(public_key=config.LANGFUSE_PUBLIC_KEY)]

    def record_result(self, state: dict):
        self.client.update_current_span(metadata={
            "route": state.get("intent", "unknown"),
            "phase": state.get("phase", "none"),
            "booking_status": "confirmed" if state.get("appointment_id") else "none",
        })

    def shutdown(self):
        self.client.flush()


def make_tracer():
    if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
        return LangfuseTracer()
    return None
