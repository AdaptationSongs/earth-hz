"""empty message

Revision ID: 379c54c16629
Revises: 2a7423a8226a
Create Date: 2022-01-18 22:11:53.209049

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '379c54c16629'
down_revision = '2a7423a8226a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_model_outputs_file_name'), 'model_outputs', ['file_name'], unique=False)
    op.create_index(op.f('ix_model_outputs_iteration_id'), 'model_outputs', ['iteration_id'], unique=False)
    op.create_index(op.f('ix_model_outputs_label_id'), 'model_outputs', ['label_id'], unique=False)
    op.create_index(op.f('ix_model_outputs_offset'), 'model_outputs', ['offset'], unique=False)
    op.create_index(op.f('ix_model_outputs_probability'), 'model_outputs', ['probability'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_model_outputs_probability'), table_name='model_outputs')
    op.drop_index(op.f('ix_model_outputs_offset'), table_name='model_outputs')
    op.drop_index(op.f('ix_model_outputs_label_id'), table_name='model_outputs')
    op.drop_index(op.f('ix_model_outputs_iteration_id'), table_name='model_outputs')
    op.drop_index(op.f('ix_model_outputs_file_name'), table_name='model_outputs')
    # ### end Alembic commands ###
