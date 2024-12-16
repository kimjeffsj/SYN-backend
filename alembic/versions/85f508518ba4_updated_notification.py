"""updated notification

Revision ID: 85f508518ba4
Revises: aad14e167e4a
Create Date: 2024-12-13 13:22:08.590853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85f508518ba4'
down_revision: Union[str, None] = 'aad14e167e4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_notification_templates_event_type'), 'notification_templates', ['event_type'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_notification_templates_event_type'), table_name='notification_templates')
    # ### end Alembic commands ###