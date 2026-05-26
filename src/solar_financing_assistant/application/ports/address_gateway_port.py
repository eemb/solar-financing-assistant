from abc import ABC, abstractmethod

from solar_financing_assistant.application.dtos.address_dto import AddressDTO


class AddressGatewayPort(ABC):
    @abstractmethod
    def get_address_by_zipcode(self, zipcode: str) -> AddressDTO:
        pass
