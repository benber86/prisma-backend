from pydantic import BaseModel


class ChainsResponse(BaseModel):
    data: list[str]
