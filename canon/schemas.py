"""Dataclasses: CharacterSheet, Shot, Script. The shared data shapes the pipeline passes around."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CharacterSheet:
    """A character's locked look. `descriptor` + `seed` (+ optional `ref_image`) are reused
    on every shot to hold the character consistent across shots and episodes."""

    name: str
    descriptor: str
    seed: int
    ref_image: Optional[str] = None


@dataclass
class Shot:
    """One shot in an episode. `prompt` and `clip` are filled during rendering."""

    index: int
    character: Optional[str]
    setting: str
    action: str
    dialogue: str = ""
    prompt: str = ""
    clip: Optional[str] = None


@dataclass
class Script:
    """A single episode's plan: premise, style, and its ordered shots."""

    premise: str
    style: str
    shots: List[Shot] = field(default_factory=list)
