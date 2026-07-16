"""Migracion inicial: crea todas las tablas del dominio.

Escrita para ser portable entre SQLite (tests) y PostgreSQL (produccion):
no usa tipos ENUM nativos (los enums se guardan como texto) ni JSONB especifico.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamp_columns() -> list:
    """Columnas comunes de timestamps + soft delete."""
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamp_columns(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # --- suppliers ---
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("lead_days", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_suppliers_name", "suppliers", ["name"])
    op.create_index("ix_suppliers_deleted_at", "suppliers", ["deleted_at"])

    # --- products ---
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("barcode", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamp_columns(),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_barcode", "products", ["barcode"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_supplier_id", "products", ["supplier_id"])
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])

    # --- product_aliases ---
    op.create_table(
        "product_aliases",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("alias", sa.String(), nullable=False),
        *_timestamp_columns(),
    )
    op.create_index("ix_product_aliases_product_id", "product_aliases", ["product_id"])
    op.create_index("ix_product_aliases_alias", "product_aliases", ["alias"])
    op.create_index("ix_product_aliases_deleted_at", "product_aliases", ["deleted_at"])

    # --- demand_requests ---
    op.create_table(
        "demand_requests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_name_free", sa.String(), nullable=True),
        sa.Column("variant", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("customer_contact", sa.String(), nullable=True),
        sa.Column("customer_consent", sa.Boolean(), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("evidence_url", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_demand_requests_product_id", "demand_requests", ["product_id"])
    op.create_index("ix_demand_requests_reason", "demand_requests", ["reason"])
    op.create_index("ix_demand_requests_channel", "demand_requests", ["channel"])
    op.create_index("ix_demand_requests_status", "demand_requests", ["status"])
    op.create_index("ix_demand_requests_priority", "demand_requests", ["priority"])
    op.create_index("ix_demand_requests_assigned_to_id", "demand_requests", ["assigned_to_id"])
    op.create_index("ix_demand_requests_supplier_id", "demand_requests", ["supplier_id"])
    op.create_index("ix_demand_requests_opportunity_id", "demand_requests", ["opportunity_id"])
    op.create_index("ix_demand_requests_deleted_at", "demand_requests", ["deleted_at"])

    # --- demand_interests ---
    op.create_table(
        "demand_interests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("demand_request_id", sa.Integer(), sa.ForeignKey("demand_requests.id"), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_demand_interests_demand_request_id", "demand_interests", ["demand_request_id"])
    op.create_index("ix_demand_interests_deleted_at", "demand_interests", ["deleted_at"])

    # --- status_history ---
    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("demand_request_id", sa.Integer(), sa.ForeignKey("demand_requests.id"), nullable=False),
        sa.Column("from_status", sa.String(), nullable=True),
        sa.Column("to_status", sa.String(), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_status_history_demand_request_id", "status_history", ["demand_request_id"])
    op.create_index("ix_status_history_deleted_at", "status_history", ["deleted_at"])

    # --- import_jobs ---
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("rows_ok", sa.Integer(), nullable=False),
        sa.Column("rows_error", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("error_summary", sa.String(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])
    op.create_index("ix_import_jobs_deleted_at", "import_jobs", ["deleted_at"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_deleted_at", "audit_logs", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("import_jobs")
    op.drop_table("status_history")
    op.drop_table("demand_interests")
    op.drop_table("demand_requests")
    op.drop_table("product_aliases")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("users")
