"""MidiData → Handpan notation tokens → LilyPond .ly content."""

import sys
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, TypeAlias

from .midi_processing import MidiData, TimeSignatureChange
from .models import MidiNoteEvent, HandpanScale, HandpanPart, HandpanSet
from .quantize import DUR_TO_BEATS, DurationStr, quantize
from .tf_lookup import (
    NormInfo,
    PriorityEntry,
    find_lookup,
    normalize_midi,
    scale_priority,
    set_priority,
)

# ---------------------------------------------------------------------------
# Domain type aliases
# ---------------------------------------------------------------------------

Token: TypeAlias = str


class Articulation(Enum):
    NORMAL = ""
    ACCENT = "!"
    GHOST  = "."


class Technique(Enum):
    NORMAL = ""
    APEX   = "O"
    SLAP   = "S"


_TECHNIQUE_MIDI: dict[int, Technique] = {0: Technique.APEX, 1: Technique.SLAP}


@dataclass
class ToneFieldNote:
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


# ---------------------------------------------------------------------------
# Named tuples
# ---------------------------------------------------------------------------

class GroupedEvents(NamedTuple):
    groups: dict[int, list[MidiNoteEvent]]
    sorted_ticks: list[int]


class MarkerSplit(NamedTuple):
    technique: Technique
    real_notes: list[MidiNoteEvent]


class BarGenState(NamedTuple):
    generator: Iterator[int]
    next_tick: int


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _velocity_to_articulation(velocity: int) -> Articulation:
    """velocity 値をアーティキュレーション文字に変換する。

    Args:
        velocity: MIDI ノートオンの velocity（1–127）。

    Returns:
        "!" （アクセント）、"." （ゴーストノート）、または "" （通常）。
    """
    if velocity == 127:
        return Articulation.ACCENT
    if 1 <= velocity <= 30:
        return Articulation.GHOST
    return Articulation.NORMAL


def _chord_token(note_tokens: list[Token]) -> Token:
    """単音トークンのリストから和音トークンを組み立てる。

    Args:
        note_tokens: 単音トークンのリスト（ToneFieldNote.to_token() の出力）。

    Returns:
        単音トークン（要素が 1 つの場合）または和音トークン（例: "< 1-4 3-4 >"）。
    """
    if len(note_tokens) == 1:
        return note_tokens[0]
    return f"< {' '.join(note_tokens)} >"


# ---------------------------------------------------------------------------
# Event grouping & bar-line helpers
# ---------------------------------------------------------------------------

def _group_by_tick(events: list[MidiNoteEvent]) -> GroupedEvents:
    """イベントリストを tick_start でグループ化する。

    Args:
        events: MidiNoteEvent のリスト。

    Returns:
        GroupedEvents(groups, sorted_ticks)。
        groups: tick_start → MidiNoteEvent リストの辞書。
        sorted_ticks: tick_start の昇順リスト。
    """
    groups: dict[int, list[MidiNoteEvent]] = {}
    for event in events:
        groups.setdefault(event.tick_start, []).append(event)
    return GroupedEvents(groups=groups, sorted_ticks=sorted(groups))


def _split_markers(group: list[MidiNoteEvent]) -> MarkerSplit:
    """同一 tick のグループから奏法マーカーノートと実音ノートを分離する。

    Args:
        group: 同一 tick_start を持つ MidiNoteEvent のリスト。

    Returns:
        MarkerSplit(technique, real_notes)。
        technique: 奏法プレフィックス（"O"、"S"、または ""）。
        real_notes: マーカーを除いた実音ノートのリスト。
    """
    technique: Technique = Technique.NORMAL
    real_notes: list[MidiNoteEvent] = []
    for event in group:
        if event.midi_note in _TECHNIQUE_MIDI:
            technique = _TECHNIQUE_MIDI[event.midi_note]
        else:
            real_notes.append(event)
    return MarkerSplit(technique=technique, real_notes=real_notes)


def _bar_ticks(
    time_sig_changes: list[TimeSignatureChange],
    ticks_per_beat: int,
) -> Iterator[int]:
    """拍子変化に従って小節先頭ティックを順に生成するジェネレータ。

    Args:
        time_sig_changes: 拍子変化イベントのリスト。
        ticks_per_beat: MIDI ファイルの ticks_per_beat。

    Yields:
        各小節の先頭ティック（0, bar_len, 2*bar_len, ...）。
    """
    time_sig_index = 0
    current_tick = 0
    while True:
        while time_sig_index + 1 < len(time_sig_changes) and time_sig_changes[time_sig_index + 1].tick <= current_tick:
            time_sig_index += 1
        time_sig = time_sig_changes[time_sig_index]
        bar_length_ticks = round(time_sig.numerator * (4 / time_sig.denominator) * ticks_per_beat)
        yield current_tick
        current_tick += bar_length_ticks


def _init_bar_gen(
    time_sig_changes: list[TimeSignatureChange],
    ticks_per_beat: int,
) -> BarGenState:
    """小節境界ジェネレータを初期化し、最初の小節境界ティックを返す。

    tick=0 はスキップする（楽譜先頭に小節線は不要）。

    Args:
        time_sig_changes: 拍子変化イベントのリスト。
        ticks_per_beat: MIDI ファイルの ticks_per_beat。

    Returns:
        BarGenState(generator, next_tick)。
    """
    generator = _bar_ticks(time_sig_changes, ticks_per_beat)
    next(generator)  # skip tick 0 — 先頭に小節線不要
    return BarGenState(generator=generator, next_tick=next(generator))


# ---------------------------------------------------------------------------
# Duration validation
# ---------------------------------------------------------------------------

