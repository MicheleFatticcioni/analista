"""Structured outputs for the crew's tasks."""

from pydantic import BaseModel, Field, field_validator


class CoreMechanic(BaseModel):
    name: str = Field(description="Short name of the mechanic")
    description: str = Field(max_length=200, description="What the mechanic does, max 200 characters")
    inferred: bool = Field(
        description="False if the pitch states it; True if you interpreted it from the text"
    )


class PitchExtraction(BaseModel):
    title: str = Field(description="Game title, or 'not specified'")
    description: str = Field(max_length=200, description="One-line description of the game")
    core_mechanics: list[CoreMechanic] = Field(
        description="The mechanics and features that set this game apart"
    )
    system: str = Field(
        description="Game system (e.g. Year Zero Engine, d20 System, PbtA), or 'not specified'"
    )
    system_inferred: bool = Field(
        description="True if the pitch does not name the system and you deduced it from the text"
    )
    lore: str = Field(max_length=200, description="Setting of the game, max 200 characters")
    lang: str = Field(description="Language of the pitch as ISO 639-1 code (e.g. 'it', 'en')")


class SimilarGame(BaseModel):
    title: str = Field(description="Name of the game")
    description: str = Field(max_length=100, description="Short game summary of at most 100 characters; aim for about 80 so you never exceed the limit")
    source: str = Field(description="URL of the page the game was found on")
    publisher: str = Field(description="Publisher as named by the source page, or 'not found'")
    keyword: str = Field(description="The search keyword that led to this game")

    @field_validator("publisher")
    @classmethod
    def normalize_not_found(cls, value: str) -> str:
        return "not found" if value.strip().lower() == "not found" else value


class SimilarGamesResult(BaseModel):
    games: list[SimilarGame] = Field(
        max_length=5, description="Similar tabletop RPGs, ordered from most to least similar"
    )
    keywords_used: list[str] = Field(description="All search keywords generated and searched")
    message: str = Field(
        description="'no games found' when games is empty; otherwise why fewer than 5 were found, or 'none'"
    )
