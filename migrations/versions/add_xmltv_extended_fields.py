"""add extended xmltv fields to epg_channel_programmes

Revision ID: add_xmltv_extended_fields
Revises: e829b6fba2dc
Create Date: 2025-08-24
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_xmltv_extended_fields'
down_revision = 'e829b6fba2dc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('epg_channel_programmes') as batch_op:
        batch_op.add_column(sa.Column('summary', sa.String(length=500)))
        batch_op.add_column(sa.Column('keywords', sa.String(length=500)))
        batch_op.add_column(sa.Column('actors', sa.String(length=500)))
        batch_op.add_column(sa.Column('directors', sa.String(length=500)))
        batch_op.add_column(sa.Column('guests', sa.String(length=500)))
        batch_op.add_column(sa.Column('presenters', sa.String(length=500)))
        batch_op.add_column(sa.Column('writers', sa.String(length=500)))
        batch_op.add_column(sa.Column('video_colour', sa.String(length=32)))
        batch_op.add_column(sa.Column('video_aspect', sa.String(length=32)))
        batch_op.add_column(sa.Column('video_quality', sa.String(length=16)))
        batch_op.add_column(sa.Column('subtitles_type', sa.String(length=32)))
        batch_op.add_column(sa.Column('audio_described', sa.Boolean()))
        batch_op.add_column(sa.Column('previously_shown', sa.String(length=32)))
        batch_op.add_column(sa.Column('premiere', sa.Boolean()))
        batch_op.add_column(sa.Column('is_new', sa.Boolean()))
        batch_op.add_column(sa.Column('episode_num_onscreen', sa.String(length=128)))
        batch_op.add_column(sa.Column('episode_num_xmltv_ns', sa.String(length=128)))
        batch_op.add_column(sa.Column('episode_num_dd_progid', sa.String(length=128)))
        batch_op.add_column(sa.Column('star_rating', sa.String(length=32)))
        batch_op.add_column(sa.Column('date', sa.String(length=8)))
        batch_op.add_column(sa.Column('rating_system', sa.String(length=64)))
        batch_op.add_column(sa.Column('rating_value', sa.String(length=64)))


def downgrade():
    with op.batch_alter_table('epg_channel_programmes') as batch_op:
        batch_op.drop_column('rating_value')
        batch_op.drop_column('rating_system')
        batch_op.drop_column('date')
        batch_op.drop_column('star_rating')
        batch_op.drop_column('episode_num_dd_progid')
        batch_op.drop_column('episode_num_xmltv_ns')
        batch_op.drop_column('episode_num_onscreen')
        batch_op.drop_column('is_new')
        batch_op.drop_column('premiere')
        batch_op.drop_column('previously_shown')
        batch_op.drop_column('audio_described')
        batch_op.drop_column('subtitles_type')
        batch_op.drop_column('video_quality')
        batch_op.drop_column('video_aspect')
        batch_op.drop_column('video_colour')
        batch_op.drop_column('writers')
        batch_op.drop_column('presenters')
        batch_op.drop_column('guests')
        batch_op.drop_column('directors')
        batch_op.drop_column('actors')
        batch_op.drop_column('keywords')
        batch_op.drop_column('summary')