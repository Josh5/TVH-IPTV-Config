"""empty message

Revision ID: 46f0f37aab7b
Revises: 
Create Date: 2023-04-24 11:38:57.368281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '46f0f37aab7b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('channel_tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('epgs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('epgs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_epgs_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_epgs_url'), ['url'], unique=False)

    op.create_table('playlists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('connections', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('tvh_uuid', sa.String(length=64), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_playlists_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_playlists_tvh_uuid'), ['tvh_uuid'], unique=True)
        batch_op.create_index(batch_op.f('ix_playlists_url'), ['url'], unique=False)

    op.create_table('channels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('number', sa.Integer(), nullable=True),
    sa.Column('guide_id', sa.Integer(), nullable=True),
    sa.Column('guide_name', sa.String(length=256), nullable=True),
    sa.Column('guide_channel_id', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['guide_id'], ['epgs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('channels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_channels_logo_url'), ['logo_url'], unique=False)
        batch_op.create_index(batch_op.f('ix_channels_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_channels_number'), ['number'], unique=False)

    op.create_table('epg_channels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('channel_id', sa.String(length=256), nullable=True),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('icon_url', sa.String(length=500), nullable=True),
    sa.Column('epg_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['epg_id'], ['epgs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('epg_channels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_epg_channels_channel_id'), ['channel_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_epg_channels_name'), ['name'], unique=False)

    op.create_table('playlist_streams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('channel_id', sa.String(length=500), nullable=True),
    sa.Column('group_title', sa.String(length=500), nullable=True),
    sa.Column('tvg_chno', sa.Integer(), nullable=True),
    sa.Column('tvg_id', sa.String(length=500), nullable=True),
    sa.Column('tvg_logo', sa.String(length=500), nullable=True),
    sa.Column('playlist_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('playlist_streams', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_playlist_streams_channel_id'), ['channel_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_playlist_streams_group_title'), ['group_title'], unique=False)
        batch_op.create_index(batch_op.f('ix_playlist_streams_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_playlist_streams_tvg_id'), ['tvg_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_playlist_streams_url'), ['url'], unique=False)

    op.create_table('channel_sources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('channel_id', sa.Integer(), nullable=False),
    sa.Column('playlist_id', sa.Integer(), nullable=False),
    sa.Column('playlist_stream_name', sa.String(length=500), nullable=True),
    sa.Column('playlist_stream_url', sa.String(length=500), nullable=True),
    sa.Column('priority', sa.String(length=500), nullable=True),
    sa.Column('tvh_uuid', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
    sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('channel_sources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_channel_sources_playlist_stream_name'), ['playlist_stream_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_channel_sources_playlist_stream_url'), ['playlist_stream_url'], unique=False)
        batch_op.create_index(batch_op.f('ix_channel_sources_priority'), ['priority'], unique=False)
        batch_op.create_index(batch_op.f('ix_channel_sources_tvh_uuid'), ['tvh_uuid'], unique=False)

    op.create_table('channels_tags_group',
    sa.Column('channel_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['channel_tags.id'], )
    )
    op.create_table('epg_channel_programmes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('channel_id', sa.String(length=256), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('desc', sa.String(length=500), nullable=True),
    sa.Column('start', sa.String(length=256), nullable=True),
    sa.Column('stop', sa.String(length=256), nullable=True),
    sa.Column('start_timestamp', sa.String(length=256), nullable=True),
    sa.Column('stop_timestamp', sa.String(length=256), nullable=True),
    sa.Column('epg_channel_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['epg_channel_id'], ['epg_channels.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('epg_channel_programmes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_epg_channel_programmes_channel_id'), ['channel_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_epg_channel_programmes_title'), ['title'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('epg_channel_programmes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_epg_channel_programmes_title'))
        batch_op.drop_index(batch_op.f('ix_epg_channel_programmes_channel_id'))

    op.drop_table('epg_channel_programmes')
    op.drop_table('channels_tags_group')
    with op.batch_alter_table('channel_sources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_channel_sources_tvh_uuid'))
        batch_op.drop_index(batch_op.f('ix_channel_sources_priority'))
        batch_op.drop_index(batch_op.f('ix_channel_sources_playlist_stream_url'))
        batch_op.drop_index(batch_op.f('ix_channel_sources_playlist_stream_name'))

    op.drop_table('channel_sources')
    with op.batch_alter_table('playlist_streams', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_playlist_streams_url'))
        batch_op.drop_index(batch_op.f('ix_playlist_streams_tvg_id'))
        batch_op.drop_index(batch_op.f('ix_playlist_streams_name'))
        batch_op.drop_index(batch_op.f('ix_playlist_streams_group_title'))
        batch_op.drop_index(batch_op.f('ix_playlist_streams_channel_id'))

    op.drop_table('playlist_streams')
    with op.batch_alter_table('epg_channels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_epg_channels_name'))
        batch_op.drop_index(batch_op.f('ix_epg_channels_channel_id'))

    op.drop_table('epg_channels')
    with op.batch_alter_table('channels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_channels_number'))
        batch_op.drop_index(batch_op.f('ix_channels_name'))
        batch_op.drop_index(batch_op.f('ix_channels_logo_url'))

    op.drop_table('channels')
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_playlists_url'))
        batch_op.drop_index(batch_op.f('ix_playlists_tvh_uuid'))
        batch_op.drop_index(batch_op.f('ix_playlists_name'))

    op.drop_table('playlists')
    with op.batch_alter_table('epgs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_epgs_url'))
        batch_op.drop_index(batch_op.f('ix_epgs_name'))

    op.drop_table('epgs')
    op.drop_table('channel_tags')
    # ### end Alembic commands ###