"""fixed typo in class Event

Revision ID: aad14e167e4a
Revises: 0163a6badd45
Create Date: 2024-12-13 09:52:58.109981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aad14e167e4a'
down_revision: Union[str, None] = '0163a6badd45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('notification_preferences', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('notification_preferences', 'notification_type',
               existing_type=postgresql.ENUM('SCHEDULE', 'ANNOUNCEMENT', 'REQUEST', name='notificationtype'),
               nullable=True)
    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
    op.alter_column('notification_templates', 'priority',
               existing_type=postgresql.ENUM('HIGH', 'NORMAL', 'LOW', name='notificationpriority'),
               nullable=True,
               existing_server_default=sa.text("'NORMAL'::notificationpriority"))
    op.drop_index('ix_notification_templates_event_type', table_name='notification_templates')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_notification_templates_event_type', 'notification_templates', ['event_type'], unique=False)
    op.alter_column('notification_templates', 'priority',
               existing_type=postgresql.ENUM('HIGH', 'NORMAL', 'LOW', name='notificationpriority'),
               nullable=False,
               existing_server_default=sa.text("'NORMAL'::notificationpriority"))
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'], unique=False)
    op.alter_column('notification_preferences', 'notification_type',
               existing_type=postgresql.ENUM('SCHEDULE', 'ANNOUNCEMENT', 'REQUEST', name='notificationtype'),
               nullable=False)
    op.alter_column('notification_preferences', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
