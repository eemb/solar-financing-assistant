"""Unit tests for EstimateSolarProjectFromBillUseCase."""

from decimal import Decimal

import pytest

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
from solar_financing_assistant.application.use_cases.estimate_solar_project import (
    EstimateSolarProjectUseCase,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project_from_bill import (
    EstimateSolarProjectFromBillUseCase,
)
from solar_financing_assistant.domain.entities.address import Address
from solar_financing_assistant.domain.exceptions import SimulationError

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

_ADDRESS_WITH_COORDS = Address(
    zip_code="52000000",
    street="Rua Exemplo",
    number="",
    neighborhood="Bairro",
    city="Recife",
    state="PE",
    latitude=-8.0476,
    longitude=-34.877,
)

_ADDRESS_NO_COORDS = Address(
    zip_code="52000000",
    street="Rua Exemplo",
    number="",
    neighborhood="Bairro",
    city="Recife",
    state="PE",
    latitude=None,
    longitude=None,
)

_SOLAR_POTENTIAL = SolarPotentialDTO(
    latitude=-8.0476,
    longitude=-34.877,
    estimated_daily_generation_kwh_per_kwp=4.0,
)


class FakeValidateAddressUseCase:
    def __init__(self, address: Address, raises: Exception | None = None) -> None:
        self._address = address
        self._raises = raises

    async def execute(self, zipcode: str) -> Address:
        if self._raises is not None:
            raise self._raises
        return self._address


class FakeGetSolarPotentialUseCase:
    def __init__(
        self,
        dto: SolarPotentialDTO | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._dto = dto
        self._raises = raises

    async def execute(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        if self._raises is not None:
            raise self._raises
        assert self._dto is not None
        return self._dto


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FALLBACK = 120.0
_COST_PER_KWP = Decimal("5000.00")


def _make_use_case(
    validate_address: FakeValidateAddressUseCase | None = None,
    get_solar_potential: FakeGetSolarPotentialUseCase | None = None,
) -> EstimateSolarProjectFromBillUseCase:
    return EstimateSolarProjectFromBillUseCase(
        validate_address_use_case=validate_address
        or FakeValidateAddressUseCase(_ADDRESS_NO_COORDS),
        get_solar_potential_use_case=get_solar_potential
        or FakeGetSolarPotentialUseCase(_SOLAR_POTENTIAL),
        estimate_solar_project_use_case=EstimateSolarProjectUseCase(),
        fallback_generation_per_kwp_month=_FALLBACK,
        cost_per_kwp_brl=_COST_PER_KWP,
    )


def _make_bill(
    monthly_consumption_kwh: float | None = 450.0,
    zipcode: str | None = "52000000",
) -> ExtractedEnergyBillDataDTO:
    return ExtractedEnergyBillDataDTO(
        customer_name="Test User",
        distributor="Test Distributor",
        monthly_consumption_kwh=monthly_consumption_kwh,
        monthly_cost_brl=Decimal("380.50"),
        zipcode=zipcode,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uses_solar_potential_when_zipcode_and_coords_available() -> None:
    """generation_per_kwp_month = 4.0 * 30 = 120 → system = 450 / 120 = 3.75 kWp."""
    use_case = _make_use_case(
        validate_address=FakeValidateAddressUseCase(_ADDRESS_WITH_COORDS),
        get_solar_potential=FakeGetSolarPotentialUseCase(_SOLAR_POTENTIAL),
    )

    project = await use_case.execute(_make_bill(monthly_consumption_kwh=450.0))

    assert project.estimated_system_kwp == pytest.approx(3.75)
    assert project.monthly_consumption_kwh == 450.0


@pytest.mark.asyncio
async def test_uses_fallback_when_no_zipcode() -> None:
    use_case = _make_use_case(
        validate_address=FakeValidateAddressUseCase(_ADDRESS_WITH_COORDS),
        get_solar_potential=FakeGetSolarPotentialUseCase(_SOLAR_POTENTIAL),
    )

    project = await use_case.execute(_make_bill(zipcode=None))

    assert project.estimated_system_kwp == pytest.approx(450.0 / _FALLBACK)


@pytest.mark.asyncio
async def test_uses_fallback_when_address_has_no_coords() -> None:
    use_case = _make_use_case(
        validate_address=FakeValidateAddressUseCase(_ADDRESS_NO_COORDS),
    )

    project = await use_case.execute(_make_bill())

    assert project.estimated_system_kwp == pytest.approx(450.0 / _FALLBACK)


@pytest.mark.asyncio
async def test_uses_fallback_when_validate_address_raises() -> None:
    use_case = _make_use_case(
        validate_address=FakeValidateAddressUseCase(
            _ADDRESS_WITH_COORDS,
            raises=Exception("BrasilAPI unavailable"),
        ),
    )

    project = await use_case.execute(_make_bill())

    assert project.estimated_system_kwp == pytest.approx(450.0 / _FALLBACK)


@pytest.mark.asyncio
async def test_uses_fallback_when_solar_potential_raises() -> None:
    use_case = _make_use_case(
        validate_address=FakeValidateAddressUseCase(_ADDRESS_WITH_COORDS),
        get_solar_potential=FakeGetSolarPotentialUseCase(
            raises=Exception("Open-Meteo unavailable"),
        ),
    )

    project = await use_case.execute(_make_bill())

    assert project.estimated_system_kwp == pytest.approx(450.0 / _FALLBACK)


@pytest.mark.asyncio
async def test_raises_simulation_error_when_consumption_is_none() -> None:
    use_case = _make_use_case()

    with pytest.raises(SimulationError, match="Monthly consumption is required"):
        await use_case.execute(_make_bill(monthly_consumption_kwh=None))


@pytest.mark.asyncio
async def test_raises_simulation_error_when_consumption_is_zero() -> None:
    use_case = _make_use_case()

    with pytest.raises(SimulationError, match="Monthly consumption is required"):
        await use_case.execute(_make_bill(monthly_consumption_kwh=0.0))
