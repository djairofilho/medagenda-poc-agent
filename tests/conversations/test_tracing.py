import hashlib
import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from langfuse.types import OtelSpanIdentifier, OtelSpanData, MaskOtelSpansParams
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.observability.tracing import OBSERVATION_NAMES, LangfuseTracer, mask_otel_spans, should_export_span
from app.availability.service import LOCAL_TZ


def test_span_masking_drops_identifiers_and_clinical_content():
    identifier = OtelSpanIdentifier(trace_id="a" * 32, span_id="b" * 16)
    span = OtelSpanData(
        trace_id="a" * 32, span_id="b" * 16, parent_span_id=None,
        name="medagenda-chat", instrumentation_scope_name="langfuse",
        instrumentation_scope_version=None,
        attributes={
            "langfuse.observation.input": "Ana Souza, CPF 529.982.247-25, telefone 11999999999, dor no peito",
            "langfuse.observation.output": "Paciente Ana Souza",
            "langfuse.observation.metadata.route": '"triage"',
            "gen_ai.usage.input_tokens": 42,
        },
        resource_attributes={},
    )
    result = mask_otel_spans(params=MaskOtelSpansParams(spans={identifier: span}))
    patch = result.span_patches[identifier]
    assert "langfuse.observation.input" in patch.delete_attributes
    assert "langfuse.observation.output" in patch.delete_attributes
    assert "langfuse.observation.metadata.route" not in patch.delete_attributes
    assert "gen_ai.usage.input_tokens" not in patch.delete_attributes


def test_event_with_free_text_is_not_exported():
    span = SimpleNamespace(events=[SimpleNamespace(attributes={"exception.message": "CPF 52998224725"})])
    assert not should_export_span(span)


def test_exported_span_contains_no_cpf_or_phone():
    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-lf-medagenda-privacy-test", secret_key="sk-lf-medagenda-privacy-test",
        span_exporter=exporter, mask_otel_spans=mask_otel_spans,
        should_export_span=should_export_span,
    )
    with client.start_as_current_observation(name="medagenda-chat") as span:
        span.update(input="CPF 52998224725, telefone 11999999999, dor no peito")
    client.flush()
    exported = exporter.get_finished_spans()
    assert len(exported) == 1
    assert all("52998224725" not in str(span.attributes) and "11999999999" not in str(span.attributes)
               for span in exported)


def _tracer_with_exporter(monkeypatch):
    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key=f"pk-lf-medagenda-{uuid4().hex}", secret_key="sk-lf-medagenda-privacy-test",
        span_exporter=exporter, mask_otel_spans=mask_otel_spans,
        should_export_span=should_export_span,
    )
    scores = []
    monkeypatch.setattr(client, "create_score", lambda **kwargs: scores.append(kwargs))
    tracer = LangfuseTracer.__new__(LangfuseTracer)
    tracer.client = client
    return tracer, exporter, scores


def test_real_export_keeps_session_generation_model_tokens_and_safe_result(monkeypatch):
    tracer, exporter, scores = _tracer_with_exporter(monkeypatch)
    with tracer.trace_turn("patient-52998224725", "gpt-4o-mini"):
        with tracer.client.start_as_current_observation(
            as_type="generation", name="classification", model="gpt-4o-mini",
            usage_details={"input": 42, "output": 7},
            metadata={"prompt_name": "classification", "prompt_version": "3", "prompt_source": "production"},
        ) as generation:
            generation.update(input="Ana Souza CPF 52998224725 dor no peito",
                              output="Telefone 11999999999", metadata={"route": "triage"})
        tracer.record_result({"intent": "triage", "phase": "none", "booking_status": "no_attempt"})
    tracer.client.flush()

    spans = exporter.get_finished_spans()
    assert len(spans) == 2
    root = next(span for span in spans if span.name == "medagenda-chat")
    generation = next(span for span in spans if span.name == "classification")
    expected_session = hashlib.sha256(b"patient-52998224725").hexdigest()
    assert root.attributes["session.id"] == expected_session
    assert generation.attributes["session.id"] == expected_session
    assert generation.attributes["langfuse.observation.type"] == "generation"
    assert generation.attributes["langfuse.observation.model.name"] == "gpt-4o-mini"
    assert json.loads(generation.attributes["langfuse.observation.usage_details"]) == {"input": 42, "output": 7}
    assert generation.attributes["langfuse.observation.metadata.prompt_source"] == '"production"'
    assert root.attributes["langfuse.observation.metadata.booking_status"] == '"no_attempt"'
    assert root.attributes["langfuse.observation.metadata.technical_success"] == "true"
    assert [(score["name"], score["value"], score["trace_id"]) for score in scores] == [
        ("technical_success", 1, format(root.context.trace_id, "032x")),
    ]
    serialized = str([(span.attributes, span.events) for span in spans])
    for private in ("Ana Souza", "52998224725", "11999999999", "dor no peito"):
        assert private not in serialized


