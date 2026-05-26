from pydantic import BaseModel


class AddressDTO(BaseModel):
    zipcode: str
    street: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
