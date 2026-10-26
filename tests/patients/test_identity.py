from app.patients.service import digits, valid_cpf, valid_phone


def test_patient_identifier_validation():
    assert digits("529.982.247-25") == "52998224725"
    assert valid_cpf("529.982.247-25")
    assert not valid_cpf("123.456.789-01")
    assert valid_phone("(11) 99999-9999")
    assert not valid_phone("123")
