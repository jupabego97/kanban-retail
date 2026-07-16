"""Router de metricas / KPIs del tablero de demanda."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.db import get_session
from app.enums import DemandStatus
from app.models.demand import DemandRequest, StatusHistory
from app.models.product import Product
from app.models.user import User
from app.schemas.metrics import (
    CountByKey,
    MetricsResponse,
    OperatorStat,
    TopProduct,
)
from app.security.deps import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _counts_by(session: Session, column) -> list[CountByKey]:
    stmt = (
        select(column, func.count())
        .select_from(DemandRequest)
        .where(DemandRequest.deleted_at.is_(None))
        .group_by(column)
    )
    return [CountByKey(key=str(k), count=int(c)) for k, c in session.exec(stmt).all()]


@router.get("", response_model=MetricsResponse)
def metrics(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> MetricsResponse:
    base_filter = DemandRequest.deleted_at.is_(None)

    total = session.exec(
        select(func.count()).select_from(DemandRequest).where(base_filter)
    ).one()

    by_reason = _counts_by(session, DemandRequest.reason)
    by_status = _counts_by(session, DemandRequest.status)
    by_channel = _counts_by(session, DemandRequest.channel)

    status_counts = {s.value: 0 for s in DemandStatus}
    for item in by_status:
        status_counts[item.key] = item.count

    # Top productos por cantidad de solicitudes (por product_id o nombre libre).
    top_rows = session.exec(
        select(
            DemandRequest.product_id,
            DemandRequest.product_name_free,
            func.count().label("c"),
        )
        .where(base_filter)
        .group_by(DemandRequest.product_id, DemandRequest.product_name_free)
        .order_by(func.count().desc())
        .limit(10)
    ).all()

    top_products: list[TopProduct] = []
    for product_id, name_free, count in top_rows:
        name = name_free or ""
        if product_id is not None:
            product = session.get(Product, product_id)
            if product is not None:
                name = product.name
        top_products.append(TopProduct(product_id=product_id, product_name=name or "(sin nombre)", count=int(count)))

    # Tiempo promedio hasta validacion (NUEVA -> VALIDANDO) usando el historial.
    avg_hours_to_validation = _avg_hours_to_validation(session)

    disponible = status_counts.get(DemandStatus.DISPONIBLE.value, 0)
    descartada = status_counts.get(DemandStatus.DESCARTADA.value, 0)
    conversion = (disponible / total) if total else 0.0
    discarded_rate = (descartada / total) if total else 0.0

    by_operator = _operator_stats(session)

    return MetricsResponse(
        total_demands=int(total),
        by_reason=by_reason,
        by_status=by_status,
        by_channel=by_channel,
        top_products=top_products,
        avg_hours_to_validation=avg_hours_to_validation,
        conversion_to_disponible=round(conversion, 4),
        discarded_rate=round(discarded_rate, 4),
        by_operator=by_operator,
        status_counts=status_counts,
    )


def _avg_hours_to_validation(session: Session) -> Optional[float]:
    """Promedio de horas entre la creacion de la demanda y su paso a VALIDANDO."""
    validations = session.exec(
        select(StatusHistory)
        .where(StatusHistory.to_status == DemandStatus.VALIDANDO.value)
        .order_by(StatusHistory.demand_request_id, StatusHistory.id)
    ).all()

    seen: set[int] = set()
    deltas: list[float] = []
    for hist in validations:
        if hist.demand_request_id in seen:
            continue
        seen.add(hist.demand_request_id)
        demand = session.get(DemandRequest, hist.demand_request_id)
        if demand is None:
            continue
        delta = (hist.created_at - demand.created_at).total_seconds() / 3600.0
        if delta >= 0:
            deltas.append(delta)

    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 2)


def _operator_stats(session: Session) -> list[OperatorStat]:
    """Estadisticas por operador asignado."""
    rows = session.exec(
        select(DemandRequest.assigned_to_id, DemandRequest.status)
        .where(DemandRequest.deleted_at.is_(None))
    ).all()

    agg: dict[Optional[int], dict[str, int]] = {}
    for assigned_to_id, status in rows:
        bucket = agg.setdefault(assigned_to_id, {"total": 0, "disponible": 0, "descartada": 0})
        bucket["total"] += 1
        if status == DemandStatus.DISPONIBLE.value:
            bucket["disponible"] += 1
        elif status == DemandStatus.DESCARTADA.value:
            bucket["descartada"] += 1

    stats: list[OperatorStat] = []
    for operator_id, bucket in agg.items():
        name = "(sin asignar)"
        if operator_id is not None:
            user = session.get(User, operator_id)
            if user is not None:
                name = user.name
        stats.append(
            OperatorStat(
                operator_id=operator_id,
                operator_name=name,
                total=bucket["total"],
                disponible=bucket["disponible"],
                descartada=bucket["descartada"],
            )
        )
    stats.sort(key=lambda s: s.total, reverse=True)
    return stats
