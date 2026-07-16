"""Tests de integracion de los endpoints principales."""
from __future__ import annotations

import io

from app.enums import Role
from tests.conftest import login_as


def test_login_logout_me(client, users):
    # Credenciales invalidas.
    bad = client.post("/api/auth/login", json={"email": "owner@test.local", "password": "malas"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "authentication_error"

    login_as(client, Role.OWNER.value)
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "owner@test.local"

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_crud_suppliers(client, users):
    login_as(client, Role.MANAGER.value)
    created = client.post("/api/suppliers", json={"name": "Proveedor Test", "lead_days": 4})
    assert created.status_code == 201
    sid = created.json()["id"]

    got = client.get(f"/api/suppliers/{sid}")
    assert got.status_code == 200 and got.json()["name"] == "Proveedor Test"

    upd = client.patch(f"/api/suppliers/{sid}", json={"lead_days": 10})
    assert upd.status_code == 200 and upd.json()["lead_days"] == 10

    listing = client.get("/api/suppliers")
    assert listing.status_code == 200 and listing.json()["total"] == 1

    assert client.delete(f"/api/suppliers/{sid}").status_code == 204
    assert client.get(f"/api/suppliers/{sid}").status_code == 404


def test_products_search(client, users):
    login_as(client, Role.MANAGER.value)
    client.post("/api/products", json={"sku": "ABC-1", "name": "Cargador rapido", "barcode": "7700001"})
    client.post("/api/products", json={"sku": "ABC-2", "name": "Cable HDMI"})

    by_name = client.get("/api/products", params={"q": "Cargador"})
    assert by_name.json()["total"] == 1

    by_barcode = client.get("/api/products", params={"q": "7700001"})
    assert by_barcode.json()["total"] == 1

    dup = client.post("/api/products", json={"sku": "ABC-1", "name": "Duplicado"})
    assert dup.status_code == 409
    assert dup.json()["code"] == "duplicate"


def _create_demand(client) -> dict:
    resp = client.post(
        "/api/demands",
        json={"product_name_free": "Producto libre", "quantity": 1, "reason": "OUT_OF_STOCK", "channel": "STORE"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_demand_create_requires_product(client, users):
    login_as(client, Role.OPERATOR.value)
    resp = client.post("/api/demands", json={"quantity": 1})
    assert resp.status_code == 422


def test_demand_board_and_status_flow(client, users):
    login_as(client, Role.OPERATOR.value)
    demand = _create_demand(client)
    assert demand["status"] == "NUEVA"
    did = demand["id"]

    board = client.get("/api/demands/board")
    assert board.status_code == 200
    counts = board.json()["counts"]
    assert counts["NUEVA"] == 1

    # Transicion valida NUEVA -> VALIDANDO con version correcta.
    ok = client.patch(f"/api/demands/{did}/status", json={"status": "VALIDANDO", "version": 1})
    assert ok.status_code == 200
    assert ok.json()["status"] == "VALIDANDO"
    assert ok.json()["version"] == 2

    # Transicion invalida (salto de estado).
    bad = client.patch(f"/api/demands/{did}/status", json={"status": "DISPONIBLE", "version": 2})
    assert bad.status_code == 409
    assert bad.json()["code"] == "invalid_transition"


def test_demand_version_conflict(client, users):
    login_as(client, Role.OPERATOR.value)
    demand = _create_demand(client)
    did = demand["id"]
    # Version incorrecta => conflicto optimista.
    resp = client.patch(f"/api/demands/{did}/status", json={"status": "VALIDANDO", "version": 999})
    assert resp.status_code == 409
    assert resp.json()["code"] == "version_conflict"


def test_demand_consolidate_endpoint(client, users):
    login_as(client, Role.OPERATOR.value)
    demand = _create_demand(client)
    did = demand["id"]
    resp = client.post(f"/api/demands/{did}/consolidate", json={"note": "Otro cliente"})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 2


def test_demand_reorder(client, users):
    login_as(client, Role.OPERATOR.value)
    d1 = _create_demand(client)["id"]
    d2 = _create_demand(client)["id"]
    resp = client.patch(
        "/api/demands/reorder",
        json={"items": [{"id": d1, "sort_order": 5}, {"id": d2, "sort_order": 1}]},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] == 2


def test_metrics_endpoint(client, users):
    login_as(client, Role.OPERATOR.value)
    _create_demand(client)
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_demands"] >= 1
    assert "by_reason" in body and "status_counts" in body


def test_import_products_preview_and_commit(client, users):
    login_as(client, Role.MANAGER.value)
    csv_content = "sku,name,barcode\nIMP-1,Producto Importado,111\nIMP-2,Otro,222\n,SinSku,333\n"

    files = {"file": ("productos.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    preview = client.post("/api/imports/preview", params={"entity_type": "products"}, files=files)
    assert preview.status_code == 200
    pv = preview.json()
    assert pv["total_rows"] == 3
    assert pv["valid_rows"] == 2
    assert pv["invalid_rows"] == 1

    files = {"file": ("productos.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    commit = client.post("/api/imports/commit", params={"entity_type": "products"}, files=files)
    assert commit.status_code == 200
    cm = commit.json()
    assert cm["rows_ok"] == 2

    listing = client.get("/api/products", params={"q": "Importado"})
    assert listing.json()["total"] == 1


def test_audit_records_actions(client, users):
    login_as(client, Role.OWNER.value)
    client.post("/api/products", json={"sku": "AUD-1", "name": "Auditado"})
    resp = client.get("/api/audit")
    assert resp.status_code == 200
    actions = [row["action"] for row in resp.json()["items"]]
    assert "product.create" in actions
