from solar_financing_assistant.application.ports.ocr_port import OCRPort
from solar_financing_assistant.application.ports.address_gateway_port import AddressGatewayPort
from solar_financing_assistant.application.ports.solar_potential_gateway_port import (
    SolarPotentialGatewayPort,
)
from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)


def test_application_ports_can_be_imported() -> None:
    assert OCRPort is not None
    assert AddressGatewayPort is not None
    assert SolarPotentialGatewayPort is not None
    assert FinancingSimulationRepositoryPort is not None
