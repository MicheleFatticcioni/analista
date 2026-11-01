"""Structured outputs for the crew's tasks."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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


class SharedFeature(BaseModel):
    pitch_element: str = Field(description="Name of the matching item in the pitch extraction")
    pitch_category: Literal["core_feature", "mechanic", "lore"] = Field(
        description="List of the pitch extraction the matching item belongs to"
    )
    in_similar_game: str = Field(description="How the similar game implements it, as stated by the source")


class SimilarGame(BaseModel):
    title: str = Field(description="Name of the game")
    publisher: str = Field(
        description="Publisher as named by a source page (the creator, if self-published), or 'not specified'"
    )
    description: str = Field(max_length=200, description="Short game summary, max 200 characters")
    shared_features: list[SharedFeature] = Field(
        min_length=2,
        description="Elements in common with the pitch; at least one is a core feature or a mechanic",
    )
    source: str = Field(description="URL of the page that confirms the game and the shared features")

    @model_validator(mode="after")
    def needs_feature_or_mechanic(self) -> "SimilarGame":
        if not any(f.pitch_category != "lore" for f in self.shared_features):
            raise ValueError(
                f"'{self.title}' shares only lore with the pitch: at least one shared element "
                "must be a core feature or a mechanic"
            )
        return self


class SimilarGamesResult(BaseModel):
    games: list[SimilarGame] = Field(
        max_length=5, description="Similar tabletop RPGs, ordered from most to least similar"
    )
    queries_used: list[str] = Field(description="Search queries actually run")
    notes: str = Field(description="Why fewer than 5 games were found, or 'none'")