def test_real_export_keeps_controlled_error_without_exception_text(monkeypatch):
    tracer, exporter, scores = _tracer_with_exporter(monkeypatch)
    with pytest.raises(TimeoutError, match="52998224725"):
        with tracer.trace_turn("private-session", "gpt-4o-mini"):
            raise TimeoutError("CPF 52998224725, dor no peito")
    tracer.client.flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    root = spans[0]
    assert root.attributes["langfuse.observation.level"] == "ERROR"
    assert root.attributes["langfuse.observation.metadata.error_category"] == '"timeout"'
    assert root.attributes["langfuse.observation.metadata.booking_status"] == '"no_attempt"'
    assert root.attributes["langfuse.observation.metadata.technical_success"] == "false"
    assert root.events == ()
    assert "52998224725" not in str(root.attributes)
    assert [(score["name"], score["value"], score["trace_id"]) for score in scores] == [
        ("technical_success", 0, format(root.context.trace_id, "032x")),
    ]


def test_mask_rejects_structured_or_enum_values_with_patient_text():
    identifier = OtelSpanIdentifier(trace_id="a" * 32, span_id="b" * 16)
    span = OtelSpanData(
        trace_id="a" * 32, span_id="b" * 16, parent_span_id=None,
        name="generation", instrumentation_scope_name="langfuse",
        instrumentation_scope_version=None,
        attributes={
            "langfuse.observation.usage_details": '{"input": "CPF 52998224725"}',
            "langfuse.observation.cost_details": '{"input": 1, "patient": 52998224725}',
            "langfuse.observation.metadata.route": '"Ana Souza"',
            "langfuse.observation.metadata.prompt_name": '"Ana Souza"',
            "langfuse.observation.metadata.prompt_version": '"CPF 52998224725"',
            "gen_ai.usage.input_tokens": 52998224725,
        }, resource_attributes={},
    )
    patch = mask_otel_spans(params=MaskOtelSpansParams(spans={identifier: span})).span_patches[identifier]
    assert set(patch.delete_attributes) == set(span.attributes)


def test_mask_keeps_only_valid_prompt_link_dimensions():
    identifier = OtelSpanIdentifier(trace_id="a" * 32, span_id="b" * 16)
    span = OtelSpanData(
        trace_id="a" * 32, span_id="b" * 16, parent_span_id=None,
        name="classification", instrumentation_scope_name="langfuse-sdk",
        instrumentation_scope_version=None,
        attributes={
            "langfuse.observation.prompt.name": "classification",
            "langfuse.observation.prompt.version": 3,
            "langfuse.observation.metadata.prompt_source": '"production"',
            "langfuse.observation.metadata.prompt_name": '"classification"',
            "langfuse.observation.metadata.prompt_version": '"3"',
            "langfuse.observation.prompt.text": "CPF 52998224725",
        }, resource_attributes={},
    )
    patch = mask_otel_spans(params=MaskOtelSpansParams(spans={identifier: span})).span_patches[identifier]
    assert patch.delete_attributes == ("langfuse.observation.prompt.text",)


