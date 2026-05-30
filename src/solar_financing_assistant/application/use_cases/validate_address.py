"""Use case for validating and fetching address data by zipcode."""

from solar_financing_assistant.application.ports.address_gateway_port import AddressGatewayPort
from solar_financing_assistant.domain.entities.address import Address
from solar_financing_assistant.domain.exceptions import InvalidAddressError


class ValidateAddressUseCase:
    def __init__(self, address_gateway: AddressGatewayPort) -> None:
        self.address_gateway = address_gateway

    async def execute(self, zipcode: str) -> Address:
        if not zipcode or not zipcode.strip():
            raise InvalidAddressError("Address zipcode is required.")

        dto = await self.address_gateway.get_address_by_zipcode(zipcode)

        if not dto.zipcode:
            raise InvalidAddressError("Zipcode not found.")

        return Address(
            zip_code=dto.zipcode,
            street=dto.street or "",
            number=None,
            neighborhood=dto.neighborhood or "",
            city=dto.city or "",
            state=dto.state or "",
            latitude=dto.latitude,
            longitude=dto.longitude,
        )
