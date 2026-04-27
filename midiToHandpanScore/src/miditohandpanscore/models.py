"""Data model definitions."""

from dataclasses import dataclass
from typing import TypeAlias
from .helpers import note_name_to_midi, note_name_to_scale_identifier

PositionMap: TypeAlias = dict[int, int]


def _build_position_map(ding: int, sorted_midis: list[int]) -> PositionMap:
    """Ding を基準とした位置記譜法の N 値マップを構築する。

    Ding の N 値は -1、Ding より低い音は -2, -3, ...（低いほど小さい負数）、
    Ding より高い音は 1, 2, ...（高いほど大きい正数）。

    Args:
        ding: Ding（最低音）の MIDI ノート番号。
        sorted_midis: 昇順に並んだ全スケール音の MIDI ノート番号リスト。

    Returns:
        MIDI ノート番号 → N 値の辞書。
    """
    ding_pos = sorted_midis.index(ding)
    position_map: PositionMap = {ding: -1}
    for index, midi_note in enumerate(reversed(sorted_midis[:ding_pos])):
        position_map[midi_note] = -2 - index
    for index, midi_note in enumerate(sorted_midis[ding_pos + 1:]):
        position_map[midi_note] = 1 + index
    return position_map


def _compute_ly_pitches(midi_notes: list[int]) -> list[int]:
    """MIDI ノート番号リストから位置記譜法の N 値リストを導出する。

    Args:
        midi_notes: スケール音の MIDI ノート番号リスト（先頭が Ding）。

    Returns:
        各音の N 値リスト。インデックスは midi_notes と対応する。
    """
    ding = midi_notes[0]
    position_map = _build_position_map(ding, sorted(midi_notes))
    return [position_map[midi_note] for midi_note in midi_notes]


@dataclass(frozen=True)
class HandpanScale:
    """1台のハンドパンのスケール定義。

    Attributes:
        scale_family: スケールファミリー名（例: "Kurd", "Minor"）。
        note_names: 音名リスト（先頭が Ding、例: ["D3", "A3", "Bb3", ...]）。
        key_signature: LilyPond 調号文字列（例: "d \\minor"）。
    """
    scale_family: str
    note_names: list[str]
    key_signature: str

    @property
    def midi_notes(self) -> list[int]:
        """各音名を MIDI ノート番号に変換したリストを返す。"""
        return [note_name_to_midi(note_name) for note_name in self.note_names]

    @property
    def name(self) -> str:
        """スケールの識別名を返す（例: "D_Kurd9"）。"""
        ding_id = note_name_to_scale_identifier(self.note_names[0])
        family = self.scale_family.replace(" ", "_")
        note_count = len(self.note_names)
        return f"{ding_id}_{family}{note_count}"

    @property
    def ly_name(self) -> str:
        """LilyPond 変数名として使うスネークケース識別子を返す（例: "d_kurd9"）。"""
        return self.name.lower()

    @property
    def ly_pitches(self) -> list[int]:
        """位置記譜法の N 値リストを返す。LilyPond スケール定義ファイル生成に使用する。"""
        return _compute_ly_pitches(self.midi_notes)


@dataclass(frozen=True)
class HandpanPart:
    """HandpanSet を構成する1台分のパート定義。

    Attributes:
        instrument_name: LilyPond の \\SetTranslateTable に使う識別子。
        scale: このパートのスケール定義。
    """
    instrument_name: str
    scale: HandpanScale


@dataclass(frozen=True)
class HandpanSet:
    """複数台のハンドパンで構成されるセット定義。

    Attributes:
        scale_family: セット全体のスケールファミリー名。
        parts: 各ハンドパンのパート定義リスト。
        key_signature: LilyPond 調号文字列（例: "d \\minor"）。
    """
    scale_family: str
    parts: list[HandpanPart]
    key_signature: str

    @property
    def name(self) -> str:
        """セットの識別名を返す（例: "D_Kurd18"）。"""
        ding_name = self.parts[0].scale.note_names[0]
        total = sum(len(part.scale.note_names) for part in self.parts)
        family = self.scale_family.replace(" ", "_")
        return f"{note_name_to_scale_identifier(ding_name)}_{family}{total}"

    def part_ly_pitches(self, part_index: int) -> list[int]:
        """指定パートの位置記譜法 N 値リストをセット全体のスケールを基準に返す。

        全パートの音をまとめたスケールを基準とするため、単スケールの ly_pitches とは
        異なる値になる場合がある。

        Args:
            part_index: 対象パートのインデックス（self.parts の順）。

        Returns:
            指定パートの各音の N 値リスト。
        """
        all_midi_set: set[int] = set()
        for part in self.parts:
            all_midi_set.update(part.scale.midi_notes)
        all_midis = sorted(all_midi_set)
        ding = self.parts[0].scale.midi_notes[0]
        position_map = _build_position_map(ding, all_midis)
        return [position_map[midi_note] for midi_note in self.parts[part_index].scale.midi_notes]


@dataclass(frozen=True)
class MidiNoteEvent:
    """1つの MIDI ノートイベント（ノートオン〜ノートオフ）。

    Attributes:
        midi_note: MIDI ノート番号（0–127）。
        tick_start: ノートオンの絶対 tick。
        tick_end: ノートオフの絶対 tick。
        velocity: ノートオンの velocity（0–127）。
    """
    midi_note: int
    tick_start: int
    tick_end: int
    velocity: int
