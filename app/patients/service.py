"""Validation of the patient data required for a booking."""

import re


def digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def valid_cpf(value: str) -> bool:
    cpf = digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for length in (9, 10):
        number = sum(int(cpf[i]) * (length + 1 - i) for i in range(length))
        check = (number * 10) % 11
        if check == 10:
            check = 0
        if check != int(cpf[length]):
            return False
    return True


def valid_phone(value: str) -> bool:
    return len(digits(value)) in (10, 11)
