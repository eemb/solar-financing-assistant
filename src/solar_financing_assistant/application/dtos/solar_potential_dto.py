from pydantic import BaseModel


class SolarPotentialDTO(BaseModel):
    latitude: float
    longitude: float
    estimated_daily_generation_kwh_per_kwp: float
    average_shortwave_radiation: float | None = None
