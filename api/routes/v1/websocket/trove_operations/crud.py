from sqlalchemy import select
from web3 import Web3

from api.routes.v1.websocket.trove_operations.models import TroveOperation
from database.engine import db
from database.models.troves import Trove, TroveSnapshot


async def get_trove_operations(
    manager_id: int, page: int, items: int
) -> list[TroveOperation]:
    offset = (page - 1) * items if page > 0 else 0

    query = (
        select(
            Trove.owner_id.label("owner"),
            TroveSnapshot.operation,
            TroveSnapshot.collateral_usd,
            TroveSnapshot.debt,
            TroveSnapshot.block_timestamp.label("timestamp"),
            TroveSnapshot.transaction_hash.label("hash"),
        )
        .join(TroveSnapshot, Trove.id == TroveSnapshot.trove_id)
        .where(Trove.manager_id == manager_id)
        .order_by(TroveSnapshot.block_timestamp.desc())
        .limit(items)
        .offset(offset)
    )

    result = await db.fetch_all(query)

    operations = [
        TroveOperation(
            owner=Web3.to_checksum_address(row.owner),
            operation=row.operation,
            collateral_usd=float(row.collateral_usd),
            debt=float(row.debt),
            timestamp=int(row.timestamp),
            hash=row.hash,
        )
        for row in result
    ]

    return operations
