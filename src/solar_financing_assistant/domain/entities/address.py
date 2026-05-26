"""Address entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    street: str
    number: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    complement: str = ""
    latitude: float | None = None
    longitude: float | None = None

    def full_display(self) -> str:
        parts = [f"{self.street}, {self.number}"]
        if self.complement:
            parts.append(self.complement)
        parts.append(f"{self.neighborhood} - {self.city}/{self.state}")
        parts.append(self.zip_code)
        return ", ".join(parts)
