from sqlalchemy import (
    String,
    and_,
    case,
    cast,
    desc,
    func,
    join,
    null,
    or_,
    select,
)
from sqlalchemy.orm import aliased

from api.models.common import Pagination
from api.routes.v1.rest.trove.models import (
    FilterSet,
    Status,
    TroveEntry,
    TroveEntryReponse,
    TroveHistoryData,
    TroveHistoryResponse,
    TroveSnapshotData,
    TroveSnapshotsResponse,
)
from database.engine import db
from database.models.troves import Trove, TroveManagerSnapshot, TroveSnapshot


def _map_trove_to_entry(trove, created_at, last_update, collateral_ratio):
    status_mapping = {
        "open": Status.open,
        "closedByOwner": Status.closed_by_owner,
        "closedByLiquidation": Status.closed_by_liquidation,
        "closedByRedemption": Status.closed_by_redemption,
    }

    return TroveEntry(
        owner=trove["owner_id"],
        status=status_mapping.get(trove["status"].value, Status.open),
        collateral_usd=float(trove["collateral_usd"]),
        debt=float(trove["debt"]),
        collateral_ratio=collateral_ratio,
        created_at=int(created_at),
        last_update=int(last_update),
    )


async def search_for_troves(
    manager_id: int, pagination: Pagination, filter_set: FilterSet
) -> TroveEntryReponse | None:
    first_snapshot = aliased(TroveSnapshot)
    last_snapshot = aliased(TroveSnapshot)

    collateral_ratio = case(
        [(Trove.debt == 0, 0)], else_=(Trove.collateral_usd / Trove.debt)
    ).label("collateral_ratio")

    if filter_set.order_by in [
        "last_update",
        "created_at",
        "collateral_ratio",
    ]:
        if filter_set.order_by == "last_update":
            order_by_column = func.max(last_snapshot.block_timestamp)
        elif filter_set.order_by == "created_at":
            order_by_column = func.min(first_snapshot.block_timestamp)
        elif filter_set.order_by == "collateral_ratio":
            order_by_column = collateral_ratio
    else:
        order_by_column = getattr(Trove, filter_set.order_by)  # type: ignore

    query = (
        select(
            Trove.owner_id,
            Trove.status,
            Trove.collateral_usd,
            Trove.debt,
            func.min(first_snapshot.block_timestamp).label("created_at"),
            func.max(last_snapshot.block_timestamp).label("last_update"),
            collateral_ratio,
        )
        .join(first_snapshot, first_snapshot.trove_id == Trove.id)
        .join(last_snapshot, last_snapshot.trove_id == Trove.id)
        .where(Trove.manager_id == manager_id)
        .group_by(Trove.id)
    )

    if filter_set.owner_filter:
        query = query.where(
            Trove.owner_id.ilike(f"%{filter_set.owner_filter}%")
        )

    total_entries = await db.fetch_val(query.with_only_columns([func.count()]))

    items = min(pagination.items, 100)
    page = pagination.page if pagination else 1

    query = query.order_by(
        desc(order_by_column) if filter_set.desc else order_by_column
    )
    query = query.offset((page - 1) * items).limit(items)

    result = await db.fetch_all(query)
    if not result:
        return None

    trove_entries = [
        _map_trove_to_entry(
            {
                "owner_id": row[0],
                "status": row[1],
                "collateral_usd": row[2],
                "debt": row[3],
            },
            row[4],
            row[5],
            row[6],
        )
        for row in result
    ]
    return TroveEntryReponse(
        page=page, total_entries=total_entries, troves=trove_entries
    )


async def get_all_snapshots(
    manager_id: int, owner: str
) -> TroveSnapshotsResponse:
    query = (
        select(
            [
                cast(TroveSnapshot.operation, String).label("operation"),
                TroveSnapshot.collateral,
                TroveSnapshot.collateral_usd,
                TroveSnapshot.collateral_ratio.label("cr"),
                TroveSnapshot.debt,
                TroveSnapshot.stake,
                TroveSnapshot.block_number.label("block"),
                TroveSnapshot.block_timestamp.label("timestamp"),
                TroveSnapshot.transaction_hash.label("hash"),
            ]
        )
        .join(Trove, Trove.id == TroveSnapshot.trove_id)
        .where(
            and_(Trove.manager_id == manager_id, Trove.owner_id.ilike(owner))
        )
    )

    results = await db.fetch_all(query)

    snapshots = [TroveSnapshotData(**dict(result)) for result in results]

    return TroveSnapshotsResponse(snapshots=snapshots)


async def get_snapshot_historical_stats(
    manager_id: int, owner_id: str
) -> TroveHistoryResponse:
    trove_snapshots = (
        select(
            TroveSnapshot.collateral,
            TroveSnapshot.debt,
            TroveSnapshot.block_timestamp.label("snapshot_timestamp"),
            func.lead(TroveSnapshot.block_timestamp)
            .over(order_by=TroveSnapshot.block_timestamp)
            .label("next_snapshot_timestamp"),
        )
        .join(
            Trove,
            and_(
                TroveSnapshot.trove_id == Trove.id,
                Trove.owner_id.ilike(owner_id),
                Trove.manager_id == manager_id,
            ),
        )
        .order_by(TroveSnapshot.block_timestamp)
    ).cte("trove_snapshots")

    max_timestamp_subquery = (
        select(
            func.max(TroveManagerSnapshot.block_timestamp).label(
                "max_timestamp"
            )
        ).where(TroveManagerSnapshot.manager_id == manager_id)
    ).alias("max_timestamp_subquery")

    manager_snapshots = (
        select(
            TroveManagerSnapshot.block_timestamp,
            TroveManagerSnapshot.collateral_price,
        )
        .where(TroveManagerSnapshot.manager_id == manager_id)
        .distinct(TroveManagerSnapshot.collateral_price)
        .order_by(
            TroveManagerSnapshot.collateral_price,
            TroveManagerSnapshot.block_timestamp,
        )
    ).alias("manager_snapshots")

    query = (
        select(
            trove_snapshots.c.collateral,
            trove_snapshots.c.debt,
            manager_snapshots.c.block_timestamp,
            (
                trove_snapshots.c.collateral
                * manager_snapshots.c.collateral_price
            ).label("collateral_usd"),
            case(
                [(trove_snapshots.c.debt == 0, None)],
                else_=(
                    (
                        trove_snapshots.c.collateral
                        * manager_snapshots.c.collateral_price
                    )
                    / trove_snapshots.c.debt
                ),
            ).label("cr"),
        )
        .join(
            manager_snapshots,
            and_(
                manager_snapshots.c.block_timestamp
                >= trove_snapshots.c.snapshot_timestamp,
                or_(
                    trove_snapshots.c.next_snapshot_timestamp
                    == None,  # noqa: E711
                    manager_snapshots.c.block_timestamp
                    < trove_snapshots.c.next_snapshot_timestamp,
                ),
            ),
        )
        .join(
            max_timestamp_subquery,
            manager_snapshots.c.block_timestamp
            <= max_timestamp_subquery.c.max_timestamp,
            isouter=True,
        )
        .order_by(manager_snapshots.c.block_timestamp)
    )

    results = await db.fetch_all(query)

    history_data = [
        TroveHistoryData(
            collateral=float(result.collateral),
            collateral_usd=float(result.collateral_usd),
            cr=float(result.cr) if result.cr is not None else None,
            debt=float(result.debt),
            timestamp=int(result.block_timestamp),
        )
        for result in results
    ]

    return TroveHistoryResponse(history=history_data)
