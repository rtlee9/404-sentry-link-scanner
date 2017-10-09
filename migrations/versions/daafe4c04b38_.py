"""empty message

Revision ID: daafe4c04b38
Revises: 58bbeea63691
Create Date: 2017-10-03 00:04:16.857153

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'daafe4c04b38'
down_revision = '58bbeea63691'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('owners',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=50), nullable=True),
    sa.Column('stripe_token', sa.Text(), nullable=True),
    sa.Column('stripe_email', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_owners_email'), 'owners', ['email'], unique=False)
    op.add_column('permissioned_url', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.drop_constraint('unique_urls_per_userowner', 'permissioned_url', type_='unique')
    op.create_unique_constraint('unique_urls_per_userowner', 'permissioned_url', ['root_url', 'user_id', 'owner_id'])
    op.drop_index('ix_permissioned_url_owner', table_name='permissioned_url')
    op.create_foreign_key(None, 'permissioned_url', 'owners', ['owner_id'], ['id'])
    op.drop_column('permissioned_url', 'owner')
    op.add_column('scan_job', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.drop_index('ix_scan_job_owner', table_name='scan_job')
    op.create_foreign_key(None, 'scan_job', 'owners', ['owner_id'], ['id'])
    op.drop_column('scan_job', 'owner')
    op.add_column('scheduled_job', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.drop_index('ix_scheduled_job_owner', table_name='scheduled_job')
    op.create_foreign_key(None, 'scheduled_job', 'owners', ['owner_id'], ['id'])
    op.drop_column('scheduled_job', 'owner')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scheduled_job', sa.Column('owner', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'scheduled_job', type_='foreignkey')
    op.create_index('ix_scheduled_job_owner', 'scheduled_job', ['owner'], unique=False)
    op.drop_column('scheduled_job', 'owner_id')
    op.add_column('scan_job', sa.Column('owner', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'scan_job', type_='foreignkey')
    op.create_index('ix_scan_job_owner', 'scan_job', ['owner'], unique=False)
    op.drop_column('scan_job', 'owner_id')
    op.add_column('permissioned_url', sa.Column('owner', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'permissioned_url', type_='foreignkey')
    op.create_index('ix_permissioned_url_owner', 'permissioned_url', ['owner'], unique=False)
    op.drop_constraint('unique_urls_per_userowner', 'permissioned_url', type_='unique')
    op.create_unique_constraint('unique_urls_per_userowner', 'permissioned_url', ['root_url', 'user_id', 'owner'])
    op.drop_column('permissioned_url', 'owner_id')
    op.drop_index(op.f('ix_owners_email'), table_name='owners')
    op.drop_table('owners')
    # ### end Alembic commands ###