"""Script de carga de datos de demostracion (idempotente).

Uso:
    python -m scripts.seed

Crea usuarios (OWNER/MANAGER/OPERATOR/VIEWER), proveedores, productos y
15 solicitudes de demanda repartidas por los distintos estados del tablero.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar el script directamente (python scripts/seed.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.db import engine, init_db
from app.enums import DemandChannel, DemandReason, DemandStatus, Priority, Role
from app.models.demand import DemandRequest, StatusHistory
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User
from app.security.password import hash_password
from app.state_machine import _LINEAR_TRANSITIONS  # noqa: F401  (referencia del flujo)

# Camino lineal de estados para llevar una tarjeta hasta un destino concreto.
_LINEAR_PATH = [
    DemandStatus.NUEVA,
    DemandStatus.VALIDANDO,
    DemandStatus.COTIZANDO,
    DemandStatus.POR_PEDIR,
    DemandStatus.EN_CAMINO,
    DemandStatus.DISPONIBLE,
    DemandStatus.CERRADA,
]


def _get_or_create_user(session: Session, email: str, name: str, role: Role, password: str) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        return user
    user = User(email=email, name=name, role=role.value, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _get_or_create_supplier(session: Session, name: str, **kwargs) -> Supplier:
    sup = session.exec(select(Supplier).where(Supplier.name == name)).first()
    if sup:
        return sup
    sup = Supplier(name=name, **kwargs)
    session.add(sup)
    session.commit()
    session.refresh(sup)
    return sup


def _get_or_create_product(session: Session, sku: str, **kwargs) -> Product:
    prod = session.exec(select(Product).where(Product.sku == sku)).first()
    if prod:
        return prod
    prod = Product(sku=sku, **kwargs)
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod


def _create_demand_to_status(
    session: Session,
    *,
    target: DemandStatus,
    actor_id: int,
    product: Product | None,
    product_name_free: str | None,
    reason: DemandReason,
    channel: DemandChannel,
    priority: Priority,
    sort_order: int,
) -> DemandRequest:
    """Crea una demanda en NUEVA y la avanza (via historial) hasta `target`."""
    demand = DemandRequest(
        product_id=product.id if product else None,
        product_name_free=product_name_free,
        quantity=1,
        reason=reason.value,
        channel=channel.value,
        priority=priority.value,
        status=DemandStatus.NUEVA.value,
        sort_order=sort_order,
        assigned_to_id=actor_id,
    )
    session.add(demand)
    session.commit()
    session.refresh(demand)

    session.add(
        StatusHistory(
            demand_request_id=demand.id,
            from_status=None,
            to_status=DemandStatus.NUEVA.value,
            changed_by_id=actor_id,
            note="Creacion (seed)",
        )
    )

    if target == DemandStatus.DESCARTADA:
        # Cualquier estado abierto puede descartarse.
        session.add(
            StatusHistory(
                demand_request_id=demand.id,
                from_status=DemandStatus.NUEVA.value,
                to_status=DemandStatus.DESCARTADA.value,
                changed_by_id=actor_id,
                note="Descartada (seed)",
            )
        )
        demand.status = DemandStatus.DESCARTADA.value
        demand.version += 1
    else:
        # Avanza por el camino lineal hasta llegar al estado objetivo.
        idx = _LINEAR_PATH.index(target)
        prev = DemandStatus.NUEVA
        for step in _LINEAR_PATH[1 : idx + 1]:
            session.add(
                StatusHistory(
                    demand_request_id=demand.id,
                    from_status=prev.value,
                    to_status=step.value,
                    changed_by_id=actor_id,
                    note="Avance (seed)",
                )
            )
            prev = step
            demand.version += 1
        demand.status = target.value

    session.add(demand)
    session.commit()
    session.refresh(demand)
    return demand


def run() -> None:
    # Asegura que las tablas existan (util con SQLite sin correr Alembic).
    init_db()

    with Session(engine) as session:
        # --- Usuarios ---
        owner = _get_or_create_user(session, "admin@tienda.local", "Administrador", Role.OWNER, "Admin123!")
        manager = _get_or_create_user(session, "gerente@tienda.local", "Gerente", Role.MANAGER, "Manager123!")
        operator = _get_or_create_user(session, "operador@tienda.local", "Operador", Role.OPERATOR, "Operator123!")
        _viewer = _get_or_create_user(session, "consulta@tienda.local", "Consulta", Role.VIEWER, "Viewer123!")

        # --- Proveedores ---
        s1 = _get_or_create_supplier(session, "Distribuidora Norte", contact_phone="3001112233", email="ventas@norte.com", lead_days=5)
        s2 = _get_or_create_supplier(session, "Importaciones Sur", contact_phone="3004445566", email="pedidos@sur.com", lead_days=12)
        _s3 = _get_or_create_supplier(session, "Mayorista Central", contact_phone="3007778899", email="info@central.com", lead_days=3)

        # --- Productos ---
        products = [
            _get_or_create_product(session, "SKU-001", name="Audifonos Bluetooth X1", brand="SoundPro", category="Audio", supplier_id=s1.id),
            _get_or_create_product(session, "SKU-002", name="Cargador USB-C 65W", brand="PowerMax", category="Accesorios", supplier_id=s1.id),
            _get_or_create_product(session, "SKU-003", name="Teclado Mecanico RGB", brand="KeyOne", category="Perifericos", supplier_id=s2.id),
            _get_or_create_product(session, "SKU-004", name="Mouse Inalambrico Pro", brand="ClickPro", category="Perifericos", supplier_id=s2.id),
            _get_or_create_product(session, "SKU-005", name="Monitor 27 4K", brand="ViewMax", category="Monitores", supplier_id=s1.id),
            _get_or_create_product(session, "SKU-006", name="Webcam Full HD", brand="CamPro", category="Video", supplier_id=s2.id),
            _get_or_create_product(session, "SKU-007", name="Disco SSD 1TB", brand="FastStore", category="Almacenamiento", supplier_id=s1.id),
            _get_or_create_product(session, "SKU-008", name="Memoria RAM 16GB", brand="MemPro", category="Componentes", supplier_id=s2.id),
            _get_or_create_product(session, "SKU-009", name="Hub USB 7 puertos", brand="ConnectX", category="Accesorios", supplier_id=s1.id),
            _get_or_create_product(session, "SKU-010", name="Silla Ergonomica", brand="ErgoSit", category="Mobiliario", supplier_id=_s3.id),
            _get_or_create_product(session, "SKU-011", name="Lampara LED Escritorio", brand="LumenX", category="Iluminacion", supplier_id=_s3.id),
            _get_or_create_product(session, "SKU-012", name="Parlante Portatil", brand="SoundPro", category="Audio", supplier_id=s1.id),
        ]

        # --- Demandas (15, repartidas por estado) ---
        existing = session.exec(select(DemandRequest)).first()
        if existing:
            print("Ya existen demandas, se omite la carga de demandas.")
            _print_summary(session)
            return

        actors = [operator.id, manager.id, owner.id]
        plan = [
            (DemandStatus.NUEVA, DemandReason.OUT_OF_STOCK, DemandChannel.STORE, Priority.HIGH),
            (DemandStatus.NUEVA, DemandReason.NOT_CARRIED, DemandChannel.WHATSAPP, Priority.MEDIUM),
            (DemandStatus.NUEVA, DemandReason.NEW_RELEASE, DemandChannel.WEB, Priority.LOW),
            (DemandStatus.VALIDANDO, DemandReason.OUT_OF_STOCK, DemandChannel.PHONE, Priority.HIGH),
            (DemandStatus.VALIDANDO, DemandReason.NOT_CARRIED, DemandChannel.STORE, Priority.URGENT),
            (DemandStatus.COTIZANDO, DemandReason.OUT_OF_STOCK, DemandChannel.WHATSAPP, Priority.MEDIUM),
            (DemandStatus.COTIZANDO, DemandReason.NEW_RELEASE, DemandChannel.WEB, Priority.MEDIUM),
            (DemandStatus.POR_PEDIR, DemandReason.OUT_OF_STOCK, DemandChannel.STORE, Priority.HIGH),
            (DemandStatus.EN_CAMINO, DemandReason.NOT_CARRIED, DemandChannel.PHONE, Priority.MEDIUM),
            (DemandStatus.EN_CAMINO, DemandReason.OUT_OF_STOCK, DemandChannel.WHATSAPP, Priority.LOW),
            (DemandStatus.DISPONIBLE, DemandReason.OUT_OF_STOCK, DemandChannel.STORE, Priority.HIGH),
            (DemandStatus.DISPONIBLE, DemandReason.NEW_RELEASE, DemandChannel.WEB, Priority.MEDIUM),
            (DemandStatus.CERRADA, DemandReason.OUT_OF_STOCK, DemandChannel.STORE, Priority.LOW),
            (DemandStatus.DESCARTADA, DemandReason.NOT_CARRIED, DemandChannel.OTHER, Priority.LOW),
            (DemandStatus.DESCARTADA, DemandReason.NEW_RELEASE, DemandChannel.WEB, Priority.LOW),
        ]

        for i, (status, reason, channel, priority) in enumerate(plan):
            product = products[i % len(products)]
            _create_demand_to_status(
                session,
                target=status,
                actor_id=actors[i % len(actors)],
                product=product,
                product_name_free=None if i % 3 else f"Pedido libre {i + 1}",
                reason=reason,
                channel=channel,
                priority=priority,
                sort_order=i,
            )

        print("Seed completado correctamente.")
        _print_summary(session)


def _print_summary(session: Session) -> None:
    users = session.exec(select(User)).all()
    suppliers = session.exec(select(Supplier)).all()
    products = session.exec(select(Product)).all()
    demands = session.exec(select(DemandRequest)).all()
    print(f"Usuarios: {len(users)} | Proveedores: {len(suppliers)} | Productos: {len(products)} | Demandas: {len(demands)}")
    print("Credenciales OWNER -> admin@tienda.local / Admin123!")


if __name__ == "__main__":
    run()
