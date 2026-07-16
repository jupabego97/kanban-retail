"""Router de importacion CSV (preview + commit) para productos y proveedores."""
from __future__ import annotations

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.enums import ImportStatus, Role
from app.errors import ValidationError
from app.models.imports import ImportJob
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.imports import (
    ImportCommitResult,
    ImportPreview,
    ImportRowError,
)
from app.security.deps import require_roles
from app.services.audit_service import record_audit

router = APIRouter(prefix="/imports", tags=["imports"])

_EDITORS = (Role.OWNER, Role.MANAGER)

_SUPPORTED = {"products", "suppliers"}


async def _read_rows(file: UploadFile) -> List[dict]:
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in row.items()})
    return rows


def _validate_row(entity_type: str, row: dict) -> Optional[str]:
    """Devuelve un mensaje de error si la fila es invalida, o None si es valida."""
    if entity_type == "products":
        if not row.get("sku"):
            return "Falta la columna obligatoria 'sku'."
        if not row.get("name"):
            return "Falta la columna obligatoria 'name'."
    elif entity_type == "suppliers":
        if not row.get("name"):
            return "Falta la columna obligatoria 'name'."
        lead = row.get("lead_days")
        if lead:
            try:
                int(lead)
            except ValueError:
                return "El campo 'lead_days' debe ser numerico."
    return None


@router.post("/preview", response_model=ImportPreview)
async def preview_import(
    entity_type: str = Query(..., description="products | suppliers"),
    file: UploadFile = File(...),
    _: User = Depends(require_roles(*_EDITORS)),
) -> ImportPreview:
    if entity_type not in _SUPPORTED:
        raise ValidationError("entity_type no soportado.", details={"supported": sorted(_SUPPORTED)})

    rows = await _read_rows(file)
    errors: List[ImportRowError] = []
    valid = 0
    for idx, row in enumerate(rows, start=1):
        err = _validate_row(entity_type, row)
        if err:
            errors.append(ImportRowError(row=idx, error=err))
        else:
            valid += 1

    return ImportPreview(
        entity_type=entity_type,
        total_rows=len(rows),
        valid_rows=valid,
        invalid_rows=len(errors),
        sample=rows[:10],
        errors=errors[:50],
    )


@router.post("/commit", response_model=ImportCommitResult)
async def commit_import(
    entity_type: str = Query(..., description="products | suppliers"),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> ImportCommitResult:
    if entity_type not in _SUPPORTED:
        raise ValidationError("entity_type no soportado.", details={"supported": sorted(_SUPPORTED)})

    rows = await _read_rows(file)
    errors: List[ImportRowError] = []
    rows_ok = 0

    for idx, row in enumerate(rows, start=1):
        err = _validate_row(entity_type, row)
        if err:
            errors.append(ImportRowError(row=idx, error=err))
            continue
        try:
            if entity_type == "products":
                existing = session.exec(
                    select(Product).where(Product.sku == row["sku"], Product.deleted_at.is_(None))
                ).first()
                if existing:
                    existing.name = row.get("name") or existing.name
                    existing.barcode = row.get("barcode") or existing.barcode
                    existing.brand = row.get("brand") or existing.brand
                    existing.category = row.get("category") or existing.category
                    session.add(existing)
                else:
                    session.add(
                        Product(
                            sku=row["sku"],
                            name=row["name"],
                            barcode=row.get("barcode") or None,
                            brand=row.get("brand") or None,
                            category=row.get("category") or None,
                        )
                    )
            else:  # suppliers
                session.add(
                    Supplier(
                        name=row["name"],
                        contact_phone=row.get("contact_phone") or None,
                        email=row.get("email") or None,
                        lead_days=int(row["lead_days"]) if row.get("lead_days") else 0,
                        notes=row.get("notes") or None,
                    )
                )
            rows_ok += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(ImportRowError(row=idx, error=f"Error al procesar la fila: {type(exc).__name__}"))

    job = ImportJob(
        filename=file.filename or "upload.csv",
        entity_type=entity_type,
        status=ImportStatus.COMMITTED.value if not errors else ImportStatus.FAILED.value,
        rows_ok=rows_ok,
        rows_error=len(errors),
        created_by_id=current_user.id,
        error_summary="; ".join(e.error for e in errors[:5]) if errors else None,
    )
    session.add(job)
    record_audit(
        session,
        actor_id=current_user.id,
        action="import.commit",
        entity_type=entity_type,
        meta={"rows_ok": rows_ok, "rows_error": len(errors)},
    )
    session.commit()
    session.refresh(job)

    return ImportCommitResult(
        job_id=job.id,
        entity_type=entity_type,
        rows_ok=rows_ok,
        rows_error=len(errors),
        errors=errors[:50],
    )
