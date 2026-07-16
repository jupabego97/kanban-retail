"""Fixtures compartidos para los tests (SQLite en memoria + TestClient)."""
from __future__ import annotations

import os

# Configura el entorno ANTES de importar la app (settings se cachea al importar).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RATE_LIMIT_MAX_REQUESTS", "100000")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

import app.models  # noqa: F401,E402  (registra la metadata)
from app.db import get_session  # noqa: E402
from app.enums import Role  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security.password import hash_password  # noqa: E402


@pytest.fixture(name="engine")
def engine_fixture():
    """Engine SQLite en memoria compartido (StaticPool) para cada test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    def _get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="users")
def users_fixture(session) -> dict[str, User]:
    """Crea un usuario por cada rol y devuelve un dict por rol."""
    created: dict[str, User] = {}
    seeds = [
        ("owner@test.local", "Owner", Role.OWNER, "Owner123!"),
        ("manager@test.local", "Manager", Role.MANAGER, "Manager123!"),
        ("operator@test.local", "Operator", Role.OPERATOR, "Operator123!"),
        ("viewer@test.local", "Viewer", Role.VIEWER, "Viewer123!"),
    ]
    for email, name, role, password in seeds:
        user = User(email=email, name=name, role=role.value, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)
        created[role.value] = user
    return created


# Contrasenas conocidas por rol (coinciden con users_fixture).
PASSWORDS = {
    Role.OWNER.value: "Owner123!",
    Role.MANAGER.value: "Manager123!",
    Role.OPERATOR.value: "Operator123!",
    Role.VIEWER.value: "Viewer123!",
}

EMAILS = {
    Role.OWNER.value: "owner@test.local",
    Role.MANAGER.value: "manager@test.local",
    Role.OPERATOR.value: "operator@test.local",
    Role.VIEWER.value: "viewer@test.local",
}


def login_as(client: TestClient, role: str) -> None:
    """Inicia sesion con el usuario del rol dado (guarda la cookie en el cliente)."""
    resp = client.post("/api/auth/login", json={"email": EMAILS[role], "password": PASSWORDS[role]})
    assert resp.status_code == 200, resp.text
