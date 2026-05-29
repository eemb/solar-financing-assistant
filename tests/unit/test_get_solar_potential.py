"""Unit tests for GetSolarPotentialUseCase."""

import pytest

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
from solar_financing_assistant.application.ports.solar_potential_gateway_port import (
    SolarPotentialGatewayPort,
)
from solar_financing_assistant.application.use_cases.get_solar_potential import (
    GetSolarPotentialUseCase,
)
from solar_financing_assistant.domain.exceptions import SimulationError


class FakeSolarPotentialGateway(SolarPotentialGatewayPort):
    async def get_solar_potential(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        return SolarPotentialDTO(
            latitude=latitude,
            longitude=longitude,
            average_shortwave_radiation=250.50,
            estimated_daily_generation_kwh_per_kwp=2.25,
        )


@pytest.fixture()
def use_case() -> GetSolarPotentialUseCase:
    return GetSolarPotentialUseCase(solar_potential_gateway=FakeSolarPotentialGateway())


async def test_returns_solar_potential_dto(use_case: GetSolarPotentialUseCase) -> None:
    result = await use_case.execute(latitude=-8.0476, longitude=-34.877)

    assert isinstance(result, SolarPotentialDTO)
    assert result.latitude == -8.0476
    assert result.longitude == -34.877
    assert result.average_shortwave_radiation == 250.50
    assert result.estimated_daily_generation_kwh_per_kwp == 2.25


async def test_invalid_latitude_raises_simulation_error(
    use_case: GetSolarPotentialUseCase,
) -> None:
    with pytest.raises(SimulationError):
        await use_case.execute(latitude=91.0, longitude=0.0)


async def test_invalid_longitude_raises_simulation_error(
    use_case: GetSolarPotentialUseCase,
) -> None:
    with pytest.raises(SimulationError):
        await use_case.execute(latitude=0.0, longitude=181.0)
