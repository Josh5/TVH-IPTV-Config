"""empty message

Revision ID: 044b003faaaa
Revises: 62e3f7ef0ad2
Create Date: 2024-06-17 13:45:34.336229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '044b003faaaa'
down_revision = '62e3f7ef0ad2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('use_custom_hls_proxy', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('hls_proxy_path', sa.String(length=256), nullable=True))

    # Set all existing values for 'use_custom_hls_proxy' to False
    op.execute('UPDATE playlists SET use_custom_hls_proxy = False WHERE use_custom_hls_proxy IS NULL')

    # Alter the column to be non-nullable
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.alter_column('use_custom_hls_proxy', existing_type=sa.Boolean(), nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('playlists', 'hls_proxy_path')
    op.drop_column('playlists', 'use_custom_hls_proxy')
    # ### end Alembic commands ###
