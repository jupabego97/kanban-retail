"""Tests de control de acceso basado en roles (RBAC)."""
from __future__ import annotations

from app.enums import Role
from app.security.deps import has_role
from app.models.user import User
from tests.conftest import login_as


def test_has_role_helper():
    owner = User(email="o@x.com", name="O", role=Role.OWNER.value, password_hash="x")
    viewer = User(email="v@x.com", name="V", role=Role.VIEWER.value, password_hash="x")
    assert has_role(owner, Role.OWNER, Role.MANAGER)
    assert not has_role(viewer, Role.OWNER, Role.MANAGER)


def test_rutas_requieren_autenticacion(client, users):
    # Sin login no se puede acceder a /me ni a recursos protegidos.
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/products").status_code == 401
    assert client.get("/api/users").status_code == 401


def test_health_no_requiere_auth(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_viewer_no_puede_crear_producto(client, users):
    login_as(client, Role.VIEWER.value)
    resp = client.post("/api/products", json={"sku": "V-1", "name": "Prohibido"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


def test_operator_puede_crear_producto(client, users):
    login_as(client, Role.OPERATOR.value)
    resp = client.post("/api/products", json={"sku": "OP-1", "name": "Permitido"})
    assert resp.status_code == 201


def test_solo_managers_gestionan_usuarios(client, users):
    login_as(client, Role.OPERATOR.value)
    assert client.get("/api/users").status_code == 403

    login_as(client, Role.MANAGER.value)
    assert client.get("/api/users").status_code == 200


def test_manager_no_crea_owner(client, users):
    login_as(client, Role.MANAGER.value)
    resp = client.post(
        "/api/users",
        json={"email": "nuevo@x.com", "name": "Nuevo", "password": "Passw0rd!", "role": "OWNER"},
    )
    assert resp.status_code == 403


def test_solo_manager_ve_auditoria(client, users):
    login_as(client, Role.OPERATOR.value)
    assert client.get("/api/audit").status_code == 403
    login_as(client, Role.OWNER.value)
    assert client.get("/api/audit").status_code == 200


def test_operator_no_borra_producto(client, users):
    login_as(client, Role.OPERATOR.value)
    created = client.post("/api/products", json={"sku": "DEL-1", "name": "X"})
    assert created.status_code == 201
    pid = created.json()["id"]
    # Operator no puede borrar (solo OWNER/MANAGER).
    assert client.delete(f"/api/products/{pid}").status_code == 403
