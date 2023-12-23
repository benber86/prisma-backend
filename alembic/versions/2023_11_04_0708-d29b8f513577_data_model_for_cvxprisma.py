"""Data model for cvxPrisma

Revision ID: d29b8f513577
Revises: 51a796697c57
Create Date: 2023-11-04 07:08:32.202048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd29b8f513577'
down_revision: Union[str, None] = '51a796697c57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
enum_name = 'stakeoperation'


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cvx_prisma_staking',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('token_balance', sa.Numeric(), nullable=True),
    sa.Column('tvl', sa.Numeric(), nullable=True),
    sa.Column('deposit_count', sa.Numeric(), nullable=True),
    sa.Column('withdraw_count', sa.Numeric(), nullable=True),
    sa.Column('payout_count', sa.Numeric(), nullable=True),
    sa.Column('snapshot_count', sa.Numeric(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__cvx_prisma_staking__chain_id__chains')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__cvx_prisma_staking'))
    )
    op.create_index('idx_cvx_prisma_staking__chain_id__id', 'cvx_prisma_staking', ['chain_id', 'id'], unique=True)
    op.create_table('reward_paid',
    sa.Column('staking_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('token_address', sa.String(), nullable=True),
    sa.Column('token_symbol', sa.String(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('amount_usd', sa.Numeric(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['staking_id'], ['cvx_prisma_staking.id'], name=op.f('fk__reward_paid__staking_id__cvx_prisma_staking')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk__reward_paid__user_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__reward_paid'))
    )
    op.create_index('idx_reward_paid__staking_id__user_id__index', 'reward_paid', ['staking_id', 'user_id', 'index'], unique=True)
    op.create_table('stake_event',
    sa.Column('staking_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('operation', sa.Enum('withdraw', 'stake', name='stakeoperation'), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('amount_usd', sa.Numeric(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['staking_id'], ['cvx_prisma_staking.id'], name=op.f('fk__stake_event__staking_id__cvx_prisma_staking')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk__stake_event__user_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__stake_event'))
    )
    op.create_index('idx_stake_event__staking_id__user_id__index', 'stake_event', ['staking_id', 'user_id', 'index'], unique=True)
    op.create_table('staking_balance',
    sa.Column('staking_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('stake_size', sa.Numeric(), nullable=True),
    sa.Column('timestamp', sa.Numeric(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['staking_id'], ['cvx_prisma_staking.id'], name=op.f('fk__staking_balance__staking_id__cvx_prisma_staking')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk__staking_balance__user_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__staking_balance'))
    )
    op.create_index('idx_staking_balance__staking_id__user_id__timestamp', 'staking_balance', ['staking_id', 'user_id', 'timestamp'], unique=True)
    op.create_table('staking_snapshot',
    sa.Column('staking_id', sa.String(), nullable=True),
    sa.Column('token_balance', sa.Numeric(), nullable=True),
    sa.Column('token_supply', sa.Numeric(), nullable=True),
    sa.Column('tvl', sa.Numeric(), nullable=True),
    sa.Column('total_apr', sa.Numeric(), nullable=True),
    sa.Column('apr_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('timestamp', sa.Numeric(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['staking_id'], ['cvx_prisma_staking.id'], name=op.f('fk__staking_snapshot__staking_id__cvx_prisma_staking')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__staking_snapshot'))
    )
    op.create_index('idx_staking_snapshot__staking_id__timestamp', 'staking_snapshot', ['staking_id', 'timestamp'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_staking_snapshot__staking_id__timestamp', table_name='staking_snapshot')
    op.drop_table('staking_snapshot')
    op.drop_index('idx_staking_balance__staking_id__user_id__timestamp', table_name='staking_balance')
    op.drop_table('staking_balance')
    op.drop_index('idx_stake_event__staking_id__user_id__index', table_name='stake_event')
    op.drop_table('stake_event')
    op.drop_index('idx_reward_paid__staking_id__user_id__index', table_name='reward_paid')
    op.drop_table('reward_paid')
    op.drop_index('idx_cvx_prisma_staking__chain_id__id', table_name='cvx_prisma_staking')
    op.drop_table('cvx_prisma_staking')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Check if the enum exists before trying to remove it
        result = bind.execute("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{}')".format(enum_name))
        exists, = result.fetchone()
        if exists:
            bind.execute(sa.text("DROP TYPE {}".format(enum_name)))
    # ### end Alembic commands ###