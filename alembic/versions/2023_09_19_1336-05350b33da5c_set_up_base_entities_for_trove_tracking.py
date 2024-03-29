"""Set up base entities for trove tracking

Revision ID: 05350b33da5c
Revises: 
Create Date: 2023-09-19 13:36:12.419289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05350b33da5c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chains',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__chains'))
    )
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('total_deposited', sa.Numeric(), nullable=True),
    sa.Column('total_collateral_gained_usd', sa.Numeric(), nullable=True),
    sa.Column('vote_count', sa.Integer(), nullable=True),
    sa.Column('lock_balance', sa.Numeric(), nullable=True),
    sa.Column('frozen', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__users'))
    )
    op.create_table('liquidations',
    sa.Column('liquidator_id', sa.String(), nullable=True),
    sa.Column('liquidated_debt', sa.Numeric(), nullable=True),
    sa.Column('liquidated_collateral', sa.Numeric(), nullable=True),
    sa.Column('liquidated_collateral_usd', sa.Numeric(), nullable=True),
    sa.Column('coll_gas_compensation', sa.Numeric(), nullable=True),
    sa.Column('coll_gas_compensation_usd', sa.Numeric(), nullable=True),
    sa.Column('debt_gas_compensation', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['liquidator_id'], ['users.id'], name=op.f('fk__liquidations__liquidator_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__liquidations'))
    )
    op.create_index('idx_liquidations__liquidator_id__block_timestamp', 'liquidations', ['liquidator_id', 'block_timestamp'], unique=True)
    op.create_table('protocols',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('start_time', sa.Numeric(), nullable=True),
    sa.Column('price_feed', sa.String(), nullable=True),
    sa.Column('lockers_count', sa.Integer(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__protocols__chain_id__chains')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__protocols'))
    )
    op.create_index('idx_protocols__chain_id', 'protocols', ['chain_id'], unique=True)
    op.create_table('redemptions',
    sa.Column('redeemer_id', sa.String(), nullable=True),
    sa.Column('attempted_debt_amount', sa.Numeric(), nullable=True),
    sa.Column('actual_debt_amount', sa.Numeric(), nullable=True),
    sa.Column('collateral_sent', sa.Numeric(), nullable=True),
    sa.Column('collateral_sent_usd', sa.Numeric(), nullable=True),
    sa.Column('collateral_sent_to_redeemer', sa.Numeric(), nullable=True),
    sa.Column('collateral_sent_to_redeemer_usd', sa.Numeric(), nullable=True),
    sa.Column('collateral_fee', sa.Numeric(), nullable=True),
    sa.Column('collateral_fee_usd', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['redeemer_id'], ['users.id'], name=op.f('fk__redemptions__redeemer_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__redemptions'))
    )
    op.create_index('idx_redemptions__redeemer_id__block_timestamp', 'redemptions', ['redeemer_id', 'block_timestamp'], unique=True)
    op.create_table('stability_pool',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('snapshots_count', sa.Integer(), nullable=True),
    sa.Column('operations_count', sa.Integer(), nullable=True),
    sa.Column('total_deposited', sa.Numeric(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__stability_pool__chain_id__chains')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__stability_pool'))
    )
    op.create_index('idx_stability_pool__chain_id__address', 'stability_pool', ['chain_id', 'address'], unique=True)
    op.create_table('trove_managers',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('price_feed', sa.String(), nullable=True),
    sa.Column('sunsetting', sa.Boolean(), nullable=True),
    sa.Column('snapshots_count', sa.Integer(), nullable=True),
    sa.Column('trove_snapshots_count', sa.Integer(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__trove_managers__chain_id__chains')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__trove_managers'))
    )
    op.create_index('idx_trove_managers__chain_id__address', 'trove_managers', ['chain_id', 'address'], unique=True)
    op.create_table('collaterals',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('decimals', sa.Integer(), nullable=True),
    sa.Column('symbol', sa.String(), nullable=True),
    sa.Column('latest_price', sa.Numeric(), nullable=True),
    sa.Column('manager_id', sa.BigInteger(), nullable=True),
    sa.Column('stability_pool_id', sa.BigInteger(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__collaterals__chain_id__chains')),
    sa.ForeignKeyConstraint(['manager_id'], ['trove_managers.id'], name=op.f('fk__collaterals__manager_id__trove_managers')),
    sa.ForeignKeyConstraint(['stability_pool_id'], ['stability_pool.id'], name=op.f('fk__collaterals__stability_pool_id__stability_pool')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__collaterals'))
    )
    op.create_index('idx_collaterals__chain_id__address', 'collaterals', ['chain_id', 'address'], unique=True)
    op.create_table('sp_ops',
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('pool_id', sa.BigInteger(), nullable=True),
    sa.Column('operation', sa.Enum('stable_deposit', 'stable_withdrawal', 'collateral_withdrawal', name='stabilitypooloperationtype'), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('stable_amount', sa.Numeric(), nullable=True),
    sa.Column('user_deposit', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['pool_id'], ['stability_pool.id'], name=op.f('fk__sp_ops__pool_id__stability_pool')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk__sp_ops__user_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__sp_ops'))
    )
    op.create_index('idx_sp_ops__pool_id__user_id__index__block_timestamp', 'sp_ops', ['pool_id', 'user_id', 'index', 'block_timestamp'], unique=True)
    op.create_table('stability_pool_snapshots',
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('pool_id', sa.BigInteger(), nullable=True),
    sa.Column('total_deposited', sa.Numeric(), nullable=True),
    sa.Column('total_collateral_withdrawn_usd', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['pool_id'], ['stability_pool.id'], name=op.f('fk__stability_pool_snapshots__pool_id__stability_pool')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__stability_pool_snapshots'))
    )
    op.create_index('idx_stability_pool_snapshots__pool_id__index__block_timestamp', 'stability_pool_snapshots', ['pool_id', 'index', 'block_timestamp'], unique=True)
    op.create_table('trove_manager_parameters',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('minute_decay_factor', sa.Numeric(), nullable=True),
    sa.Column('redemption_fee_floor', sa.Numeric(), nullable=True),
    sa.Column('max_redemption_fee', sa.Numeric(), nullable=True),
    sa.Column('borrowing_fee_floor', sa.Numeric(), nullable=True),
    sa.Column('max_borrowing_fee', sa.Numeric(), nullable=True),
    sa.Column('max_system_debt', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('manager_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['manager_id'], ['trove_managers.id'], name=op.f('fk__trove_manager_parameters__manager_id__trove_managers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__trove_manager_parameters'))
    )
    op.create_index('idx_trove_manager_parameters__manager_id__block_timestamp', 'trove_manager_parameters', ['manager_id', 'block_timestamp'], unique=True)
    op.create_table('troves',
    sa.Column('owner_id', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('open', 'closed_by_owner', 'closed_by_liquidation', 'closed_by_redemption', name='trovestatus'), nullable=True),
    sa.Column('manager_id', sa.BigInteger(), nullable=True),
    sa.Column('snapshots_count', sa.Integer(), nullable=True),
    sa.Column('collateral', sa.Numeric(), nullable=True),
    sa.Column('collateral_usd', sa.Numeric(), nullable=True),
    sa.Column('debt', sa.Numeric(), nullable=True),
    sa.Column('stake', sa.Numeric(), nullable=True),
    sa.Column('reward_snapshot_collateral', sa.Numeric(), nullable=True),
    sa.Column('reward_snapshot_debt', sa.Numeric(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['manager_id'], ['trove_managers.id'], name=op.f('fk__troves__manager_id__trove_managers')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk__troves__owner_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__troves'))
    )
    op.create_index('idx_troves__manager_id__owner_id', 'troves', ['manager_id', 'owner_id'], unique=True)
    op.create_table('collateral_withdrawals',
    sa.Column('collateral_id', sa.BigInteger(), nullable=True),
    sa.Column('collateral_amount', sa.Numeric(), nullable=True),
    sa.Column('collateral_amount_usd', sa.Numeric(), nullable=True),
    sa.Column('operation_id', sa.BigInteger(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['collateral_id'], ['collaterals.id'], name=op.f('fk__collateral_withdrawals__collateral_id__collaterals')),
    sa.ForeignKeyConstraint(['operation_id'], ['sp_ops.id'], name=op.f('fk__collateral_withdrawals__operation_id__sp_ops')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__collateral_withdrawals'))
    )
    op.create_index('idx_collateral_withdrawals__collateral_id__operation_id', 'collateral_withdrawals', ['collateral_id', 'operation_id'], unique=True)
    op.create_table('price_records',
    sa.Column('collateral_id', sa.BigInteger(), nullable=True),
    sa.Column('price', sa.Numeric(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['collateral_id'], ['collaterals.id'], name=op.f('fk__price_records__collateral_id__collaterals')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__price_records'))
    )
    op.create_index('idx_price_records__collateral_id__block_timestamp', 'price_records', ['collateral_id', 'block_timestamp'], unique=True)
    op.create_table('trove_manager_snapshots',
    sa.Column('manager_id', sa.BigInteger(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('collateral_price', sa.Numeric(), nullable=True),
    sa.Column('rate', sa.Numeric(), nullable=True),
    sa.Column('borrowing_fee', sa.Numeric(), nullable=True),
    sa.Column('collateral_ratio', sa.Numeric(), nullable=True),
    sa.Column('total_collateral', sa.Numeric(), nullable=True),
    sa.Column('total_collateral_usd', sa.Numeric(), nullable=True),
    sa.Column('total_debt', sa.Numeric(), nullable=True),
    sa.Column('total_stakes', sa.Numeric(), nullable=True),
    sa.Column('total_borrowing_fees_paid', sa.Numeric(), nullable=True),
    sa.Column('total_redemption_fees_paid', sa.Numeric(), nullable=True),
    sa.Column('total_redemption_fees_paid_usd', sa.Numeric(), nullable=True),
    sa.Column('total_collateral_redistributed', sa.Numeric(), nullable=True),
    sa.Column('total_collateral_redistributed_usd', sa.Numeric(), nullable=True),
    sa.Column('total_debt_redistributed', sa.Numeric(), nullable=True),
    sa.Column('open_troves', sa.Integer(), nullable=True),
    sa.Column('total_troves_opened', sa.Integer(), nullable=True),
    sa.Column('liquidated_troves', sa.Integer(), nullable=True),
    sa.Column('total_troves_liquidated', sa.Integer(), nullable=True),
    sa.Column('redeemed_troves', sa.Integer(), nullable=True),
    sa.Column('total_troves_redeemed', sa.Integer(), nullable=True),
    sa.Column('closed_troves', sa.Integer(), nullable=True),
    sa.Column('total_troves_closed', sa.Integer(), nullable=True),
    sa.Column('total_troves', sa.Integer(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('parameters_id', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['manager_id'], ['trove_managers.id'], name=op.f('fk__trove_manager_snapshots__manager_id__trove_managers')),
    sa.ForeignKeyConstraint(['parameters_id'], ['trove_manager_parameters.id'], name=op.f('fk__trove_manager_snapshots__parameters_id__trove_manager_parameters')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__trove_manager_snapshots'))
    )
    op.create_index('idx_trove_manager_snapshots__manager_id__block_timestamp__index', 'trove_manager_snapshots', ['manager_id', 'block_timestamp', 'index'], unique=True)
    op.create_table('trove_snapshots',
    sa.Column('trove_id', sa.BigInteger(), nullable=True),
    sa.Column('operation', sa.Enum('open_trove', 'close_trove', 'adjust_trove', 'apply_pending_rewards', 'liquidate_in_normal_mode', 'liquidate_in_recovery_mode', 'redeem_collateral', name='troveoperation'), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('collateral', sa.Numeric(), nullable=True),
    sa.Column('collateral_usd', sa.Numeric(), nullable=True),
    sa.Column('collateral_ratio', sa.Numeric(), nullable=True),
    sa.Column('debt', sa.Numeric(), nullable=True),
    sa.Column('stake', sa.Numeric(), nullable=True),
    sa.Column('borrowing_fee', sa.Numeric(), nullable=True),
    sa.Column('liquidation_id', sa.BigInteger(), nullable=True),
    sa.Column('redemption_id', sa.BigInteger(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['liquidation_id'], ['liquidations.id'], name=op.f('fk__trove_snapshots__liquidation_id__liquidations')),
    sa.ForeignKeyConstraint(['redemption_id'], ['redemptions.id'], name=op.f('fk__trove_snapshots__redemption_id__redemptions')),
    sa.ForeignKeyConstraint(['trove_id'], ['troves.id'], name=op.f('fk__trove_snapshots__trove_id__troves')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__trove_snapshots'))
    )
    op.create_index('idx_trove_snapshots__trove_id__block_timestamp__index', 'trove_snapshots', ['trove_id', 'block_timestamp', 'index'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_trove_snapshots__trove_id__block_timestamp__index', table_name='trove_snapshots')
    op.drop_table('trove_snapshots')
    op.drop_index('idx_trove_manager_snapshots__manager_id__block_timestamp__index', table_name='trove_manager_snapshots')
    op.drop_table('trove_manager_snapshots')
    op.drop_index('idx_price_records__collateral_id__block_timestamp', table_name='price_records')
    op.drop_table('price_records')
    op.drop_index('idx_collateral_withdrawals__collateral_id__operation_id', table_name='collateral_withdrawals')
    op.drop_table('collateral_withdrawals')
    op.drop_index('idx_troves__manager_id__owner_id', table_name='troves')
    op.drop_table('troves')
    op.drop_index('idx_trove_manager_parameters__manager_id__block_timestamp', table_name='trove_manager_parameters')
    op.drop_table('trove_manager_parameters')
    op.drop_index('idx_stability_pool_snapshots__pool_id__index__block_timestamp', table_name='stability_pool_snapshots')
    op.drop_table('stability_pool_snapshots')
    op.drop_index('idx_sp_ops__pool_id__user_id__index__block_timestamp', table_name='sp_ops')
    op.drop_table('sp_ops')
    op.drop_index('idx_collaterals__chain_id__address', table_name='collaterals')
    op.drop_table('collaterals')
    op.drop_index('idx_trove_managers__chain_id__address', table_name='trove_managers')
    op.drop_table('trove_managers')
    op.drop_index('idx_stability_pool__chain_id__address', table_name='stability_pool')
    op.drop_table('stability_pool')
    op.drop_index('idx_redemptions__redeemer_id__block_timestamp', table_name='redemptions')
    op.drop_table('redemptions')
    op.drop_index('idx_protocols__chain_id', table_name='protocols')
    op.drop_table('protocols')
    op.drop_index('idx_liquidations__liquidator_id__block_timestamp', table_name='liquidations')
    op.drop_table('liquidations')
    op.drop_table('users')
    op.drop_table('chains')
    # ### end Alembic commands ###
