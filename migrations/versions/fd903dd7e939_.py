"""empty message

Revision ID: fd903dd7e939
Revises: 9f27eae10c36
Create Date: 2020-04-13 06:37:08.632494

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fd903dd7e939'
down_revision = '9f27eae10c36'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_iterations', 'training_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.add_column('model_outputs', sa.Column('probability', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('model_outputs', 'probability')
    op.alter_column('model_iterations', 'training_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    # ### end Alembic commands ###
