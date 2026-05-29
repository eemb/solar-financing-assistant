"""Unit tests for ValidateAddressUseCase."""

import pytest

from solar_financing_assistant.application.dtos.address_dto import AddressDTO
from solar_financing_assistant.application.use_cases.validate_address import ValidateAddressUseCase
from solar_financing_assistant.domain.exceptions import InvalidAddressError


class FakeAddressGateway:
    async def get_address_by_zipcode(self, zipcode: str) -> AddressDTO:
        return AddressDTO(
            zipcode="01001000",
            street="Praça da Sé",
            neighborhood="Sé",
            city="São Paulo",
            state="SP",
            latitude=-23.54819,
            longitude=-46.63382,
        )


class FakeEmptyZipcodeGateway:
    async def get_address_by_zipcode(self, zipcode: str) -> AddressDTO:
        return AddressDTO(zipcode="")


async def test_returns_domain_address_with_city_state_and_coordinates() -> None:
    use_case = ValidateAddressUseCase(FakeAddressGateway())

    address = await use_case.execute("01001000")

    assert address.city == "São Paulo"
    assert address.state == "SP"
    assert address.latitude == -23.54819
    assert address.longitude == -46.63382


async def test_raises_when_input_zipcode_is_empty() -> None:
    use_case = ValidateAddressUseCase(FakeAddressGateway())

    with pytest.raises(InvalidAddressError, match="zipcode is required"):
        await use_case.execute("")


async def test_raises_when_dto_returns_empty_zipcode() -> None:
    use_case = ValidateAddressUseCase(FakeEmptyZipcodeGateway())

    with pytest.raises(InvalidAddressError):
        await use_case.execute("01001000")
