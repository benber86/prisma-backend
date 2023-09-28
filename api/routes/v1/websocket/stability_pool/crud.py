from sqlalchemy import case, desc, func, select

from api.routes.v1.websocket.stability_pool.models import (
    StabilityPoolOperationDetails,
    StabilityPoolOperationType,
)
from database.engine import db
from database.models.troves import (
    CollateralWithdrawal,
    StabilityPool,
    StabilityPoolOperation,
)


async def get_pool_operations(
    chain_id, page, items
) -> list[StabilityPoolOperationDetails]:
    query = (
        select(
            StabilityPoolOperation.user_id.label("user"),
            StabilityPoolOperation.operation,
            func.coalesce(
                func.sum(
                    case(
                        [
                            (
                                StabilityPoolOperation.operation
                                == StabilityPoolOperation.StabilityPoolOperationType.collateral_withdrawal,
                                CollateralWithdrawal.collateral_amount_usd,
                            )
                        ],
                        else_=StabilityPoolOperation.stable_amount,
                    )
                ),
                0,
            ).label("amount"),
            StabilityPoolOperation.transaction_hash.label("hash"),
        )
        .join(
            StabilityPool, StabilityPool.id == StabilityPoolOperation.pool_id
        )
        .outerjoin(
            CollateralWithdrawal,
            CollateralWithdrawal.operation_id == StabilityPoolOperation.id,
        )
        .where(StabilityPool.chain_id == chain_id)
        .group_by(StabilityPoolOperation.id)
        .order_by(desc(StabilityPoolOperation.block_timestamp))
        .limit(items)
        .offset((page - 1) * items)
    )

    result = await db.fetch_all(query)
    return [
        StabilityPoolOperationDetails(
            user=op["user"],
            operation=StabilityPoolOperationType(op["operation"].value),
            amount=float(op["amount"]),
            hash=op["hash"],
        )
        for op in result
    ]
