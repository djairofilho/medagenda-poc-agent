from types import SimpleNamespace

from langfuse.types import OtelSpanIdentifier, OtelSpanData, MaskOtelSpansParams
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.observability.tracing import mask_otel_spans, should_export_span


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
    with client.start_as_current_observation(name="privacy-test") as span:
        span.update(input="CPF 52998224725, telefone 11999999999, dor no peito")
    client.flush()
    exported = exporter.get_finished_spans()
    assert len(exported) == 1
    assert all("52998224725" not in str(span.attributes) and "11999999999" not in str(span.attributes)
               for span in exported)
