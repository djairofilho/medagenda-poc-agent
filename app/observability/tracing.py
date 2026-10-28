"""Privacy boundary for Langfuse's OpenTelemetry export."""

import hashlib
import json
import re
import subprocess
from contextlib import contextmanager

from app import config

ROUTES = frozenset({"scheduling", "information", "triage", "unknown"})
PHASES = frozenset({"none", "collecting", "awaiting_confirmation", "booked"})
BOOKING_STATUSES = frozenset({"booked", "already_booked", "unavailable", "invalid", "no_attempt"})
PROMPT_NAMES = frozenset({"classification", "extraction", "information", "triage"})
PROMPT_SOURCES = frozenset({"production", "local"})
ERROR_CATEGORIES = frozenset({"timeout", "dependency", "persistence", "validation", "internal"})
ENVIRONMENTS = frozenset({"default", "development", "staging", "production", "test", "sdk-experiment"})
OBSERVATION_TYPES = frozenset({"span", "generation", "agent", "chain", "tool", "retriever", "evaluator", "guardrail", "embedding"})
OBSERVATION_NAMES = frozenset({
    "medagenda-chat", "router", "scheduling", "information", "triage",
    "classification", "extraction", "classify", "extract",
    "codex-cli-classify", "codex-cli-extract", "codex-cli-information", "codex-cli-triage",
    "ChatOpenAI", "ChatGoogleGenerativeAI", "RunnableSequence", "RunnableLambda",
    "RunnableCallable",
    "experiment-item-run", "experiment-item-task", "experiment-item-evaluation",
    "route_score", "booking_score", "safety_score", "quality_score",
})
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_./:-]{0,79}\Z")
_VERSION = re.compile(r"(?:[0-9]{1,8}|v[0-9]{1,8}|local)\Z")
_HEX_SESSION = re.compile(r"[0-9a-f]{64}\Z")
_HEX_16 = re.compile(r"[0-9a-f]{16}\Z")
_HEX_40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX_12 = re.compile(r"[0-9a-f]{12}\Z")
_EXPERIMENT_NAME = re.compile(r"medagenda-(?:v?[0-9]{1,8}|local)-[0-9a-f]{8}\Z")
_SCENARIO = re.compile(r"[a-z][a-z0-9_]{0,79}\Z")
_EXPERIMENT_ITEMS = frozenset({"experiment-item-run", "experiment-item-task"})
_TOKEN_KEYS = frozenset({"input", "output", "total", "cache_read_input_tokens", "cache_creation_input_tokens", "input_tokens", "output_tokens", "total_tokens"})
_COST_KEYS = frozenset({"input", "output", "total"})


def _json_scalar(value):
    """Langfuse stores metadata values as JSON encoded OTel strings."""
    if not isinstance(value, str) or len(value) > 256:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _valid_structured(value, keys, *, integer):
    if not isinstance(value, str) or len(value) > 1024:
        return False
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return False
    if not isinstance(parsed, dict) or not parsed or not set(parsed) <= keys:
        return False
    for amount in parsed.values():
        if isinstance(amount, bool) or not isinstance(amount, int if integer else (int, float)):
            return False
        if not 0 <= amount <= 1_000_000_000:
            return False
    return True


def _valid_experiment_metadata(value):
    if not isinstance(value, str) or len(value) > 1024:
        return False
    try:
        metadata = json.loads(value)
    except (TypeError, ValueError):
        return False
    if not isinstance(metadata, dict) or set(metadata) != {
        "code_version", "prompt_version", "prompt_versions", "dataset_version", "model"
    }:
        return False
    versions = metadata["prompt_versions"]
    return (
        isinstance(metadata["code_version"], str) and bool(_HEX_40.fullmatch(metadata["code_version"]))
        and isinstance(metadata["dataset_version"], str) and bool(_HEX_12.fullmatch(metadata["dataset_version"]))
        and isinstance(metadata["prompt_version"], str) and bool(_VERSION.fullmatch(metadata["prompt_version"]))
        and isinstance(metadata["model"], str) and bool(_IDENTIFIER.fullmatch(metadata["model"]))
        and isinstance(versions, dict) and set(versions) == PROMPT_NAMES
        and all(isinstance(version, str) and bool(_VERSION.fullmatch(version)) for version in versions.values())
    )


