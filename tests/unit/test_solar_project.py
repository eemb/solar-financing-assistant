from decimal import Decimal

from solar_financing_assistant.domain.entities import SolarProject


class TestSolarProject:
    def test_is_viable(self):
        project = SolarProject(
            monthly_consumption_kwh=450.0,
            estimated_system_kwp=3.8,
            estimated_monthly_generation_kwh=460.0,
            estimated_project_cost=Decimal("22000.00"),
        )
        assert project.is_viable() is True

    def test_is_not_viable_zero_generation(self):
        project = SolarProject(
            monthly_consumption_kwh=450.0,
            estimated_system_kwp=3.8,
            estimated_monthly_generation_kwh=0.0,
            estimated_project_cost=Decimal("22000.00"),
        )
        assert project.is_viable() is False

    def test_is_not_viable_zero_cost(self):
        project = SolarProject(
            monthly_consumption_kwh=450.0,
            estimated_system_kwp=3.8,
            estimated_monthly_generation_kwh=460.0,
            estimated_project_cost=Decimal("0"),
        )
        assert project.is_viable() is False
