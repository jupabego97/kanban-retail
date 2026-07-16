"""Tests unitarios de consolidacion de intereses y cambio de estado en el servicio."""
from __future__ import annotations

import pytest

from app.enums import DemandStatus
from app.errors import InvalidTransitionError, VersionConflictError
from app.models.demand import DemandInterest, DemandRequest
from app.services import demand_service


def _new_demand(session) -> DemandRequest:
    demand = DemandRequest(product_name_free="Producto X", status=DemandStatus.NUEVA.value, quantity=1)
    session.add(demand)
    session.commit()
    session.refresh(demand)
    return demand


def test_consolidate_incrementa_cantidad_y_crea_interes(session):
    demand = _new_demand(session)
    assert demand.quantity == 1

    demand_service.consolidate_interest(session, demand, actor_id=None, note="Otro cliente lo pidio")
    session.commit()
    session.refresh(demand)

    assert demand.quantity == 2
    assert demand.version == 2
    intereses = session.query(DemandInterest).filter_by(demand_request_id=demand.id).all()
    assert len(intereses) == 1
    assert intereses[0].note == "Otro cliente lo pidio"


def test_consolidate_multiple(session):
    demand = _new_demand(session)
    for _ in range(3):
        demand_service.consolidate_interest(session, demand, actor_id=None)
    session.commit()
    session.refresh(demand)
    assert demand.quantity == 4


def test_change_status_registra_historial(session):
    demand = _new_demand(session)
    demand_service.change_status(session, demand, DemandStatus.VALIDANDO.value, actor_id=None)
    session.commit()
    session.refresh(demand)
    assert demand.status == DemandStatus.VALIDANDO.value
    assert demand.version == 2


def test_change_status_version_conflict(session):
    demand = _new_demand(session)
    with pytest.raises(VersionConflictError):
        demand_service.change_status(
            session, demand, DemandStatus.VALIDANDO.value, actor_id=None, expected_version=99
        )


def test_change_status_transicion_invalida(session):
    demand = _new_demand(session)
    with pytest.raises(InvalidTransitionError):
        demand_service.change_status(session, demand, DemandStatus.DISPONIBLE.value, actor_id=None)