def _valid_experiment_io(key, value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        payload = json.loads(value)
    except (TypeError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False
    if key == "langfuse.observation.input":
        return (set(payload) == {"id"} and isinstance(payload["id"], str)
                and bool(_SCENARIO.fullmatch(payload["id"])))
    allowed = {"route", "booking_status", "bookings", "false_claim",
               "emergency_guidance", "clinical_boundary", "route_correct",
               "booking_integrity", "clinical_safety", "quality"}
    if not payload or not set(payload) <= allowed:
        return False
    for field, item in payload.items():
        if field == "route" and (not isinstance(item, str) or item not in ROUTES):
            return False
        if field == "booking_status" and (not isinstance(item, str) or item not in BOOKING_STATUSES):
            return False
        if field == "bookings" and (type(item) is not int or not 0 <= item <= 1000):
            return False
        if field in {"false_claim", "emergency_guidance", "clinical_boundary",
                     "route_correct", "booking_integrity", "clinical_safety"} and type(item) is not bool:
            return False
        if field == "quality" and (not isinstance(item, dict)
                                   or set(item) != {"clarity", "instruction_adherence"}
                                   or any(type(score) is not int or not 1 <= score <= 5
                                          for score in item.values())):
            return False
    return True


def _safe_attribute(key, value):
    if key == "langfuse.internal.is_app_root":
        return isinstance(value, bool)
    if key == "session.id":
        return isinstance(value, str) and bool(_HEX_SESSION.fullmatch(value))
    if key == "langfuse.trace.name":
        return value == "medagenda-chat"
    if key == "langfuse.environment":
        return isinstance(value, str) and value in ENVIRONMENTS
    if key == "langfuse.observation.type":
        return isinstance(value, str) and value in OBSERVATION_TYPES
    if key == "langfuse.observation.level":
        return isinstance(value, str) and value in {"DEBUG", "DEFAULT", "WARNING", "ERROR"}
    if key == "langfuse.observation.name":
        return isinstance(value, str) and value in OBSERVATION_NAMES
    if key == "langfuse.observation.prompt.name":
        return isinstance(value, str) and value in PROMPT_NAMES
    if key == "langfuse.observation.prompt.version":
        return type(value) is int and 0 < value <= 1_000_000
    if key in {"langfuse.experiment.id", "langfuse.experiment.item.id",
               "langfuse.experiment.item.root_observation_id"}:
        return isinstance(value, str) and bool(_HEX_16.fullmatch(value))
    if key == "langfuse.experiment.name":
        return isinstance(value, str) and bool(_EXPERIMENT_NAME.fullmatch(value))
    if key == "langfuse.experiment.metadata":
        return _valid_experiment_metadata(value)
    if key in {"langfuse.observation.model.name", "gen_ai.request.model", "gen_ai.response.model"}:
        return isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))
    if key in {"langfuse.observation.usage_details", "langfuse.observation.cost_details"}:
        return _valid_structured(value, _TOKEN_KEYS if key.endswith("usage_details") else _COST_KEYS,
                                 integer=key.endswith("usage_details"))
    if key in {"gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens"}:
        return type(value) is int and 0 <= value <= 1_000_000_000
    if key.startswith(("langfuse.trace.metadata.", "langfuse.observation.metadata.")):
        field = key.rsplit(".", 1)[-1]
        scalar = _json_scalar(value)
        if field == "model":
            return isinstance(scalar, str) and bool(_IDENTIFIER.fullmatch(scalar))
        if field == "prompt_name":
            return isinstance(scalar, str) and scalar in PROMPT_NAMES
        if field == "prompt_version":
            return isinstance(scalar, str) and bool(_VERSION.fullmatch(scalar))
        if field == "prompt_versions":
            return (isinstance(scalar, dict) and set(scalar) == PROMPT_NAMES
                    and all((type(version) is int and 0 < version <= 1_000_000)
                            or (isinstance(version, str) and bool(_VERSION.fullmatch(version)))
                            for version in scalar.values()))
        if field == "prompt_source":
            return isinstance(scalar, str) and scalar in PROMPT_SOURCES
        if field == "route":
            return isinstance(scalar, str) and scalar in ROUTES
        if field == "phase":
            return isinstance(scalar, str) and scalar in PHASES
        if field == "booking_status":
            return isinstance(scalar, str) and scalar in BOOKING_STATUSES
        if field == "technical_success":
            return type(scalar) is bool
        if field == "error_category":
            return isinstance(scalar, str) and scalar in ERROR_CATEGORIES
    if key == "langfuse.trace.version":
        return isinstance(value, str) and bool(_VERSION.fullmatch(value))
    return False


