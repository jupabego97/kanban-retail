"""Tests unitarios de la maquina de estados."""
from __future__ import annotations

import pytest

from app.enums import DemandStatus
from app.errors import InvalidTransitionError
from app.state_machine import (
    allowed_transitions,
    can_transition,
    validate_transition,
)


def test_flujo_lineal_valido():
    assert can_transition(DemandStatus.NUEVA, DemandStatus.VALIDANDO)
    assert can_transition(DemandStatus.VALIDANDO, DemandStatus.COTIZANDO)
    assert can_transition(DemandStatus.COTIZANDO, DemandStatus.POR_PEDIR)
    assert can_transition(DemandStatus.POR_PEDIR, DemandStatus.EN_CAMINO)
    assert can_transition(DemandStatus.EN_CAMINO, DemandStatus.DISPONIBLE)
    assert can_transition(DemandStatus.DISPONIBLE, DemandStatus.CERRADA)


def test_no_puede_saltar_estados():
    assert not can_transition(DemandStatus.NUEVA, DemandStatus.COTIZANDO)
    assert not can_transition(DemandStatus.NUEVA, DemandStatus.DISPONIBLE)
    assert not can_transition(DemandStatus.VALIDANDO, DemandStatus.POR_PEDIR)


def test_cualquier_abierto_a_descartada():
    for s in [
        DemandStatus.NUEVA,
        DemandStatus.VALIDANDO,
        DemandStatus.COTIZANDO,
        DemandStatus.POR_PEDIR,
        DemandStatus.EN_CAMINO,
        DemandStatus.DISPONIBLE,
    ]:
        assert can_transition(s, DemandStatus.DESCARTADA)


def test_estados_terminales_no_transicionan():
    assert not can_transition(DemandStatus.CERRADA, DemandStatus.DISPONIBLE)
    assert not can_transition(DemandStatus.DESCARTADA, DemandStatus.NUEVA)
    assert allowed_transitions(DemandStatus.CERRADA) == set()
    assert allowed_transitions(DemandStatus.DESCARTADA) == set()


def test_no_transicion_al_mismo_estado():
    assert not can_transition(DemandStatus.NUEVA, DemandStatus.NUEVA)


def test_validate_transition_levanta_error():
    with pytest.raises(InvalidTransitionError):
        validate_transition(DemandStatus.NUEVA, DemandStatus.DISPONIBLE)
    with pytest.raises(InvalidTransitionError):
        validate_transition(DemandStatus.CERRADA, DemandStatus.DISPONIBLE)


def test_validate_transition_valida_devuelve_enum():
    result = validate_transition(DemandStatus.NUEVA, "VALIDANDO")
    assert result == DemandStatus.VALIDANDO


def test_estado_desconocido():
    with pytest.raises(InvalidTransitionError):
        validate_transition("INEXISTENTE", DemandStatus.NUEVA)
    assert not can_transition("INEXISTENTE", DemandStatus.NUEVA)
