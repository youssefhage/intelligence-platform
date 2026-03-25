"""Expand commodity categories and add currency_rates table.

Revision ID: 002_expand
Revises: 001_initial
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_expand"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to commoditycategory
    # Each ADD VALUE auto-commits in Postgres; IF NOT EXISTS makes it idempotent
    op.execute("ALTER TYPE commoditycategory ADD VALUE IF NOT EXISTS 'beverage'")
    op.execute("ALTER TYPE commoditycategory ADD VALUE IF NOT EXISTS 'cleaning'")
    op.execute("ALTER TYPE commoditycategory ADD VALUE IF NOT EXISTS 'shipping'")
    op.execute("ALTER TYPE commoditycategory ADD VALUE IF NOT EXISTS 'currency'")

    # Add new alert types
    op.execute("ALTER TYPE alerttype ADD VALUE IF NOT EXISTS 'buy_window'")
    op.execute("ALTER TYPE alerttype ADD VALUE IF NOT EXISTS 'shipping_rate_change'")
    op.execute("ALTER TYPE alerttype ADD VALUE IF NOT EXISTS 'sourcing_currency_move'")

    # Create currency_rates table for persistent exchange rate history
    op.create_table(
        "currency_rates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pair", sa.String(10), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_currency_rates_pair", "currency_rates", ["pair"])
    op.create_index("ix_currency_rates_recorded_at", "currency_rates", ["recorded_at"])

    # Create news_articles table
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False, unique=True),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("matched_commodities", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("impact_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"])
    op.create_index("ix_news_articles_source", "news_articles", ["source"])

    # Create landed_cost_calculations table
    op.create_table(
        "landed_cost_calculations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "commodity_id",
            sa.Integer(),
            sa.ForeignKey("commodities.id"),
            nullable=True,
        ),
        sa.Column("commodity_name", sa.String(200), nullable=False),
        sa.Column("origin_country", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("incoterm", sa.String(10), nullable=False, server_default="'FOB'"),
        sa.Column("fob_price_usd", sa.Float(), nullable=False),
        sa.Column("freight_cost_usd", sa.Float(), nullable=False),
        sa.Column(
            "insurance_pct", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column("insurance_cost_usd", sa.Float(), nullable=False),
        sa.Column("cif_price_usd", sa.Float(), nullable=False),
        sa.Column("duty_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duty_usd", sa.Float(), nullable=False),
        sa.Column("port_charges_usd", sa.Float(), nullable=False),
        sa.Column("inland_transport_usd", sa.Float(), nullable=False),
        sa.Column("total_landed_cost_usd", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "calculated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_landed_cost_commodity_id",
        "landed_cost_calculations",
        ["commodity_id"],
    )

    # Create duty_rates table
    op.create_table(
        "duty_rates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hs_code", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("duty_pct", sa.Float(), nullable=False),
        sa.Column("origin_country", sa.String(100), nullable=True),
        sa.Column("effective_date", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_duty_rates_hs_code", "duty_rates", ["hs_code"])

    # Create alert_thresholds table
    op.create_table(
        "alert_thresholds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "commodity_id",
            sa.Integer(),
            sa.ForeignKey("commodities.id"),
            nullable=True,
        ),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("notify_channels", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alert_thresholds_commodity_id", "alert_thresholds", ["commodity_id"]
    )


def downgrade() -> None:
    op.drop_table("alert_thresholds")
    op.drop_table("duty_rates")
    op.drop_table("landed_cost_calculations")
    op.drop_table("news_articles")
    op.drop_table("currency_rates")
    # Note: Cannot remove enum values in Postgres without recreating the type
