"""
Migración de referencia desde el MVP Svelte (tablas solicitudes/proveedores).

Uso (después de exportar CSV o conectar a la DB legacy):

  python scripts/migrate_legacy_solicitudes.py --solicitudes solicitudes.csv --proveedores proveedores.csv

No se ejecuta automáticamente: es una guía operativa del piloto.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

STATUS_MAP = {
    "solicitudes": "NUEVA",
    "analisis": "VALIDANDO",
    "por_pedir": "POR_PEDIR",
    "en_camino": "EN_CAMINO",
    "recibido": "DISPONIBLE",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview de migración legacy → Kanban Retail")
    parser.add_argument("--solicitudes", type=Path, required=True)
    parser.add_argument("--proveedores", type=Path, required=False)
    args = parser.parse_args()

    with args.solicitudes.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"Solicitudes leídas: {len(rows)}")
    mapped = {}
    for row in rows:
        old = (row.get("estado") or row.get("status") or "").strip().lower()
        new = STATUS_MAP.get(old, "NUEVA")
        mapped[new] = mapped.get(new, 0) + 1
    print("Mapa de estados resultante:")
    for k, v in sorted(mapped.items()):
        print(f"  {k}: {v}")
    print("\nSiguiente paso: importar proveedores vía /api/imports y crear demandas con la API autenticada.")
    print("Añadir note='import_source=legacy_kanban_pedidos' en cada registro.")


if __name__ == "__main__":
    main()
