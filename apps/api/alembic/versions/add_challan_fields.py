"""Add challan fields for tax payment

Revision ID: add_challan_fields
Revises: d8139676f93e
Create Date: 2025-08-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_challan_fields'
down_revision = 'd8139676f93e'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to challans table
    op.add_column('challans', sa.Column('cin_crn', sa.String(16), nullable=False, server_default=''))
    op.add_column('challans', sa.Column('bsr_code', sa.String(7), nullable=False, server_default=''))
    op.add_column('challans', sa.Column('bank_reference', sa.String(50), nullable=False, server_default=''))
    op.add_column('challans', sa.Column('challan_file_path', sa.String(500), nullable=True))
    
    # Remove server defaults after adding columns
    op.alter_column('challans', 'cin_crn', server_default=None)
    op.alter_column('challans', 'bsr_code', server_default=None)
    op.alter_column('challans', 'bank_reference', server_default=None)


def downgrade():
    # Remove the added columns
    op.drop_column('challans', 'challan_file_path')
    op.drop_column('challans', 'bank_reference')
    op.drop_column('challans', 'bsr_code')
    op.drop_column('challans', 'cin_crn')