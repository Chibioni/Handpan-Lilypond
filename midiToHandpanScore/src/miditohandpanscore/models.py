"""Data model definitions."""

from dataclasses import dataclass
from typing import TypeAlias
from .helpers import note_name_to_midi, note_name_to_scale_identifier

PositionMap: TypeAlias = dict[int, int]


def _build_position_map(ding: int, sorted_midis: list[int]) -> PositionMap:
    """Ding と昇順 MIDI リストから位置記譜法の N 値マップを構築する。"""
    ding_pos = sorted_midis.index(ding)
    position_map: PositionMap = {ding: -1}
    for index, midi_note in enumerate(reversed(sorted_midis[:ding_pos])):
        position_map[midi_note] = -2 - index
    for index, midi_note in enumerate(sorted_midis[ding_pos + 1:]):
        position_map[midi_note] = 1 + index
    return position_map


def _compute_ly_pitches(midi_notes: list[int]) -> list[int]:
    """MIDI ノート番号リストから位置記譜法の N 値リストを導出する。"""
    ding = midi_notes[0]
    position_map = _build_position_map(ding, sorted(midi_notes))
    return [position_map[midi_note] for midi_note in midi_notes]


@dataclass(frozen=True)
class HandpanScale:
    scale_family: str
    note_names: list[str]
    key_signature: str

    @property
    def midi_notes(self) -> list[int]:
        return [note_name_to_midi(note_name) for note_name in self.note_names]

    @property
    def name(self) -> str:
        family = self.scale_family.replace(" ", "_")
        return f"{note_name_to_scale_identifier(self.note_names[0])}_{family}{len(self.note_names)}"

    @property
    def ly_name(self) -> str:
        family_slug = self.scale_family.lower().replace(" ", "_")
        return f"{note_name_to_scale_identifier(self.note_names[0]).lower()}_{family_slug}{len(self.note_names)}"

    @property
    def ly_pitches(self) -> list[int]:
        return _compute_ly_pitches(self.midi_notes)


@dataclass(frozen=True)
class HandpanPart:
    instrument_name: str
    scale: HandpanScale


@dataclass(frozen=True)
class HandpanSet:
    scale_family: str
    parts: list[HandpanPart]
    key_signature: str

    @property
    def name(self) -> str:
        ding_name = self.parts[0].scale.note_names[0]
        total = sum(len(part.scale.note_names) for part in self.parts)
        family = self.scale_family.replace(" ", "_")
        return f"{note_name_to_scale_identifier(ding_name)}_{family}{total}"

    def part_ly_pitches(self, part_index: int) -> list[int]:
        all_midis = sorted(set(midi_note for part in self.parts for midi_note in part.scale.midi_notes))
        ding = self.parts[0].scale.midi_notes[0]
        position_map = _build_position_map(ding, all_midis)
        return [position_map[midi_note] for midi_note in self.parts[part_index].scale.midi_notes]


@dataclass(frozen=True)
class MidiNoteEvent:
    midi_note: int
    tick_start: int
    tick_end: int
    velocity: int
