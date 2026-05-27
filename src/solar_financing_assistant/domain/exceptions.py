"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for all domain errors."""


class InvalidAddressError(DomainError):
    """Raised when an address fails validation."""


class InvalidEnergyBillError(DomainError):
    """Raised when energy bill data is inconsistent."""


class InvalidCustomerError(DomainError):
    """Raised when customer data fails validation."""


class SimulationError(DomainError):
    """Raised when a financing simulation cannot be completed."""
