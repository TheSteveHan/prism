"""nullable label post_id

Revision ID: 028b61b3b866
Revises: c027b719298d
Create Date: 2025-02-14 21:09:45.309115

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '028b61b3b866'
down_revision = 'c027b719298d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('label', schema=None) as batch_op:
        batch_op.alter_column('post_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('label', schema=None) as batch_op:
        batch_op.alter_column('post_id',
               existing_type=sa.BIGINT(),
               nullable=False)

    # ### end Alembic commands ###
