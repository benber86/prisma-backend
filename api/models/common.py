from pydantic import BaseModel


class Pagination(BaseModel):
    pagination: int = 10
    page: int = 1
