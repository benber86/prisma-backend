from utils.const import SUBGRAPHS


def get_snapshot_query_setup(
    chain: str, from_index: int, to_index: int | None = None
) -> tuple[int, str]:
    if not to_index:
        to_index = from_index + 1000
    endpoint = SUBGRAPHS[chain]
    return to_index, endpoint
