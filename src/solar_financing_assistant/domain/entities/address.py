"""Address entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    street: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    number: str | None = None
    complement: str = ""
    latitude: float | None = None
    longitude: float | None = None

    def full_display(self) -> str:
        street_part = f"{self.street}, {self.number}" if self.number else self.street
        parts = [street_part]
        if self.complement:
            parts.append(self.complement)
        parts.append(f"{self.neighborhood} - {self.city}/{self.state}")
        parts.append(self.zip_code)
        return ", ".join(parts)
