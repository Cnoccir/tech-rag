"""add_category_to_documents

Revision ID: 76ca7c053f33
Revises: 24ab31a54d2b
Create Date: 2025-02-15 07:41:04.589993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76ca7c053f33'
down_revision: Union[str, None] = '24ab31a54d2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
