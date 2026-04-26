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


def _select_tracks(mid: mido.MidiFile, track_index: int | None) -> list[Any]:
    """MIDI ファイルから処理対象トラックを選択する。

    track_index が None の場合は全トラックを返す。
    指定されたインデックスが範囲外の場合は [ERROR] を出力して終了する。

    Args:
        mid: 読み込み済みの mido.MidiFile オブジェクト。
        track_index: 選択するトラックの 0 始まりインデックス。None の場合は全トラック。

    Returns:
        処理対象トラックのリスト。

    Raises:
        SystemExit: track_index が範囲外の場合。
    """
    tracks: list[Any] = cast(Any, mid).tracks
    if track_index is None:
        return tracks
    if track_index >= len(tracks):
        print(
            f"[ERROR] Track {track_index} not found "
            f"(file has {len(tracks)} tracks)",
            file=sys.stderr,
        )
        sys.exit(1)
    return [tracks[track_index]]


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


def read_midi(path: Path, track_index: int | None = None) -> MidiData:
    """MIDI ファイルを読み込んで MidiData に変換する。

    複数トラックのイベントをマージし、ノートオン〜ノートオフのペアを
    MidiNoteEvent に変換する。ノートオフが来ない場合は最終イベントの
    tick をノートオフとして扱う。
    テンポ・拍子情報が存在しない場合はデフォルト値（120 BPM / 4/4拍子）を補完する。

    Args:
        path: 読み込む MIDI ファイルのパス。
        track_index: 読み込むトラックの 0 始まりインデックス。
            None の場合は全トラックをマージする。

    Returns:
        MidiData（ticks_per_beat, events, tempo_changes, time_sig_changes）。

    Raises:
        SystemExit: MIDI Format 2 のファイルや track_index が範囲外の場合。
    """
    mid = mido.MidiFile(str(path))

    if mid.type == 2:
        print("[ERROR] MIDI Format 2 is not supported", file=sys.stderr)
        sys.exit(1)

    raw_events: list[RawEvent] = []
    tempo_changes: list[TempoChange] = []
    time_sig_changes: list[TimeSignatureChange] = []

    for track in _select_tracks(mid, track_index):
        track_data = _read_track(track)
        raw_events.extend(track_data.raw_events)
        tempo_changes.extend(track_data.tempo_changes)
        time_sig_changes.extend(track_data.time_sig_changes)

    # note_off (or note_on vel=0) before note_on at the same tick
    raw_events.sort(
        key=lambda event: (
            event.abs_tick,
            0 if (event.msg.type == "note_off" or event.msg.velocity == 0) else 1,
        )
    )

    pending: dict[int, list[PendingNote]] = {}
    note_events: list[MidiNoteEvent] = []

    for abs_tick, msg in raw_events:
        note: int = msg.note
        is_off = msg.type == "note_off" or msg.velocity == 0

        if pending.get(note):
            pending_note = pending[note].pop(0)
            note_events.append(
                MidiNoteEvent(
                    midi_note=note,
                    tick_start=pending_note.tick_start,
                    tick_end=abs_tick,
                    velocity=pending_note.velocity,
                )
            )
        if not is_off:
            pending.setdefault(note, []).append(PendingNote(tick_start=abs_tick, velocity=msg.velocity))

    last_tick = raw_events[-1].abs_tick if raw_events else 0
    for note, stack in pending.items():
        for pending_note in stack:
            note_events.append(
                MidiNoteEvent(
                    midi_note=note,
                    tick_start=pending_note.tick_start,
                    tick_end=last_tick,
                    velocity=pending_note.velocity,
                )
            )

    if not tempo_changes:
        tempo_changes.append(TempoChange(tick=0, tempo=500_000))
    if not time_sig_changes:
        time_sig_changes.append(TimeSignatureChange(tick=0, numerator=4, denominator=4))

    tempo_changes.sort(key=lambda tc: tc.tick)
    time_sig_changes.sort(key=lambda tsc: tsc.tick)
    note_events.sort(key=lambda event: (event.tick_start, event.midi_note))

    return MidiData(
        ticks_per_beat=mid.ticks_per_beat,
        events=note_events,
        tempo_changes=tempo_changes,
        time_sig_changes=time_sig_changes,
    )
