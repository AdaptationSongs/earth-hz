"""empty message

Revision ID: 30ab74661e9a
Revises: 0abb957cdf18
Create Date: 2020-04-11 22:25:21.206789

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '30ab74661e9a'
down_revision = '0abb957cdf18'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('model_iterations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('training_date', sa.DateTime(), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model_outputs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('iteration_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('label_id', sa.Integer(), nullable=False),
    sa.Column('offset', sa.Float(), nullable=False),
    sa.Column('duration', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['file_name'], ['audio_files.name'], ),
    sa.ForeignKeyConstraint(['iteration_id'], ['model_iterations.id'], ),
    sa.ForeignKeyConstraint(['label_id'], ['labels.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_labels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['label_id'], ['labels.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('cluster_groups', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cluster_groups', 'projects', ['project_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'cluster_groups', type_='foreignkey')
    op.drop_column('cluster_groups', 'project_id')
    op.drop_table('project_labels')
    op.drop_table('model_outputs')
    op.drop_table('model_iterations')
    # ### end Alembic commands ###
