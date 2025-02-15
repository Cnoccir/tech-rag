"""Add is_admin to User model

Revision ID: 24ab31a54d2b
Revises: 6ac648e21454
Create Date: 2025-02-14 23:57:44.146543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24ab31a54d2b'
down_revision: Union[str, None] = '6ac648e21454'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column with default False
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_admin = FALSE")
    op.alter_column('users', 'is_admin', nullable=False)

    # Set admin user to is_admin=True
    op.execute("UPDATE users SET is_admin = TRUE WHERE username = 'admin'")


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
