from app.clinic.service import clinic_context
from app.infrastructure.models import AvailabilitySlot, ClinicInfo
from scripts.seed_demo import seed
from sqlalchemy import func, select


def test_clinic_context_contains_administrative_data(client):
    context = clinic_context(client.app.state.session_factory)
    assert "Convênios" in context
    assert "Preparo" in context


def test_demo_seed_is_idempotent_on_both_backends(client):
    factory = client.app.state.session_factory
    seed(factory)
    seed(factory)
    with factory() as session:
        assert session.scalar(select(func.count(ClinicInfo.key))) == 4
        assert session.scalar(select(func.count(AvailabilitySlot.id))) > 0
