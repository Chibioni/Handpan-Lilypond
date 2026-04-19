"""Data model definitions."""

from dataclasses import dataclass
from .helpers import note_name_to_midi, note_name_to_scale_identifier


def compute_ly_pitches(midi_notes: list[int]) -> list[int]:
    """MIDI ノート番号リストから位置記譜法の N 値リストを導出する。"""
    ding = midi_notes[0]
    sorted_midis = sorted(midi_notes)
    ding_pos = sorted_midis.index(ding)
    n_map: dict[int, int] = {ding: -1}
    for i, m in enumerate(reversed(sorted_midis[:ding_pos])):
        n_map[m] = -2 - i
    for i, m in enumerate(sorted_midis[ding_pos + 1:]):
        n_map[m] = 1 + i
    return [n_map[m] for m in midi_notes]


@dataclass
class HandpanScale:
    scale_family: str
    note_names: list[str]
    key_signature: str

    @property
    def midi_notes(self) -> list[int]:
        return [note_name_to_midi(n) for n in self.note_names]

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
        return compute_ly_pitches(self.midi_notes)


@dataclass
class HandpanPart:
    instrument_name: str
    scale: HandpanScale


@dataclass
class HandpanEnsemble:
    scale_family: str
    parts: list[HandpanPart]
    key_signature: str

    @property
    def name(self) -> str:
        ding_name = self.parts[0].scale.note_names[0]
        total = sum(len(p.scale.note_names) for p in self.parts)
        family = self.scale_family.replace(" ", "_")
        return f"{note_name_to_scale_identifier(ding_name)}_{family}{total}"

    def part_ly_pitches(self, part_index: int) -> list[int]:
        all_midis = sorted(set(m for p in self.parts for m in p.scale.midi_notes))
        ding = self.parts[0].scale.midi_notes[0]
        ding_pos = all_midis.index(ding)
        n_map: dict[int, int] = {ding: -1}
        for i, m in enumerate(reversed(all_midis[:ding_pos])):
            n_map[m] = -2 - i
        for i, m in enumerate(all_midis[ding_pos + 1:]):
            n_map[m] = 1 + i
        return [n_map[m] for m in self.parts[part_index].scale.midi_notes]


@dataclass
class MidiNoteEvent:
    midi_note: int
    tick_start: int
    tick_end: int
    velocity: int
