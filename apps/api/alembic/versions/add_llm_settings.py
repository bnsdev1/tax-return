"""Add LLM settings table

Revision ID: add_llm_settings
Revises: add_challan_fields
Create Date: 2025-01-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_llm_settings'
down_revision = 'add_challan_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add LLM settings table."""
    op.create_table(
        'llm_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('llm_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('cloud_allowed', sa.Boolean(), nullable=False, default=True),
        sa.Column('primary', sa.String(length=20), nullable=False, default='openai'),
        sa.Column('long_context_provider', sa.String(length=20), nullable=False, default='gemini'),
        sa.Column('local_provider', sa.String(length=20), nullable=False, default='ollama'),
        sa.Column('redact_pii', sa.Boolean(), nullable=False, default=True),
        sa.Column('long_context_threshold_chars', sa.Integer(), nullable=False, default=8000),
        sa.Column('confidence_threshold', sa.Numeric(precision=3, scale=2), nullable=False, default=0.7),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=2),
        sa.Column('timeout_ms', sa.Integer(), nullable=False, default=40000),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_settings_id'), 'llm_settings', ['id'], unique=False)


def downgrade() -> None:
    """Remove LLM settings table."""
    op.drop_index(op.f('ix_llm_settings_id'), table_name='llm_settings')
    op.drop_table('llm_settings')