"""Esquemas de importacion CSV."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int
    error: str


class ImportPreview(BaseModel):
    entity_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    sample: List[Dict[str, Any]]
    errors: List[ImportRowError]


class ImportCommitResult(BaseModel):
    job_id: int
    entity_type: str
    rows_ok: int
    rows_error: int
    errors: List[ImportRowError]


class ImportJobRead(BaseModel):
    id: int
    filename: str
    entity_type: str
    status: str
    rows_ok: int
    rows_error: int
    created_by_id: Optional[int]
    error_summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