def should_export_span(span) -> bool:
    """Exception events can contain patient text and cannot be patched by the SDK."""
    return (not span.events and not span.links
            and not getattr(getattr(span, "status", None), "description", None)
            and getattr(getattr(span, "instrumentation_scope", None), "name", None) == "langfuse-sdk"
            and span.name in OBSERVATION_NAMES)


def mask_otel_spans(*, params):
    """Export only validated, finite operational dimensions."""
    from langfuse.types import MaskOtelSpansResult, OtelSpanPatch

    patches = {}
    for identifier, span in params.spans.items():
        delete = tuple(
            key for key, value in span.attributes.items()
            if not ((span.name in _EXPERIMENT_ITEMS
                     and key in {"langfuse.observation.input", "langfuse.observation.output"}
                     and _valid_experiment_io(key, value)) or _safe_attribute(key, value))
        )
        if delete:
            patches[identifier] = OtelSpanPatch(delete_attributes=delete)
    return MaskOtelSpansResult(span_patches=patches)


def _error_category(exc: Exception) -> str:
    if isinstance(exc, TimeoutError) or isinstance(exc.__cause__, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, (ConnectionError, OSError)):
        return "dependency"
    if isinstance(exc, (ValueError, KeyError, TypeError)):
        return "validation"
    try:
        from sqlalchemy.exc import SQLAlchemyError
        if isinstance(exc, SQLAlchemyError):
            return "persistence"
    except ImportError:
        pass
    return "internal"


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
        failure = None
        with self.client.start_as_current_observation(as_type="span", name="medagenda-chat"):
            with propagate_attributes(
                trace_name="medagenda-chat", session_id=safe_session,
                metadata={"model": model_name},
            ):
                try:
                    yield [CallbackHandler(public_key=config.LANGFUSE_PUBLIC_KEY)]
                except Exception as exc:
                    # Exit the observation normally: the SDK otherwise stores the
                    # exception message and stack in an unpatchable OTel event.
                    failure = exc
                    self.client.update_current_span(
                        level="ERROR", metadata={"route": "unknown", "phase": "none",
                                                 "booking_status": "no_attempt",
                                                 "technical_success": False,
                                                 "error_category": _error_category(exc)},
                    )
                    self.client.score_current_trace(name="technical_success", value=0, data_type="BOOLEAN")
        if failure is not None:
            raise failure

    def record_result(self, state: dict):
        route = state.get("intent")
        phase = state.get("phase")
        booking_status = state.get("booking_status")
        route = route if route in ROUTES else "unknown"
        phase = phase if phase in PHASES else "none"
        booking_status = booking_status if booking_status in BOOKING_STATUSES else "no_attempt"
        self.client.update_current_span(metadata={
            "route": route, "phase": phase, "booking_status": booking_status,
            "technical_success": True,
        })
        self.client.score_current_trace(name="technical_success", value=1, data_type="BOOLEAN")
        if booking_status != "no_attempt":
            confirmed = booking_status in {"booked", "already_booked"}
            self.client.score_current_trace(name="booking_confirmed", value=int(confirmed), data_type="BOOLEAN")
            integrity = (bool(state.get("appointment_id")) and phase == "booked") if confirmed else phase != "booked"
            self.client.score_current_trace(name="booking_integrity", value=int(integrity), data_type="BOOLEAN")

    def shutdown(self):
        self.client.flush()


def make_tracer():
    if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
        return LangfuseTracer()
    return None
