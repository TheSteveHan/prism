"""add videos field in submission

Revision ID: a6fd56a92afa
Revises: f4c149bbc146
Create Date: 2025-02-13 11:19:57.232111

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6fd56a92afa'
down_revision = 'f4c149bbc146'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post_submission', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vodeos', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post_submission', schema=None) as batch_op:
        batch_op.drop_column('vodeos')

    # ### end Alembic commands ###
