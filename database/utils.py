from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from .base import Base


def upsert_query(
    model: type[Base], indexes: dict, data: dict, return_columns: list = None
):
    query = (
        insert(model)
        .values(**indexes, **data)
        .on_conflict_do_update(index_elements=[*indexes], set_=data)
    )
    if return_columns:
        query = query.returning(*return_columns)
    return query


def insert_ignore_query(
    model: type[Base], indexes: dict, data: dict, return_columns: list = None
):
    query = (
        insert(model)
        .values(**indexes, **data)
        .on_conflict_do_nothing(index_elements=[*indexes])
    )
    if return_columns:
        query = query.returning(*return_columns)
    return query


def batch_insert_ignore(model: type[Base], data: list[dict]):
    query = insert(model).values(data).on_conflict_do_nothing()
    return query


def update_by_id_query(model: type[Base], row_id: int, update_data: dict):
    query = (
        update(model.__table__)  # type: ignore
        .where(model.id == row_id)
        .values(**update_data)
    )
    return query
