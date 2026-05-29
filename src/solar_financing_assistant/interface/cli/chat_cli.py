"""Terminal CLI for the solar financing assistant journey."""

import asyncio
import logging
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from uuid import UUID

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.dtos.solar_project_estimate_input_dto import (
    SolarProjectEstimateInputDTO,
)
from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
)
from solar_financing_assistant.application.use_cases.create_financing_simulation import (
    CreateFinancingSimulationUseCase,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project import (
    EstimateSolarProjectUseCase,
)
from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer
from solar_financing_assistant.domain.entities.financing_simulation import (
    FinancingSimulation,
)
from solar_financing_assistant.domain.exceptions import (
    InvalidEnergyBillError,
    SimulationError,
)

logger = logging.getLogger(__name__)


class ChatCLI:
    def __init__(
        self,
        extract_energy_bill: ExtractEnergyBillDataUseCase,
        create_simulation: CreateFinancingSimulationUseCase,
        check_status: CheckSimulationStatusUseCase,
        estimate_solar_project: EstimateSolarProjectUseCase,
        generation_per_kwp_month: float,
        cost_per_kwp_brl: Decimal,
        monthly_rate: Decimal,
    ) -> None:
        self._extract_energy_bill = extract_energy_bill
        self._create_simulation = create_simulation
        self._check_status = check_status
        self._estimate_solar_project = estimate_solar_project
        self.generation_per_kwp_month = generation_per_kwp_month
        self.cost_per_kwp_brl = cost_per_kwp_brl
        self.monthly_rate = monthly_rate

    def run(self) -> None:
        print("Solar Financing Assistant")
        print()

        while True:
            self._print_menu()
            choice = input("Escolha uma opção: ").strip()

            if choice == "0":
                print("Até logo!")
                break
            if choice == "1":
                self._simulate_financing()
            elif choice == "2":
                self._consult_status()
            else:
                print("Opção inválida. Tente novamente.")
            print()

    def _print_menu(self) -> None:
        print("--- Menu ---")
        print("1 - Simular financiamento")
        print("2 - Consultar status")
        print("0 - Sair")

    def _simulate_financing(self) -> None:
        file_path_str = input("Caminho da conta de energia: ").strip()
        if not file_path_str:
            print("Caminho não informado.")
            return

        file_path = Path(file_path_str)

        try:
            bill_data = asyncio.run(self._extract_energy_bill.execute(file_path))
        except InvalidEnergyBillError as exc:
            print(f"Erro na conta de energia: {exc}")
            return

        self._print_extracted_bill_data(bill_data)

        try:
            solar_project = self._estimate_solar_project.execute(
                SolarProjectEstimateInputDTO(
                    monthly_consumption_kwh=bill_data.monthly_consumption_kwh,
                    generation_per_kwp_month=self.generation_per_kwp_month,
                    cost_per_kwp_brl=self.cost_per_kwp_brl,
                )
            )
        except SimulationError as exc:
            print(f"Erro na estimativa do projeto solar: {exc}")
            return

        self._print_solar_project_info(solar_project)

        confirmation = input("Confirma a simulação de financiamento? (s/n): ").strip().lower()
        if confirmation != "s":
            print("Simulação cancelada.")
            return

        try:
            simulation = self._create_simulation.execute(
                solar_project,
                monthly_rate=self.monthly_rate,
            )
        except SimulationError as exc:
            print(f"Erro na simulação: {exc}")
            return

        self._print_simulation_result(simulation)

    def _consult_status(self) -> None:
        id_str = input("ID da simulação (UUID): ").strip()
        if not id_str:
            print("ID não informado.")
            return

        try:
            sim_uuid = UUID(id_str)
        except ValueError:
            print("ID inválido. Informe um UUID válido (ex: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx).")
            return

        try:
            simulation = self._check_status.execute(sim_uuid)
        except SimulationError as exc:
            print(f"Erro: {exc}")
            return

        print(f"Status: {simulation.status.value}")
        offer = simulation.get_best_offer()
        if offer is not None:
            self._print_offer(offer)
        else:
            print("Nenhuma oferta disponível.")

    @staticmethod
    def _print_extracted_bill_data(data: ExtractedEnergyBillDataDTO) -> None:
        print()
        print("--- Dados extraídos da conta ---")
        print(f"Cliente: {data.customer_name}")
        print(f"CPF: {data.cpf}")
        print(f"CEP: {data.zipcode}")
        print(f"Distribuidora: {data.distributor}")
        print(f"Consumo mensal (kWh): {data.monthly_consumption_kwh}")
        print(f"Custo mensal (R$): {_format_brl(data.monthly_cost_brl)}")
        print(f"Tarifa (R$/kWh): {_format_brl(data.tariff_brl_per_kwh)}")
        print(f"Mês de referência: {data.reference_month}")
        print()

    @staticmethod
    def _print_solar_project_info(project) -> None:  # type: ignore[no-untyped-def]
        print("--- Projeto solar estimado ---")
        print(f"Consumo mensal (kWh): {project.monthly_consumption_kwh}")
        print(f"Sistema estimado (kWp): {project.estimated_system_kwp:.2f}")
        print(f"Geração mensal estimada (kWh): {project.estimated_monthly_generation_kwh:.2f}")
        print(f"Custo estimado do projeto (R$): {_format_brl(project.estimated_project_cost)}")
        print()

    def _print_simulation_result(self, simulation: FinancingSimulation) -> None:
        print()
        print("--- Resultado da simulação ---")
        print(f"Referência: {simulation.simulation_id}")
        print(f"ID para consulta: {simulation.id}")
        print(f"Status: {simulation.status.value}")
        offer = simulation.get_best_offer()
        if offer is not None:
            self._print_offer(offer)

    @staticmethod
    def _print_offer(offer: FinancingOffer) -> None:
        print(f"Valor aprovado (R$): {_format_brl(offer.approved_amount)}")
        print(f"Parcela (R$): {_format_brl(offer.installment_amount)}")
        print(f"Quantidade de parcelas: {offer.number_of_installments}")
        print(f"Taxa mensal: {offer.monthly_rate}")


def _format_brl(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
