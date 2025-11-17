from pydantic import BaseModel, Field


class BikeInfo(BaseModel):
    number: str
    distance: float
    latitude: float
    longitude: float


class ExternalBikeApiResponse(BaseModel):
    cars: list[BikeInfo]
    total: int


class KnownLocation(BaseModel):
    name: str = Field(description="Location primary name")
    aliases: list[str] = Field(
        default_factory=list, description="Other names for the location"
    )
    latitude: float
    longitude: float


class LocatorResponse(BaseModel):
    query: str = Field(description="The original query string")
    match_found: bool = Field(description="Whether a matching location was found")
    matched_name: str | None = Field(
        description="The name of the matched location, if any"
    )
    message: str = Field(
        description="A message summarizing the execution status for the LLM"
    )
    bike_data: ExternalBikeApiResponse | None = Field(
        description="The bike data retrieved from the external API, if any"
    )
