"""Esquemas de metricas / KPIs."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class CountByKey(BaseModel):
    key: str
    count: int


class TopProduct(BaseModel):
    product_id: Optional[int]
    product_name: str
    count: int


class OperatorStat(BaseModel):
    operator_id: Optional[int]
    operator_name: str
    total: int
    disponible: int
    descartada: int


class MetricsResponse(BaseModel):
    total_demands: int
    by_reason: List[CountByKey]
    by_status: List[CountByKey]
    by_channel: List[CountByKey]
    top_products: List[TopProduct]
    # Tiempo promedio (en horas) desde NUEVA hasta VALIDANDO.
    avg_hours_to_validation: Optional[float]
    # Tasa de conversion a DISPONIBLE (0..1).
    conversion_to_disponible: float
    # Tasa de descarte (0..1).
    discarded_rate: float
    by_operator: List[OperatorStat]
    status_counts: Dict[str, int]
