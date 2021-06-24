"""empty message

Revision ID: bfaa60c81835
Revises: 97cdf7d1477e
Create Date: 2021-06-24 01:29:04.627392

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bfaa60c81835'
down_revision = '97cdf7d1477e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('model_iterations', 'training_date', new_column_name='updated')

def downgrade():
    op.alter_column('model_iterations', 'updated', new_column_name='training_date')

