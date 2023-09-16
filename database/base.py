import sqlalchemy as sa
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# @see https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "all_column_names": lambda constraint, table: "_".join(
        [column.name for column in constraint.columns.values()]
    ),
    "ix": "ix__%(all_column_names)s",
    "uq": "uq__%(table_name)s__%(all_column_names)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}

metadata = sa.MetaData(naming_convention=convention)


@as_declarative(metadata=metadata)
class Base:
    """Base class for all models with created_at attr"""

    @declared_attr
    def id(cls):
        return sa.Column(sa.BigInteger, primary_key=True)

    @declared_attr
    def created_at(cls):
        return sa.Column(
            sa.DateTime,
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        )
