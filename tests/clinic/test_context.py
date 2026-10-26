from app.clinic.service import clinic_context


def test_clinic_context_contains_administrative_data(client):
    context = clinic_context(client.app.state.session_factory)
    assert "Convênios" in context
    assert "Preparo" in context
