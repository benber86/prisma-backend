import logging
from enum import Enum

from sqlalchemy import and_, desc, func, select
from web3 import Web3

from api.models.common import Pagination
from api.routes.v1.rest.dao.models import (
    OrderFilter,
    OwnershipProposalDetail,
    OwnershipProposalDetailResponse,
)
from database.engine import db
from database.models.common import User
from database.models.dao import OwnershipProposal


async def search_ownership_proposals(
    chain_id: int,
    pagination: Pagination,
    order: OrderFilter,
) -> OwnershipProposalDetailResponse:

    query = (
        select([OwnershipProposal, User.label.label("creator_label")])
        .join(User, OwnershipProposal.creator_id == User.id)
        .where(OwnershipProposal.chain_id == chain_id)
    )

    if order.creator_filter:
        query = query.where(
            OwnershipProposal.creator_id == order.creator_filter
        )
    if order.decode_data_filter:
        query = query.where(
            OwnershipProposal.decode_data == order.decode_data_filter
        )

    order_column = getattr(OwnershipProposal, order.order_by)  # type: ignore
    if order.desc:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column)

    items_per_page = pagination.items
    offset = (pagination.page - 1) * items_per_page
    query = query.limit(items_per_page).offset(offset)

    results = await db.fetch_all(query)
    proposals = []
    for result in results:
        result_dict = dict(result)
        result_dict["creator"] = Web3.to_checksum_address(
            result_dict["creator_id"]
        )
        if isinstance(result_dict["status"], Enum):
            result_dict["status"] = result_dict["status"].value
        proposal = OwnershipProposalDetail(**result_dict)
        proposals.append(proposal)
    return OwnershipProposalDetailResponse(proposals=proposals)
