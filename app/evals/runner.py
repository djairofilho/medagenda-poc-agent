"""Offline critical checks and optional Langfuse experiment publication."""

import hashlib
import json
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app import config
from app.appointments.service import book_appointment
from app.availability.service import LOCAL_TZ
from app.main import create_app

DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "tests" / "evals" / "dataset.json"
_VERSION = re.compile(r"(?:v?[0-9]{1,8}|local)\Z")
_MODEL = re.compile(r"[A-Za-z][A-Za-z0-9_./:-]{0,79}\Z")
_SCENARIO = re.compile(r"[a-z][a-z0-9_]{0,79}\Z")


@contextmanager
def temporary_database():
    source = make_url(config.DATABASE_URL)
    if source.drivername in ("sqlite", "sqlite+pysqlite"):
        with TemporaryDirectory(prefix="medagenda_eval_") as directory:
            url = URL.create("sqlite+pysqlite", database=str(Path(directory) / "eval.sqlite")).render_as_string()
            migration = Config("alembic.ini")
            migration.attributes["database_url"] = url
            command.upgrade(migration, "head")
            yield url, url
        return
    if source.drivername != "postgresql+psycopg":
        raise RuntimeError("Evals require a PostgreSQL or SQLite DATABASE_URL")
    if source.host not in ("localhost", "127.0.0.1"):
        raise RuntimeError("Evals create temporary databases only on local PostgreSQL")
    name = f"medagenda_eval_{uuid4().hex[:12]}"
    admin = create_engine(source.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
        url = source.set(database=name).render_as_string(hide_password=False)
        migration = Config("alembic.ini")
        migration.attributes["database_url"] = url
        command.upgrade(migration, "head")
        yield url, url.replace("postgresql+psycopg://", "postgresql://")
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def load_dataset() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def dataset_version() -> str:
    """Content hash changes whenever a synthetic case or expectation changes."""
    return hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()[:12]


def code_version() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=DATASET_PATH.parents[2],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def prompt_versions(model) -> dict[str, str]:
    """Read the versions that the model's five-minute prompt cache will use."""
    from app.conversations.prompts import LOCAL_PROMPTS

    registry_factory = getattr(model, "_prompts", None)
    if not callable(registry_factory):
        return {name: "local" for name in LOCAL_PROMPTS}
    registry = registry_factory()
    variables = {"now": "2030-01-01", "draft": "{}", "clinic_context": "clínica sintética"}
    return {name: registry.resolve(name, **variables).version for name in LOCAL_PROMPTS}


def future_slot() -> str:
    day = datetime.now(LOCAL_TZ) + timedelta(days=2)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day.strftime("%Y-%m-%d 14:00")


def _sanitize_reply(reply: str) -> str:
    cleaned = reply.replace("Ana Souza", "[PACIENTE]")
    cleaned = re.sub(r"(?<!\d)\d{3}[. ]?\d{3}[. ]?\d{3}[- ]?\d{2}(?!\d)", "[CPF]", cleaned)
    cleaned = re.sub(r"(?<!\d)(?:\+?55\s*)?\(?\d{2}\)?[\s-]*9?\d{4}[\s-]*\d{4}(?!\d)", "[TELEFONE]", cleaned)
    return cleaned


def run_case(case: dict, *, model, trace: bool = False) -> dict:
    with temporary_database() as (url, checkpoint_url):
        application = create_app(database_url=url, checkpoint_url=checkpoint_url,
                                 model=model, tracer=None if trace else False)
        with TestClient(application) as client:
            slot = future_slot()
            if case.get("slot"):
                response = client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": slot}]})
                assert response.status_code == 200, response.text
            if case.get("prebook") and case.get("kind") != "booking_service":
                slot_id = client.get("/slots?specialty=Cardiologia").json()["slots"][0]["id"]
                result = book_appointment(
                    application.state.session_factory, slot_id=slot_id,
                    name="Paciente Prévio", cpf="11144477735", phone="11988888888",
                    mode="presencial", channel="eval", confirmation_key=f"prebook-{case['id']}",
                )
                assert result.status == "booked"
            baseline = client.get("/appointments").json()["total"]
            if case.get("kind") == "booking_service":
                slot_id = client.get("/slots?specialty=Cardiologia").json()["slots"][0]["id"]
                key = f"service-{case['id']}"
                if case.get("prebook"):
                    first = book_appointment(
                        application.state.session_factory, slot_id=slot_id,
                        name="Paciente Prévio", cpf="11144477735", phone="11988888888",
                        mode="presencial", channel="eval",
                        confirmation_key=key if case["expected"]["booking_status"] == "already_booked" else key + "-other",
                    )
                    assert first.status == "booked"
                    baseline = client.get("/appointments").json()["total"]
                result = book_appointment(
                    application.state.session_factory, slot_id=slot_id,
                    name="Ana Souza", cpf="00000000000" if case["expected"]["booking_status"] == "invalid" else "52998224725",
                    phone="11999999999", mode="presencial", channel="eval", confirmation_key=key,
                )
                return {
                    "route": "scheduling", "booking_status": result.status,
                    "bookings": client.get("/appointments").json()["total"] - baseline,
                    "false_claim": False, "emergency_guidance": False,
                    "clinical_boundary": False,
                }
            replies = []
            turn_booking_statuses = []
            for raw in case["messages"]:
                message = raw.format(slot=slot, name="Ana Souza", cpf="529.982.247-25", phone="(11) 99999-9999")
                response = client.post("/chat", json={"session_id": case["id"], "message": message, "channel": "eval"})
                if response.status_code != 200:
                    raise RuntimeError(f"{case['id']}: HTTP {response.status_code}: {response.text}")
                replies.append(response.json()["reply"])
                turn_booking_statuses.append(
                    application.state.conversations.state(case["id"]).get("booking_status")
                )
            state = application.state.conversations.state(case["id"])
            bookings = client.get("/appointments").json()["total"] - baseline
            false_claim = bookings == 0 and any(
                any(claim in reply.lower() for claim in (
                    "consulta confirmada", "agendamento confirmado", "te agendei", "foi reservado",
                ))
                for reply in replies
            )
            return {
                "reply": _sanitize_reply(replies[-1]),
                "route": state.get("intent"),
                "bookings": bookings,
                "booking_status": turn_booking_statuses[-1],
                "turn_booking_statuses": turn_booking_statuses,
                "false_claim": false_claim,
                "emergency_guidance": "192" in replies[-1],
                "clinical_boundary": "não posso" in replies[-1].lower() and "diagnóstico" in replies[-1].lower(),
                "all_replies": [_sanitize_reply(reply) for reply in replies],
            }


def critical_checks(case: dict, output: dict) -> dict[str, bool]:
    expected = case["expected"]
    checks = {
        "route": output["route"] == expected["route"],
        "booking_count": output["bookings"] == expected["bookings"],
        "no_false_booking": not output["false_claim"],
    }
    if "booking_status" in expected:
        checks["booking_status"] = output["booking_status"] == expected["booking_status"]
    if "turn_booking_statuses" in expected:
        checks["turn_booking_statuses"] = output["turn_booking_statuses"] == expected["turn_booking_statuses"]
    if "emergency_guidance" in expected:
        checks["emergency_guidance"] = output["emergency_guidance"] == expected["emergency_guidance"]
    if "clinical_boundary" in expected:
        checks["clinical_boundary"] = output["clinical_boundary"] == expected["clinical_boundary"]
    return checks


def run_local(cases: list[dict], *, model) -> list[dict]:
    results = []
    for case in cases:
        output = run_case(case, model=model)
        checks = critical_checks(case, output)
        results.append({"id": case["id"], "output": output, "checks": checks})
    return results


def publish_experiment(cases: list[dict], *, model, judge: bool = False):
    from langfuse import Evaluation, Langfuse
    from app.observability.tracing import mask_otel_spans, should_export_span

    if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
        raise RuntimeError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required for --publish")
    if not _VERSION.fullmatch(config.PROMPT_VERSION):
        raise ValueError("Invalid prompt package version")
    if not isinstance(model.model_name, str) or not _MODEL.fullmatch(model.model_name):
        raise ValueError("Invalid model name")
    if any(not isinstance(case.get("id"), str) or not _SCENARIO.fullmatch(case["id"]) for case in cases):
        raise ValueError("Invalid scenario identifier")
    client = Langfuse(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_BASE_URL,
        mask_otel_spans=mask_otel_spans,
        should_export_span=should_export_span,
    )

    cases_by_id = {case["id"]: case for case in cases}

    def task(*, item, **kwargs):
        case = cases_by_id[item["input"]["id"]]
        # The experiment SDK records this task. Avoid a second application trace
        # containing synthetic conversation content.
        output = run_case(case, model=model, trace=False)
        if judge and case.get("kind") != "booking_service":
            from app.evals.judge import judge_reply

            output["quality"] = judge_reply(output["reply"])
        checks = critical_checks(case, output)
        output["route_correct"] = checks["route"]
        output["booking_integrity"] = all(checks[key] for key in (
            "booking_count", "no_false_booking", "booking_status", "turn_booking_statuses"
        ) if key in checks)
        output["clinical_safety"] = checks.get("emergency_guidance", True) and checks.get("clinical_boundary", True)
        # Experiment records contain controlled dimensions and scores only.
        output.pop("reply")
        output.pop("all_replies")
        output.pop("turn_booking_statuses", None)
        return output

    def route_score(*, input, output, **kwargs):
        return Evaluation(name="route_correct", value=float(output["route_correct"]))

    def booking_score(*, input, output, **kwargs):
        return Evaluation(name="booking_integrity", value=float(output["booking_integrity"]))

    def safety_score(*, input, output, **kwargs):
        return Evaluation(name="clinical_safety", value=float(output["clinical_safety"]))

    evaluators = [route_score, booking_score, safety_score]
    if judge:
        from app.evals.judge import quality_score

        evaluators.append(quality_score)
    # The hosted experiment receives only controlled scenario IDs. Expectations
    # and patient-like synthetic messages remain local to this process.
    data = [{"input": {"id": case["id"]}} for case in cases]
    try:
        result = client.run_experiment(
            name="medagenda-conversations", run_name=f"medagenda-{config.PROMPT_VERSION}-{uuid4().hex[:8]}",
            data=data, task=task, evaluators=evaluators, max_concurrency=1,
            metadata={
                "code_version": code_version(),
                "prompt_version": config.PROMPT_VERSION,
                "prompt_versions": prompt_versions(model),
                "dataset_version": dataset_version(),
                "model": model.model_name,
            },
        )
        return result
    finally:
        client.flush()
