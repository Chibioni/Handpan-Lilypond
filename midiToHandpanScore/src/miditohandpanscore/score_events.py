"""Score event types: building blocks of a handpan score."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .quantize import DurationStr

Token: TypeAlias = str


class Articulation(Enum):
    NORMAL = ""
    ACCENT = "!"
    GHOST  = "."


class Technique(Enum):
    NORMAL = ""
    APEX   = "O"
    SLAP   = "S"


class ScoreEvent(ABC):
    @abstractmethod
    def to_token(self) -> Token: ...


@dataclass
class ToneFieldNote(ScoreEvent):
    part_index: int
    number: int
    harmonic: int
    articulation: Articulation
    technique: Technique
    duration: DurationStr

    def to_token(self, duration: DurationStr | None = None) -> Token:
        dur = duration if duration is not None else self.duration
        token = self.technique.value + str(self.number)
        if self.harmonic:
            token += f"^{self.harmonic}"
        return token + self.articulation.value + f"-{dur}"


@dataclass
class Chord(ScoreEvent):
    notes: list[ToneFieldNote]
    duration: DurationStr

    def to_token(self) -> Token:
        tokens = [n.to_token(self.duration) for n in self.notes]
        if len(tokens) == 1:
            return tokens[0]
        return "< " + " ".join(tokens) + " >"


@dataclass
class Rest(ScoreEvent):
    duration: DurationStr
    hidden: bool = False

    def to_token(self) -> Token:
        return f"{'H' if self.hidden else 'R'}-{self.duration}"


@dataclass
class BarLine(ScoreEvent):
    def to_token(self) -> Token:
        return "|"
