"""added_user_profile_fields

Revision ID: e51af84ceaad
Revises: 1f3168005595
Create Date: 2024-12-05 14:36:31.488009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e51af84ceaad'
down_revision: Union[str, None] = '1f3168005595'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notifications')
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))
    op.add_column('users', sa.Column('position', sa.String(), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_on_leave', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('leave_balance', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('total_hours_worked', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('users', 'requires_password_change')
    op.drop_column('users', 'last_password_change')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('last_password_change', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('requires_password_change', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('users', 'last_active_at')
    op.drop_column('users', 'total_hours_worked')
    op.drop_column('users', 'leave_balance')
    op.drop_column('users', 'is_on_leave')
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'position')
    op.drop_column('users', 'department')
    op.create_table('notifications',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('type', postgresql.ENUM('SCHEDULE', 'ANNOUNCEMENT', 'REQUEST', name='notificationtype'), autoincrement=False, nullable=True),
    sa.Column('message', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_read', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='notifications_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='notifications_pkey')
    )
    # ### end Alembic commands ###