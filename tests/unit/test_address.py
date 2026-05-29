from solar_financing_assistant.domain.entities import Address


class TestAddress:
    def test_full_display_without_complement(self):
        addr = Address(
            street="Rua das Flores",
            number="123",
            neighborhood="Centro",
            city="São Paulo",
            state="SP",
            zip_code="01001-000",
        )

        assert addr.full_display() == ("Rua das Flores, 123, Centro - São Paulo/SP, 01001-000")

    def test_full_display_with_complement(self):
        addr = Address(
            street="Av Brasil",
            number="456",
            neighborhood="Jardins",
            city="Rio de Janeiro",
            state="RJ",
            zip_code="20040-020",
            complement="Apto 101",
        )

        assert addr.full_display() == (
            "Av Brasil, 456, Apto 101, Jardins - Rio de Janeiro/RJ, 20040-020"
        )

    def test_frozen_instance(self):
        addr = Address(
            street="Rua A",
            number="1",
            neighborhood="B",
            city="C",
            state="D",
            zip_code="00000-000",
        )

        try:
            addr.street = "Rua B"  # type: ignore[misc]
            raise AssertionError("Should not allow mutation")
        except Exception:
            pass
