from uuid import UUID

from solar_financing_assistant.domain.entities import Address, Customer


class TestCustomer:
    def test_creation_without_address(self):
        customer = Customer(
            name="João Silva",
            document="123.456.789-00",
            email="joao@email.com",
            phone="11999990000",
        )

        assert customer.name == "João Silva"
        assert customer.address is None
        assert isinstance(customer.id, UUID)

    def test_creation_with_address(self):
        addr = Address(
            street="Rua X",
            number="10",
            neighborhood="Centro",
            city="SP",
            state="SP",
            zip_code="01000-000",
        )
        customer = Customer(
            name="Maria",
            document="987.654.321-00",
            email="maria@email.com",
            phone="11888880000",
            address=addr,
        )

        assert customer.address is not None
        assert customer.address.city == "SP"

    def test_each_instance_has_unique_id(self):
        c1 = Customer(name="A", document="1", email="a@a.com", phone="1")
        c2 = Customer(name="B", document="2", email="b@b.com", phone="2")

        assert c1.id != c2.id
