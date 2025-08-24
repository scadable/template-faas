from pydantic import BaseModel


class RequestData(BaseModel):
    """Defines the structure for the incoming POST request body."""
    payload: str