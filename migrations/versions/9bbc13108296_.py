"""empty message

Revision ID: 9bbc13108296
Revises: 4345e061f3eb
Create Date: 2017-09-29 18:25:23.853603

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9bbc13108296'
down_revision = '4345e061f3eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scan_job', sa.Column('owner', sa.Text(), nullable=True))
    op.create_index(op.f('ix_scan_job_owner'), 'scan_job', ['owner'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_scan_job_owner'), table_name='scan_job')
    op.drop_column('scan_job', 'owner')
    # ### end Alembic commands ###
