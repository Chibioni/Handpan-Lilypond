"""MIDI file reading and parsing into MidiNoteEvent list."""

from pathlib import Path
import sys
from typing import Any, NamedTuple, cast

import mido

from .models import MidiNoteEvent


class TempoChange(NamedTuple):
    tick: int
    tempo: int  # microseconds per beat


class TimeSignatureChange(NamedTuple):
    tick: int
    numerator: int
    denominator: int


class RawEvent(NamedTuple):
    abs_tick: int
    msg: Any


class PendingNote(NamedTuple):
    tick_start: int
    velocity: int


class TrackData(NamedTuple):
    raw_events: list[RawEvent]
    tempo_changes: list[TempoChange]
    time_sig_changes: list[TimeSignatureChange]


class MidiData(NamedTuple):
    ticks_per_beat: int
    events: list[MidiNoteEvent]
    tempo_changes: list[TempoChange]
    time_sig_changes: list[TimeSignatureChange]




def _read_track(track: Any) -> TrackData:
    """トラック1本を走査して TrackData を返す。

    デルタ tick を絶対 tick に変換しながら、note_on / note_off・
    テンポ変化・拍子変化イベントを抽出する。

    Args:
        track: mido のトラックオブジェクト。

    Returns:
        TrackData（raw_events, tempo_changes, time_sig_changes）。
    """
    raw_events: list[RawEvent] = []
    tempo_changes: list[TempoChange] = []
    time_sig_changes: list[TimeSignatureChange] = []
    abs_tick = 0
    for msg in track:
        abs_tick += msg.time
        if msg.type == "set_tempo":
            tempo_changes.append(TempoChange(tick=abs_tick, tempo=msg.tempo))
        elif msg.type == "time_signature":
            time_sig_changes.append(
                TimeSignatureChange(tick=abs_tick, numerator=msg.numerator, denominator=msg.denominator)
            )
        elif msg.type in ("note_on", "note_off"):
            raw_events.append(RawEvent(abs_tick=abs_tick, msg=msg))
    return TrackData(raw_events=raw_events, tempo_changes=tempo_changes, time_sig_changes=time_sig_changes)


def _is_note_off(msg: Any) -> bool:
    return msg.type == "note_off" or msg.velocity == 0


def read_midi(path: Path) -> MidiData:
    """MIDI ファイルを読み込んで MidiData に変換する。

    音符イベント（note_on / note_off）を持つトラックを「音符トラック」とみなす。
    音符トラックが 2本以上の場合はエラーで終了する。
    テンポ・拍子情報は全トラックから収集する。
    ノートオフが来ない場合は最終イベントの tick をノートオフとして扱う。
    テンポ・拍子情報が存在しない場合はデフォルト値（120 BPM / 4/4拍子）を補完する。

    Args:
        path: 読み込む MIDI ファイルのパス。

    Returns:
        MidiData（ticks_per_beat, events, tempo_changes, time_sig_changes）。

    Raises:
        SystemExit: MIDI Format 2 のファイルや音符トラックが複数ある場合。
    """
    mid = mido.MidiFile(str(path))

    if mid.type == 2:
        print("[ERROR] MIDI Format 2 is not supported", file=sys.stderr)
        sys.exit(1)

    all_track_data = [_read_track(track) for track in cast(Any, mid).tracks]
    note_tracks = [td for td in all_track_data if td.raw_events]

    if len(note_tracks) > 1:
        print(
            f"[ERROR] {len(note_tracks)} note tracks found. "
            "Only single note-track MIDI files are supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    tempo_changes: list[TempoChange] = []
    time_sig_changes: list[TimeSignatureChange] = []
    for td in all_track_data:
        tempo_changes.extend(td.tempo_changes)
        time_sig_changes.extend(td.time_sig_changes)

    if not tempo_changes:
        tempo_changes.append(TempoChange(tick=0, tempo=500_000))
    if not time_sig_changes:
        time_sig_changes.append(TimeSignatureChange(tick=0, numerator=4, denominator=4))
    tempo_changes.sort(key=lambda tc: tc.tick)
    time_sig_changes.sort(key=lambda tsc: tsc.tick)

    raw_events: list[RawEvent] = note_tracks[0].raw_events if note_tracks else []
    if not raw_events:
        return MidiData(
            ticks_per_beat=mid.ticks_per_beat,
            events=[],
            tempo_changes=tempo_changes,
            time_sig_changes=time_sig_changes,
        )

    # note_off (or note_on vel=0) before note_on at the same tick
    raw_events.sort(key=lambda event: (event.abs_tick, not _is_note_off(event.msg)))

    pending: dict[int, list[PendingNote]] = {}
    note_events: list[MidiNoteEvent] = []

    for abs_tick, msg in raw_events:
        note_number: int = msg.note
        is_off = _is_note_off(msg)

        if pending.get(note_number):
            pending_note = pending[note_number].pop(0)
            note_events.append(
                MidiNoteEvent(
                    midi_note=note_number,
                    tick_start=pending_note.tick_start,
                    tick_end=abs_tick,
                    velocity=pending_note.velocity,
                )
            )
        if not is_off:
            pending.setdefault(note_number, []).append(PendingNote(tick_start=abs_tick, velocity=msg.velocity))

    last_tick = raw_events[-1].abs_tick
    for note_number, stack in pending.items():
        for pending_note in stack:
            note_events.append(
                MidiNoteEvent(
                    midi_note=note_number,
                    tick_start=pending_note.tick_start,
                    tick_end=last_tick,
                    velocity=pending_note.velocity,
                )
            )

    note_events.sort(key=lambda event: (event.tick_start, event.midi_note))

    return MidiData(
        ticks_per_beat=mid.ticks_per_beat,
        events=note_events,
        tempo_changes=tempo_changes,
        time_sig_changes=time_sig_changes,
    )
