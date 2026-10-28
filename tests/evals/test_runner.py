from app.evals.runner import (
    _sanitize_reply, critical_checks, code_version, dataset_version,
    load_dataset, publish_experiment, run_case,
)
from app.evals.fake_model import FakeModel
from sqlalchemy.engine import URL


def test_synthetic_dataset_covers_critical_paths():
    cases = load_dataset()
    assert {case["id"] for case in cases} >= {
        "booking_complete", "missing_patient_data", "no_registered_slot",
        "duplicate_confirmation", "occupied_slot", "emergency",
        "diagnosis_request", "switch_to_information",
        "service_booked", "service_already_booked", "service_unavailable", "service_invalid",
    }
    assert {case["expected"]["booking_status"] for case in cases} == {
        "booked", "already_booked", "unavailable", "invalid", "no_attempt",
    }
    for case in cases:
        output = run_case(case, model=FakeModel())
        assert all(critical_checks(case, output).values()), (case["id"], output)


def test_local_runner_uses_sqlite_when_configured(monkeypatch, tmp_path):
    from app import config

    monkeypatch.setattr(config, "DATABASE_URL", URL.create(
        "sqlite+pysqlite", database=str(tmp_path / "source.sqlite")
    ).render_as_string())
    case = next(case for case in load_dataset() if case["id"] == "booking_complete")
    output = run_case(case, model=FakeModel())
    assert all(critical_checks(case, output).values())


def test_service_booking_outcomes():
    for case in load_dataset():
        if case.get("kind") == "booking_service":
            output = run_case(case, model=FakeModel())
            assert all(critical_checks(case, output).values()), (case["id"], output)


def test_experiment_output_masks_identifiers():
    reply = "Ana Souza, CPF 529.982.247-25, telefone (11) 99999-9999."
    sanitized = _sanitize_reply(reply)
    assert "Ana Souza" not in sanitized
    assert "529.982.247-25" not in sanitized
    assert "(11) 99999-9999" not in sanitized


def test_published_experiment_contains_no_messages_or_patient_data(monkeypatch):
    from app import config
    import app.evals.runner as runner
    import langfuse

    class Client:
        def __init__(self, **kwargs):
            pass

        def run_experiment(self, *, data, task, evaluators, **kwargs):
            assert data == [{"input": {"id": "synthetic"}}]
            assert kwargs["metadata"] == {
                "code_version": "test-sha", "dataset_version": "test-dataset",
                "prompt_version": config.PROMPT_VERSION,
                "prompt_versions": {
                    "classification": "local", "extraction": "local",
                    "information": "local", "triage": "local",
                },
                "model": "fake-model",
            }
            output = task(item=data[0])
            assert "reply" not in output and "all_replies" not in output
            assert "turn_booking_statuses" not in output
            assert all(value.value == 1 for value in (
                evaluator(input=data[0]["input"], output=output) for evaluator in evaluators
            ))
            return output

        def flush(self):
            pass

    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(langfuse, "Langfuse", Client)
    monkeypatch.setattr(runner, "code_version", lambda: "test-sha")
    monkeypatch.setattr(runner, "dataset_version", lambda: "test-dataset")
    monkeypatch.setattr(runner, "prompt_versions", lambda model: {
        "classification": "local", "extraction": "local",
        "information": "local", "triage": "local",
    })
    def fake_run_case(*args, **kwargs):
        assert kwargs["trace"] is False
        return {
        "reply": "Ana Souza, CPF 529.982.247-25, dor no peito",
        "all_replies": ["Ana Souza, CPF 529.982.247-25"],
        "route": "scheduling", "bookings": 1, "false_claim": False,
        "booking_status": "booked", "turn_booking_statuses": ["no_attempt", "booked"],
        "emergency_guidance": False, "clinical_boundary": False,
        }
    monkeypatch.setattr(runner, "run_case", fake_run_case)
    case = {"id": "synthetic", "messages": ["Tenho dor no peito"],
            "expected": {"route": "scheduling", "bookings": 1,
                         "booking_status": "booked",
                         "turn_booking_statuses": ["no_attempt", "booked"]}}
    assert publish_experiment([case], model=FakeModel())["bookings"] == 1


def test_versions_are_controlled_identifiers():
    assert len(code_version()) == 40
    assert len(dataset_version()) == 12


def test_qualitative_judge_skips_service_cases():
    from app.evals.judge import quality_score

    assert quality_score(output={"booking_status": "invalid"}) is None
