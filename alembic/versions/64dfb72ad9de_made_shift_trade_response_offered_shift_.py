"""made shift_trade_response offered_shift nullable

Revision ID: 64dfb72ad9de
Revises: c49a18aa6b68
Create Date: 2024-12-19 14:30:42.669118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64dfb72ad9de'
down_revision: Union[str, None] = 'c49a18aa6b68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
