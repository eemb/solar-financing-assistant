from typing import Protocol, runtime_checkable

from solar_financing_assistant.application.dtos.address_dto import AddressDTO


@runtime_checkable
class AddressGatewayPort(Protocol):
    async def get_address_by_zipcode(self, zipcode: str) -> AddressDTO: ...
