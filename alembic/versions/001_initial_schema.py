"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'commodities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.Enum('grain', 'oil', 'dairy', 'sugar', 'fuel', 'packaging', 'other', name='commoditycategory'), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('origin_countries', sa.Text(), nullable=True),
        sa.Column('sourcing_regions', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('global_benchmark_symbol', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_commodities_name', 'commodities', ['name'])
    op.create_index('ix_commodities_category', 'commodities', ['category'])

    op.create_table(
        'commodity_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('commodity_id', sa.Integer(), sa.ForeignKey('commodities.id'), nullable=False),
        sa.Column('price_usd', sa.Float(), nullable=False),
        sa.Column('price_lbp', sa.Float(), nullable=True),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_commodity_prices_commodity_id', 'commodity_prices', ['commodity_id'])
    op.create_index('ix_commodity_prices_recorded_at', 'commodity_prices', ['recorded_at'])

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('erp_product_id', sa.String(100), nullable=True, unique=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True, unique=True),
        sa.Column('category', sa.String(200), nullable=True),
        sa.Column('brand', sa.String(200), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('current_cost_usd', sa.Float(), nullable=True),
        sa.Column('current_sell_price_usd', sa.Float(), nullable=True),
        sa.Column('margin_percent', sa.Float(), nullable=True),
        sa.Column('primary_commodity', sa.String(200), nullable=True),
        sa.Column('supplier_name', sa.String(300), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_category', 'products', ['category'])
    op.create_index('ix_products_erp_product_id', 'products', ['erp_product_id'])

    op.create_table(
        'product_price_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('sell_price_usd', sa.Float(), nullable=True),
        sa.Column('margin_percent', sa.Float(), nullable=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_product_price_history_product_id', 'product_price_history', ['product_id'])
    op.create_index('ix_product_price_history_recorded_at', 'product_price_history', ['recorded_at'])

    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('region', sa.String(200), nullable=True),
        sa.Column('contact_info', sa.Text(), nullable=True),
        sa.Column('commodities_supplied', sa.Text(), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('payment_terms', sa.String(200), nullable=True),
        sa.Column('shipping_route', sa.Text(), nullable=True),
        sa.Column('current_risk_level', sa.Enum('low', 'medium', 'high', 'critical', name='risklevel'), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_suppliers_name', 'suppliers', ['name'])
    op.create_index('ix_suppliers_country', 'suppliers', ['country'])

    op.create_table(
        'supplier_risk_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'high', 'critical', name='risklevel', create_type=False), nullable=False),
        sa.Column('risk_factors', sa.Text(), nullable=False),
        sa.Column('geopolitical_risk', sa.Float(), nullable=True),
        sa.Column('logistics_risk', sa.Float(), nullable=True),
        sa.Column('financial_risk', sa.Float(), nullable=True),
        sa.Column('currency_risk', sa.Float(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_supplier_risk_assessments_supplier_id', 'supplier_risk_assessments', ['supplier_id'])

    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_type', sa.Enum('price_spike', 'supply_disruption', 'margin_erosion', 'inventory_low', 'currency_shift', 'geopolitical', 'sourcing_opportunity', name='alerttype'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'critical', name='alertseverity'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
        sa.Column('action_recommended', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])

    op.create_table(
        'inventory_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('erp_product_id', sa.String(100), nullable=True),
        sa.Column('quantity_on_hand', sa.Float(), nullable=False),
        sa.Column('quantity_reserved', sa.Float(), nullable=True, server_default='0'),
        sa.Column('quantity_on_order', sa.Float(), nullable=True, server_default='0'),
        sa.Column('warehouse_location', sa.String(200), nullable=True),
        sa.Column('reorder_point', sa.Float(), nullable=True),
        sa.Column('days_of_stock', sa.Float(), nullable=True),
        sa.Column('snapshot_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inventory_snapshots_product_id', 'inventory_snapshots', ['product_id'])
    op.create_index('ix_inventory_snapshots_erp_product_id', 'inventory_snapshots', ['erp_product_id'])
    op.create_index('ix_inventory_snapshots_snapshot_at', 'inventory_snapshots', ['snapshot_at'])

    op.create_table(
        'sales_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('pos_transaction_id', sa.String(100), nullable=True),
        sa.Column('quantity_sold', sa.Float(), nullable=False),
        sa.Column('unit_price_usd', sa.Float(), nullable=False),
        sa.Column('total_usd', sa.Float(), nullable=False),
        sa.Column('customer_type', sa.String(100), nullable=True),
        sa.Column('channel', sa.String(100), nullable=True),
        sa.Column('sold_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sales_records_product_id', 'sales_records', ['product_id'])
    op.create_index('ix_sales_records_pos_transaction_id', 'sales_records', ['pos_transaction_id'])
    op.create_index('ix_sales_records_sold_at', 'sales_records', ['sold_at'])

    op.create_table(
        'market_insights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.Enum('pricing', 'supply_chain', 'sourcing', 'demand', 'risk', 'opportunity', name='insightcategory'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('detailed_analysis', sa.Text(), nullable=False),
        sa.Column('data_sources', sa.Text(), nullable=True),
        sa.Column('affected_commodities', sa.Text(), nullable=True),
        sa.Column('affected_products', sa.Text(), nullable=True),
        sa.Column('recommended_actions', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('generated_by', sa.String(100), nullable=False, server_default='ai_engine'),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_market_insights_category', 'market_insights', ['category'])
    op.create_index('ix_market_insights_created_at', 'market_insights', ['created_at'])


def downgrade() -> None:
    op.drop_table('market_insights')
    op.drop_table('sales_records')
    op.drop_table('inventory_snapshots')
    op.drop_table('alerts')
    op.drop_table('supplier_risk_assessments')
    op.drop_table('suppliers')
    op.drop_table('product_price_history')
    op.drop_table('products')
    op.drop_table('commodity_prices')
    op.drop_table('commodities')
