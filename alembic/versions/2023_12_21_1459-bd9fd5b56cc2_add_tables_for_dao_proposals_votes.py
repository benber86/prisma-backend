"""Add tables for dao proposals/votes

Revision ID: bd9fd5b56cc2
Revises: bf815fca9595
Create Date: 2023-12-21 14:59:40.768764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bd9fd5b56cc2'
down_revision: Union[str, None] = 'bf815fca9595'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
enum_name = 'ownershipproposalstatus'

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('incentive_receivers',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__incentive_receivers__chain_id__chains')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__incentive_receivers'))
    )
    op.create_index('idx_incentive_receivers__address__index__chain_id', 'incentive_receivers', ['address', 'index', 'chain_id'], unique=True)
    op.create_table('ownership_proposals',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('creator_id', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('not_passed', 'passed', 'cancelled', 'executed', name=enum_name), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('decode_data', sa.String(), nullable=True),
    sa.Column('week', sa.Integer(), nullable=True),
    sa.Column('required_weight', sa.Numeric(), nullable=True),
    sa.Column('received_weight', sa.Numeric(), nullable=True),
    sa.Column('can_execute_after', sa.Integer(), nullable=True),
    sa.Column('vote_count', sa.Integer(), nullable=True),
    sa.Column('execution_tx', sa.String(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__ownership_proposals__chain_id__chains')),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], name=op.f('fk__ownership_proposals__creator_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__ownership_proposals'))
    )
    op.create_index('idx_ownership_proposals__chain_id__creator_id__index', 'ownership_proposals', ['chain_id', 'creator_id', 'index'], unique=True)
    op.create_table('incentive_votes',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('voter_id', sa.String(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('week', sa.Integer(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.Column('is_clearance', sa.Boolean(), nullable=True),
    sa.Column('target_id', sa.BigInteger(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__incentive_votes__chain_id__chains')),
    sa.ForeignKeyConstraint(['target_id'], ['incentive_receivers.id'], name=op.f('fk__incentive_votes__target_id__incentive_receivers')),
    sa.ForeignKeyConstraint(['voter_id'], ['users.id'], name=op.f('fk__incentive_votes__voter_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__incentive_votes'))
    )
    op.create_index('idx_incentive_votes__index__week__chain_id__voter_id__target_id', 'incentive_votes', ['index', 'week', 'chain_id', 'voter_id', 'target_id'], unique=True)
    op.create_table('ownership_vote',
    sa.Column('proposal_id', sa.BigInteger(), nullable=True),
    sa.Column('voter_id', sa.String(), nullable=True),
    sa.Column('weight', sa.Numeric(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.Column('account_weight', sa.Numeric(), nullable=True),
    sa.Column('decisive', sa.Boolean(), nullable=True),
    sa.Column('block_number', sa.Numeric(), nullable=True),
    sa.Column('block_timestamp', sa.Numeric(), nullable=True),
    sa.Column('transaction_hash', sa.String(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['proposal_id'], ['ownership_proposals.id'], name=op.f('fk__ownership_vote__proposal_id__ownership_proposals')),
    sa.ForeignKeyConstraint(['voter_id'], ['users.id'], name=op.f('fk__ownership_vote__voter_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__ownership_vote'))
    )
    op.create_index('idx_ownership_vote__proposal_id__user_id__index', 'ownership_vote', ['proposal_id', 'voter_id', 'index'], unique=True)
    op.create_table('user_incent_points',
    sa.Column('chain_id', sa.BigInteger(), nullable=False),
    sa.Column('voter_id', sa.String(), nullable=True),
    sa.Column('receiver_id', sa.BigInteger(), nullable=True),
    sa.Column('week', sa.Integer(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], name=op.f('fk__user_incent_points__chain_id__chains')),
    sa.ForeignKeyConstraint(['receiver_id'], ['incentive_receivers.id'], name=op.f('fk__user_incent_points__receiver_id__incentive_receivers')),
    sa.ForeignKeyConstraint(['voter_id'], ['users.id'], name=op.f('fk__user_incent_points__voter_id__users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__user_incent_points'))
    )
    op.create_index('idx_user_incent_points__week__chain_id__voter_id__receiver_id', 'user_incent_points', ['week', 'chain_id', 'voter_id', 'receiver_id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_user_incent_points__week__chain_id__voter_id__receiver_id', table_name='user_incent_points')
    op.drop_table('user_incent_points')
    op.drop_index('idx_ownership_vote__proposal_id__user_id__index', table_name='ownership_vote')
    op.drop_table('ownership_vote')
    op.drop_index('idx_incentive_votes__index__week__chain_id__voter_id__target_id', table_name='incentive_votes')
    op.drop_table('incentive_votes')
    op.drop_index('idx_ownership_proposals__chain_id__creator_id__index', table_name='ownership_proposals')
    op.drop_table('ownership_proposals')
    op.drop_index('idx_incentive_receivers__address__index__chain_id', table_name='incentive_receivers')
    op.drop_table('incentive_receivers')
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Check if the enum exists before trying to remove it
        result = bind.execute("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{}')".format(enum_name))
        exists, = result.fetchone()
        if exists:
            bind.execute(sa.text("DROP TYPE {}".format(enum_name)))
    # ### end Alembic commands ###
