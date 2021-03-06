"""empty message

Revision ID: a942e619bd00
Revises: 049bb2ac2b92
Create Date: 2017-10-03 21:56:08.386882

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a942e619bd00'
down_revision = '049bb2ac2b92'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('owners', sa.Column('stripe_customer_id', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('owners', 'stripe_customer_id')
    # ### end Alembic commands ###