def test_experiment_spans_keep_only_controlled_association_fields():
    assert should_export_span(SimpleNamespace(
        events=(), links=(), status=None,
        instrumentation_scope=SimpleNamespace(name="langfuse-sdk"),
        name="experiment-item-run",
    ))
    identifier = OtelSpanIdentifier(trace_id="a" * 32, span_id="b" * 16)
    span = OtelSpanData(
        trace_id="a" * 32, span_id="b" * 16, parent_span_id=None,
        name="experiment-item-run", instrumentation_scope_name="langfuse-sdk",
        instrumentation_scope_version=None,
        attributes={
            "langfuse.environment": "sdk-experiment",
            "langfuse.experiment.id": "a" * 16,
            "langfuse.experiment.name": "medagenda-v1-1234abcd",
            "langfuse.experiment.item.id": "b" * 16,
            "langfuse.experiment.metadata": json.dumps({
                "code_version": "c" * 40, "dataset_version": "d" * 12,
                "prompt_version": "v1", "model": "gpt-4o-mini",
                "prompt_versions": {name: "local" for name in (
                    "classification", "extraction", "information", "triage"
                )},
            }),
            "langfuse.observation.input": '{"id":"synthetic"}',
            "langfuse.observation.output": "Ana Souza CPF 52998224725",
        }, resource_attributes={},
    )
    patch = mask_otel_spans(params=MaskOtelSpansParams(spans={identifier: span})).span_patches[identifier]
    assert patch.delete_attributes == ("langfuse.observation.output",)
    span.attributes["langfuse.observation.output"] = json.dumps({
        "route": "scheduling", "booking_status": "booked", "bookings": 1,
        "false_claim": False, "route_correct": True, "booking_integrity": True,
    })
    assert identifier not in mask_otel_spans(params=MaskOtelSpansParams(spans={identifier: span})).span_patches


def test_booking_result_is_reset_between_real_conversation_turns(app_factory, monkeypatch):
    tracer, exporter, scores = _tracer_with_exporter(monkeypatch)
    day = datetime.now(LOCAL_TZ) + timedelta(days=2)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    when = day.strftime("%Y-%m-%d 14:00")
    with TestClient(app_factory(tracer=tracer)) as client:
        created = client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": when}]})
        assert created.status_code == 200

        def chat(message):
            response = client.post("/chat", json={"session_id": "booking-private", "message": message})
            assert response.status_code == 200, response.text
            return client.app.state.conversations.state("booking-private")

        assert chat(f"Quero agendar Cardiologia em {when}")["booking_status"] == "no_attempt"
        assert chat("Nome: Ana Souza CPF: 529.982.247-25 telefone: (11) 99999-9999 presencial")["booking_status"] == "no_attempt"
        booked = chat("sim")
        assert booked["booking_status"] == "booked"
        assert booked["appointment_id"] == 1
        repeated = chat("sim")
        assert repeated["appointment_id"] == 1
        assert repeated["booking_status"] == "no_attempt"
        tracer.client.flush()

    roots = [span for span in exporter.get_finished_spans()
             if span.name == "medagenda-chat" and span.attributes.get("langfuse.observation.type") == "span"]
    assert {span.name for span in exporter.get_finished_spans()} <= OBSERVATION_NAMES
    assert [root.attributes["langfuse.observation.metadata.booking_status"] for root in roots] == [
        '"no_attempt"', '"no_attempt"', '"booked"', '"no_attempt"',
    ]
    by_trace = {}
    for score in scores:
        by_trace.setdefault(score["trace_id"], []).append((score["name"], score["value"]))
    booked_scores = by_trace[format(roots[2].context.trace_id, "032x")]
    assert booked_scores == [("technical_success", 1), ("booking_confirmed", 1), ("booking_integrity", 1)]
    assert by_trace[format(roots[3].context.trace_id, "032x")] == [("technical_success", 1)]
