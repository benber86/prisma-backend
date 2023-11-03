from utils.const import CVXPRISMA_SUBGRAPHS


def get_cvxprisma_snapshot_query_setup(
    chain: str, from_index: int, to_index: int | None = None
) -> tuple[int, str]:
    if not to_index:
        to_index = from_index + 1000
    endpoint = CVXPRISMA_SUBGRAPHS[chain]
    return to_index, endpoint
