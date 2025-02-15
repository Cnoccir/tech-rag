"""enhance_document_model_v2

Revision ID: enhance_document_model_v2
Revises: 76ca7c053f33
Create Date: 2024-02-15 07:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhance_document_model_v2'
down_revision = '76ca7c053f33'
branch_labels = None
depends_on = None

def upgrade():
    # Create DocumentCategory enum type
    document_category = postgresql.ENUM('HONEYWELL', 'TRIDIUM', 'JOHNSON_CONTROLS', 'GENERAL', name='documentcategory')
    document_category.create(op.get_bind())

    # Add new columns
    op.add_column('documents', sa.Column('mime_type', sa.String(length=100), nullable=True))
    op.add_column('documents', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('tags', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('thumbnail_s3_key', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('thumbnail_generated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('documents', sa.Column('preview_s3_key', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('page_count', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('embedding_generated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('documents', sa.Column('last_indexed_at', sa.DateTime(), nullable=True))

    # Add category column with enum type
    op.add_column('documents', sa.Column('category', document_category, nullable=True, server_default='GENERAL'))
    op.alter_column('documents', 'category', nullable=False)

def downgrade():
    # Drop all new columns
    op.drop_column('documents', 'category')
    op.drop_column('documents', 'mime_type')
    op.drop_column('documents', 'title')
    op.drop_column('documents', 'description')
    op.drop_column('documents', 'tags')
    op.drop_column('documents', 'thumbnail_s3_key')
    op.drop_column('documents', 'thumbnail_generated')
    op.drop_column('documents', 'preview_s3_key')
    op.drop_column('documents', 'page_count')
    op.drop_column('documents', 'embedding_generated')
    op.drop_column('documents', 'last_indexed_at')
    
    # Drop the enum type
    document_category = postgresql.ENUM('HONEYWELL', 'TRIDIUM', 'JOHNSON_CONTROLS', 'GENERAL', name='documentcategory')
    document_category.drop(op.get_bind())
