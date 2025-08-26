"""Add extended XMLTV programme optional fields

Revision ID: aa_add_extended_programme_fields
Revises: e829b6fba2dc
Create Date: 2025-08-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aa_add_extended_programme_fields'
down_revision = '044b003faaaa'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('epg_channel_programmes') as batch_op:
        batch_op.add_column(sa.Column('summary', sa.String(length=1000)))
        batch_op.add_column(sa.Column('keywords', sa.String(length=1000)))
        batch_op.add_column(sa.Column('credits_json', sa.String(length=4000)))
        batch_op.add_column(sa.Column('video_colour', sa.String(length=10)))
        batch_op.add_column(sa.Column('video_aspect', sa.String(length=32)))
        batch_op.add_column(sa.Column('video_quality', sa.String(length=16)))
        batch_op.add_column(sa.Column('subtitles_type', sa.String(length=32)))
        batch_op.add_column(sa.Column('audio_described', sa.Boolean()))
        batch_op.add_column(sa.Column('previously_shown_date', sa.String(length=32)))
        batch_op.add_column(sa.Column('premiere', sa.Boolean()))
        batch_op.add_column(sa.Column('is_new', sa.Boolean()))
        batch_op.add_column(sa.Column('epnum_onscreen', sa.String(length=64)))
        batch_op.add_column(sa.Column('epnum_xmltv_ns', sa.String(length=64)))
        batch_op.add_column(sa.Column('epnum_dd_progid', sa.String(length=64)))
        batch_op.add_column(sa.Column('star_rating', sa.String(length=16)))
        batch_op.add_column(sa.Column('production_year', sa.String(length=8)))
        batch_op.add_column(sa.Column('rating_system', sa.String(length=32)))
        batch_op.add_column(sa.Column('rating_value', sa.String(length=64)))

def downgrade():
    with op.batch_alter_table('epg_channel_programmes') as batch_op:
        batch_op.drop_column('rating_value')
        batch_op.drop_column('rating_system')
        batch_op.drop_column('production_year')
        batch_op.drop_column('star_rating')
        batch_op.drop_column('epnum_dd_progid')
        batch_op.drop_column('epnum_xmltv_ns')
        batch_op.drop_column('epnum_onscreen')
        batch_op.drop_column('is_new')
        batch_op.drop_column('premiere')
        batch_op.drop_column('previously_shown_date')
        batch_op.drop_column('audio_described')
        batch_op.drop_column('subtitles_type')
        batch_op.drop_column('video_quality')
        batch_op.drop_column('video_aspect')
        batch_op.drop_column('video_colour')
        batch_op.drop_column('credits_json')
        batch_op.drop_column('keywords')
        batch_op.drop_column('summary')
