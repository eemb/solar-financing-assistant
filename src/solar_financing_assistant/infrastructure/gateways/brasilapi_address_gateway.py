"""BrasilAPI implementation of AddressGatewayPort."""

from typing import Any

import httpx

from solar_financing_assistant.application.dtos.address_dto import AddressDTO
from solar_financing_assistant.application.ports.address_gateway_port import AddressGatewayPort
from solar_financing_assistant.domain.exceptions import InvalidAddressError


class BrasilApiAddressGateway(AddressGatewayPort):
    def __init__(
        self,
        base_url: str = "https://brasilapi.com.br/api",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_address_by_zipcode(self, zipcode: str) -> AddressDTO:
        clean_zipcode = "".join(c for c in zipcode if c.isdigit())

        if len(clean_zipcode) != 8:
            raise InvalidAddressError("Zipcode must have 8 digits.")

        response = await self._client.get(f"{self.base_url}/cep/v2/{clean_zipcode}")

        if response.status_code == 404:
            raise InvalidAddressError("Zipcode not found.")

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        latitude: float | None = None
        longitude: float | None = None
        location = data.get("location")
        if location:
            coordinates = location.get("coordinates")
            if coordinates:
                lat_val = coordinates.get("latitude")
                lon_val = coordinates.get("longitude")
                latitude = float(lat_val) if lat_val else None
                longitude = float(lon_val) if lon_val else None

        return AddressDTO(
            zipcode=data.get("cep", clean_zipcode),
            street=data.get("street"),
            neighborhood=data.get("neighborhood"),
            city=data.get("city"),
            state=data.get("state"),
            latitude=latitude,
            longitude=longitude,
        )
