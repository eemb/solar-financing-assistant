"""Integration tests for BrasilApiAddressGateway (requires network access)."""

import pytest

from solar_financing_assistant.domain.exceptions import InvalidAddressError
from solar_financing_assistant.infrastructure.gateways.brasilapi_address_gateway import (
    BrasilApiAddressGateway,
)


@pytest.mark.integration
async def test_returns_full_address_data_for_known_zipcode() -> None:
    gateway = BrasilApiAddressGateway()

    dto = await gateway.get_address_by_zipcode("01001000")

    assert dto.zipcode == "01001000"
    assert dto.city == "São Paulo"
    assert dto.state == "SP"
    assert dto.street is not None
    assert dto.neighborhood is not None


@pytest.mark.integration
async def test_coordinates_are_float_or_none() -> None:
    """Coordinates are optional in BrasilAPI — when present they must be floats."""
    gateway = BrasilApiAddressGateway()

    dto = await gateway.get_address_by_zipcode("01001000")

    if dto.latitude is not None:
        assert isinstance(dto.latitude, float)
    if dto.longitude is not None:
        assert isinstance(dto.longitude, float)


@pytest.mark.integration
async def test_accepts_formatted_zipcode_with_hyphen() -> None:
    gateway = BrasilApiAddressGateway()

    dto = await gateway.get_address_by_zipcode("01001-000")

    assert dto.zipcode == "01001000"
    assert dto.city == "São Paulo"


@pytest.mark.integration
async def test_raises_for_nonexistent_zipcode() -> None:
    gateway = BrasilApiAddressGateway()

    with pytest.raises(InvalidAddressError, match="Zipcode not found."):
        await gateway.get_address_by_zipcode("00000000")


@pytest.mark.integration
async def test_raises_for_zipcode_with_wrong_digit_count() -> None:
    gateway = BrasilApiAddressGateway()

    with pytest.raises(InvalidAddressError, match="8 digits"):
        await gateway.get_address_by_zipcode("0100100")
