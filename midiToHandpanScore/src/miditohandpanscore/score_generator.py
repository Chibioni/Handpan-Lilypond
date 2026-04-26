"""MidiData → ScoreEvent list → LilyPond .ly content."""

import sys
from collections.abc import Iterator
from typing import NamedTuple

from .midi_processing import MidiData, TimeSignatureChange
from .models import MidiNoteEvent, HandpanScale, HandpanPart, HandpanSet
from .quantize import DUR_TO_BEATS, DurationStr, quantize
from .score_events import (
    Articulation,
    BarLine,
    Chord,
    Rest,
    ScoreEvent,
    Technique,
    ToneFieldNote,
)
from .tf_lookup import (
    NormInfo,
    PriorityEntry,
    build_norm_info,
    find_lookup,
    normalize_midi,
    set_priority,
)

_TECHNIQUE_MIDI: dict[int, Technique] = {0: Technique.APEX, 1: Technique.SLAP}


# ---------------------------------------------------------------------------
# Named tuples
# ---------------------------------------------------------------------------

class GroupedEvents(NamedTuple):
    groups: dict[int, list[MidiNoteEvent]]
    sorted_ticks: list[int]


class MarkerSplit(NamedTuple):
    technique: Technique
    real_notes: list[MidiNoteEvent]



# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _velocity_to_articulation(velocity: int) -> Articulation:
    """velocity 値をアーティキュレーション文字に変換する。"""
    if velocity == 127:
        return Articulation.ACCENT
    if 1 <= velocity <= 30:
        return Articulation.GHOST
    return Articulation.NORMAL


# ---------------------------------------------------------------------------
# Event grouping & bar-line helpers
# ---------------------------------------------------------------------------

def _group_by_tick(events: list[MidiNoteEvent]) -> GroupedEvents:
    """イベントリストを tick_start でグループ化する。"""
    groups: dict[int, list[MidiNoteEvent]] = {}
    for event in events:
        groups.setdefault(event.tick_start, []).append(event)
    return GroupedEvents(groups=groups, sorted_ticks=sorted(groups))


def _split_markers(group: list[MidiNoteEvent]) -> MarkerSplit:
    """同一 tick のグループから奏法マーカーノートと実音ノートを分離する。"""
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
    """拍子変化に従って小節先頭ティックを順に生成するジェネレータ。"""
    time_sig_index = 0
    current_tick = 0
    while True:
        while time_sig_index + 1 < len(time_sig_changes) and time_sig_changes[time_sig_index + 1].tick <= current_tick:
            time_sig_index += 1
        time_sig = time_sig_changes[time_sig_index]
        bar_length_ticks = round(time_sig.numerator * (4 / time_sig.denominator) * ticks_per_beat)
        yield current_tick
        current_tick += bar_length_ticks


# ---------------------------------------------------------------------------
# Duration validation
# ---------------------------------------------------------------------------

def _validate_min_duration(min_duration: DurationStr) -> None:
    if min_duration not in DUR_TO_BEATS:
        print(f"[ERROR] Unknown min-duration: {min_duration!r}", file=sys.stderr)
        sys.exit(1)


def _check_duration(note: int, tick: int, beats: float, min_beats: float) -> bool:
    """音価が最小値以上かを検証する。"""
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
    if normalize_minor:
        midi = normalize_midi(event.midi_note, norm_info)
    else:
        midi = event.midi_note
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
) -> list[ScoreEvent]:
    """MidiData を単スケール用の ScoreEvent リストに変換する。"""
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
) -> list[list[ScoreEvent]]:
    """MidiData を HandpanSet 用のパートごとの ScoreEvent リストに変換する。

    他パートが演奏する tick には Rest(hidden=True) を挿入してタイミングを揃える。
    """
    _validate_min_duration(min_duration)

    warn_label = handpan_set.name
    priority = set_priority(handpan_set)
    norm_info = build_norm_info(handpan_set, priority)
    min_beats = DUR_TO_BEATS[min_duration]
    ticks_per_beat = midi_data.ticks_per_beat
    n_parts = len(handpan_set.parts)

    groups, sorted_ticks = _group_by_tick(midi_data.events)
    generator = _bar_ticks(midi_data.time_sig_changes, ticks_per_beat)
    next(generator)  # tick=0 はスキップ（楽譜先頭に小節線は不要）
    next_tick = next(generator)

    part_events: list[list[ScoreEvent]] = [[] for _ in range(n_parts)]

    for event_tick in sorted_ticks:
        while event_tick >= next_tick:
            for part_event_list in part_events:
                part_event_list.append(BarLine())
            next_tick = next(generator)

        technique, real_notes = _split_markers(groups[event_tick])
        if not real_notes:
            continue

        part_resolved: list[list[ToneFieldNote]] = [[] for _ in range(n_parts)]
        chord_dur_beats = 0.0

        for event in real_notes:
            note = _resolve_event(event, event_tick, ticks_per_beat, min_beats, priority, norm_info, normalize_minor, warn_label, technique)
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
                part_events[part_index].append(Rest(duration=chord_dur_str, hidden=True))
            else:
                part_events[part_index].append(Chord(notes=resolved, duration=chord_dur_str))

    return part_events
