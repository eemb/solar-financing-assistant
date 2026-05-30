"""Use case for validating and fetching address data by zipcode."""

import logging

from solar_financing_assistant.application.ports.address_gateway_port import AddressGatewayPort
from solar_financing_assistant.domain.entities.address import Address
from solar_financing_assistant.domain.exceptions import InvalidAddressError

logger = logging.getLogger(__name__)

# Fields that are expected to be present for a meaningful address.
_DISPLAY_FIELDS = ("city", "state", "street", "neighborhood")


class ValidateAddressUseCase:
    def __init__(self, address_gateway: AddressGatewayPort) -> None:
        self.address_gateway = address_gateway

    async def execute(self, zipcode: str) -> Address:
        if not zipcode or not zipcode.strip():
            raise InvalidAddressError("Address zipcode is required.")

        dto = await self.address_gateway.get_address_by_zipcode(zipcode)

        if not dto.zipcode:
            raise InvalidAddressError("Zipcode not found.")

        address = Address(
            zip_code=dto.zipcode,
            street=dto.street or "",
            number=None,
            neighborhood=dto.neighborhood or "",
            city=dto.city or "",
            state=dto.state or "",
            latitude=dto.latitude,
            longitude=dto.longitude,
        )

        missing = [f for f in _DISPLAY_FIELDS if not getattr(address, f)]
        if missing:
            logger.warning(
                "Address for zipcode %s is missing display fields: %s. "
                "Output may appear incomplete.",
                zipcode,
                ", ".join(missing),
            )

        return address
