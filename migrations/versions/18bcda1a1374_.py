"""empty message

Revision ID: 18bcda1a1374
Revises: 61e62c4d3bea
Create Date: 2021-01-20 16:47:37.637428

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '18bcda1a1374'
down_revision = '61e62c4d3bea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('labels', sa.Column('restricted', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('labels', 'restricted')
    # ### end Alembic commands ###
