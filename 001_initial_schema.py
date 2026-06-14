"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('search_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('favorites_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('activity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('join_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
        sa.Column('registration_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # Drive sources table
    op.create_table(
        'drive_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('drive_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_shared_drive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('added_by', sa.BigInteger(), nullable=True),
        sa.Column('total_files', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_scanned', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drive_sources_drive_id', 'drive_sources', ['drive_id'], unique=True)

    # Drive files table
    op.create_table(
        'drive_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.String(255), nullable=False),
        sa.Column('drive_source_id', sa.Integer(), sa.ForeignKey('drive_sources.id'), nullable=True),
        sa.Column('file_name', sa.String(1000), nullable=False),
        sa.Column('file_name_lower', sa.String(1000), nullable=False),
        sa.Column('extension', sa.String(20), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=False, server_default='other'),
        sa.Column('category', sa.String(50), nullable=False, server_default='uncategorized'),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(255), nullable=True),
        sa.Column('google_drive_url', sa.Text(), nullable=False),
        sa.Column('parent_folder_id', sa.String(255), nullable=True),
        sa.Column('parent_folder_name', sa.String(500), nullable=True),
        sa.Column('drive_id', sa.String(255), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('modified_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('indexed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_verified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('popularity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drive_files_file_id', 'drive_files', ['file_id'], unique=True)
    op.create_index('ix_drive_files_file_name_lower', 'drive_files', ['file_name_lower'])
    op.create_index('ix_drive_files_category', 'drive_files', ['category'])
    op.create_index('ix_drive_files_drive_id', 'drive_files', ['drive_id'])
    op.create_index('ix_drive_files_is_available', 'drive_files', ['is_available'])
    op.create_index('ix_drive_files_search', 'drive_files', ['file_name_lower', 'category', 'file_type', 'is_available'])

    # Categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('emoji', sa.String(10), nullable=False, server_default='📁'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    # Search history
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('query', sa.String(500), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category_filter', sa.String(100), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])

    # Favorites
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_id', sa.Integer(), sa.ForeignKey('drive_files.id'), nullable=False),
        sa.Column('saved_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'file_id', name='uq_user_file_favorite'),
    )

    # User analytics
    op.create_table(
        'user_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('file_id', sa.String(255), nullable=True),
        sa.Column('query', sa.String(500), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Search keywords
    op.create_table(
        'search_keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(500), nullable=False),
        sa.Column('search_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_searched', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('result_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('keyword'),
    )
    op.create_index('ix_search_keywords_keyword', 'search_keywords', ['keyword'], unique=True)

    # Index runs
    op.create_table(
        'index_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('drive_source_id', sa.Integer(), nullable=True),
        sa.Column('files_scanned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('files_added', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('files_removed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('files_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('index_runs')
    op.drop_table('search_keywords')
    op.drop_table('user_analytics')
    op.drop_table('favorites')
    op.drop_table('search_history')
    op.drop_table('categories')
    op.drop_table('drive_files')
    op.drop_table('drive_sources')
    op.drop_table('users')
