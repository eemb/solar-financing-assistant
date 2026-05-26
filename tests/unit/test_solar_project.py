from solar_financing_assistant.domain.entities import SolarProject


class TestSolarProject:
    def test_payback_years(self):
        project = SolarProject(
            system_size_kwp=5.0,
            estimated_generation_kwh_year=6000.0,
            panel_count=10,
            installation_cost_brl=30000.0,
            estimated_savings_brl_year=6000.0,
        )

        assert project.payback_years == 5.0

    def test_payback_years_with_zero_savings(self):
        project = SolarProject(
            system_size_kwp=5.0,
            estimated_generation_kwh_year=6000.0,
            panel_count=10,
            installation_cost_brl=30000.0,
            estimated_savings_brl_year=0.0,
        )

        assert project.payback_years == float("inf")

    def test_payback_years_with_negative_savings(self):
        project = SolarProject(
            system_size_kwp=5.0,
            estimated_generation_kwh_year=6000.0,
            panel_count=10,
            installation_cost_brl=30000.0,
            estimated_savings_brl_year=-100.0,
        )

        assert project.payback_years == float("inf")