def _validate_min_duration(min_duration: DurationStr) -> None:
    if min_duration not in DUR_TO_BEATS:
        print(f"[ERROR] Unknown min-duration: {min_duration!r}", file=sys.stderr)
        sys.exit(1)


def _check_duration(note: int, tick: int, beats: float, min_beats: float) -> bool:
    """音価が最小値以上かを検証する。

    Args:
        note: MIDI ノート番号（警告メッセージ用）。
        tick: ノートの tick_start（警告メッセージ用）。
        beats: ノートの実際の音価（拍数）。
        min_beats: 許容する最小音価（拍数）。

    Returns:
        音価が最小値以上なら True、短すぎる場合は False。
    """
    if beats < min_beats:
        print(
            f"[WARN] Skipped MIDI note {note} at tick {tick}: "
            f"duration too short ({beats:.2f} beats)",
            file=sys.stderr,
        )
        return False
    return True


def _resolve_event(
    event: MidiNoteEvent,
    tick_start: int,
    ticks_per_beat: float,
    min_beats: float,
    priority: list[PriorityEntry],
    norm_info: NormInfo,
    normalize_minor: bool,
    warn_label: str,
    technique: Technique,
) -> ToneFieldNote | None:
    """1つの MIDI イベントを正規化 → TF 検索 → 音価検証 → ToneFieldNote に変換する。
    スキップ対象は None を返す。"""
    midi = normalize_midi(event.midi_note, norm_info) if normalize_minor else event.midi_note
    lookup = find_lookup(midi, priority)
    if lookup is None:
        print(f"[WARN] Skipped MIDI note {event.midi_note} at tick {tick_start}: not in {warn_label}", file=sys.stderr)
        return None
    beats = (event.tick_end - event.tick_start) / ticks_per_beat
    if not _check_duration(event.midi_note, tick_start, beats, min_beats):
        return None
    return ToneFieldNote(
        part_index=lookup.part_index,
        number=lookup.tone_field_number,
        harmonic=lookup.harmonic,
        articulation=_velocity_to_articulation(event.velocity),
        technique=technique,
        duration=quantize(beats),
    )


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def events_to_tokens(
    midi_data: MidiData,
    scale: HandpanScale,
    min_duration: DurationStr = "32",
    normalize_minor: bool = False,
) -> list[Token]:
    """MidiData を単スケール用のハンドパン記法トークンリストに変換する。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        scale: 使用するハンドパンスケール。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。
        normalize_minor: True の場合、ハーモニックマイナー・メロディックマイナーの
            上昇した短6度・短7度をナチュラルマイナーの音へ丸める。

    Returns:
        ハンドパン記法トークンのリスト（例: ["1-4", "|", "< 2-8 3-8 >"]）。
    """
    set_ = HandpanSet(
        scale_family=scale.scale_family,
        parts=[HandpanPart(instrument_name=scale.ly_name, scale=scale)],
        key_signature=scale.key_signature,
    )
    return events_to_tokens_per_part(midi_data, set_, min_duration, normalize_minor)[0]


def events_to_tokens_per_part(
    midi_data: MidiData,
    handpan_set: HandpanSet,
    min_duration: DurationStr = "32",
    normalize_minor: bool = False,
) -> list[list[Token]]:
    """MidiData を HandpanSet 用のパートごとのトークンリストに変換する。

    他パートが演奏する tick には H（非表示休符）を挿入して、パート間の
    タイミングを揃える。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        handpan_set: 使用するハンドパンセット（複数台構成）。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。
        normalize_minor: True の場合、各パートのルートを基準に
            ハーモニックマイナー・メロディックマイナーの音をナチュラルマイナーへ丸める。

    Returns:
        パートごとのトークンリスト。インデックスは handpan_set.parts の順に対応。
    """
    _validate_min_duration(min_duration)

    warn_label = handpan_set.name
    priority = set_priority(handpan_set)
    norm_info: NormInfo = [
        (part.scale.midi_notes[0], frozenset(n for tonefields, _, _ in scale_priority(part.scale) for n in tonefields))
        for part in handpan_set.parts
    ]
    min_beats = DUR_TO_BEATS[min_duration]
    ticks_per_beat = midi_data.ticks_per_beat
    n_parts = len(handpan_set.parts)

    groups, sorted_ticks = _group_by_tick(midi_data.events)
    generator, next_tick = _init_bar_gen(midi_data.time_sig_changes, ticks_per_beat)

    part_tokens: list[list[Token]] = [[] for _ in range(n_parts)]

    for tick_start in sorted_ticks:
        while tick_start >= next_tick:
            for part_token_list in part_tokens:
                part_token_list.append("|")
            next_tick = next(generator)

        technique, real_notes = _split_markers(groups[tick_start])
        if not real_notes:
            continue

        part_resolved: list[list[ToneFieldNote]] = [[] for _ in range(n_parts)]
        chord_dur_beats = 0.0

        for event in real_notes:
            note = _resolve_event(event, tick_start, ticks_per_beat, min_beats, priority, norm_info, normalize_minor, warn_label, technique)
            if note is None:
                continue
            part_resolved[note.part_index].append(note)
            chord_dur_beats = max(chord_dur_beats, DUR_TO_BEATS[note.duration])

        if chord_dur_beats == 0.0:
            continue
        chord_dur_str = quantize(chord_dur_beats)

        for part_index in range(n_parts):
            resolved = part_resolved[part_index]
            if not resolved:
                part_tokens[part_index].append(f"H-{chord_dur_str}")
            else:
                note_tokens = [n.to_token(chord_dur_str) for n in resolved]
                part_tokens[part_index].append(_chord_token(note_tokens))

    return part_tokens
