"""MidiData → ScoreEvent list → LilyPond .ly content."""

import sys
from collections.abc import Iterator
from dataclasses import replace
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
    Tie,
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
    """MIDI velocity 値をアーティキュレーション記号に変換する。

    Args:
        velocity: MIDI ノートオンの velocity（0–127）。

    Returns:
        127 → ACCENT、1–30 → GHOST、それ以外 → NORMAL。
    """
    if velocity == 127:
        return Articulation.ACCENT
    if 1 <= velocity <= 30:
        return Articulation.GHOST
    return Articulation.NORMAL


# ---------------------------------------------------------------------------
# Event grouping & bar-line helpers
# ---------------------------------------------------------------------------

def _group_by_tick(events: list[MidiNoteEvent]) -> GroupedEvents:
    """MIDI イベントリストを tick_start でグループ化する。

    同じ tick に複数のイベントがある場合（和音・奏法マーカー混在）は
    同一グループにまとめられる。

    Args:
        events: 処理対象の MidiNoteEvent リスト。

    Returns:
        GroupedEvents。groups は tick → イベントリストの辞書、
        sorted_ticks は tick の昇順リスト（重複なし）。
    """
    groups: dict[int, list[MidiNoteEvent]] = {}
    for event in events:
        groups.setdefault(event.tick_start, []).append(event)
    return GroupedEvents(groups=groups, sorted_ticks=sorted(groups))


def _split_markers(group: list[MidiNoteEvent]) -> MarkerSplit:
    """同一 tick のグループから奏法マーカーノートと実音ノートを分離する。

    MIDI ノート番号 0（Apex）・1（Slap）を奏法マーカーとして扱い、
    残りを実音ノートとして返す。

    Args:
        group: 同一 tick_start を持つ MidiNoteEvent のリスト。

    Returns:
        MarkerSplit。technique は検出された奏法（なければ NORMAL）、
        real_notes はマーカーを除いた実音ノートのリスト。
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

    拍子変化が複数ある場合は、各変化が適用される tick 以降に新しい
    小節長を使用する。

    Args:
        time_sig_changes: 時系列順に並んだ拍子変化イベントのリスト。
        ticks_per_beat: MIDI ファイルの ticks_per_beat（PPQ）。

    Yields:
        小節先頭の tick（0, bar_len, 2*bar_len, ...）を昇順に無限生成する。
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


# ---------------------------------------------------------------------------
# Duration validation
# ---------------------------------------------------------------------------

def _validate_min_duration(min_duration: DurationStr) -> None:
    """min_duration が有効な音価文字列かを検証する。

    Args:
        min_duration: 検証する音価文字列（例: "16", "32"）。

    Raises:
        SystemExit: 未知の音価文字列が渡された場合。
    """
    if min_duration not in DUR_TO_BEATS:
        print(f"[ERROR] Unknown min-duration: {min_duration!r}", file=sys.stderr)
        sys.exit(1)


def _check_duration(note: int, tick: int, beats: float, min_beats: float) -> bool:
    """ノートの音価が最小値以上かを検証する。

    Args:
        note: MIDI ノート番号（警告メッセージ用）。
        tick: ノートの tick_start（警告メッセージ用）。
        beats: ノートの実際の音価（拍数）。
        min_beats: 許容する最小音価（拍数）。

    Returns:
        音価が min_beats 以上なら True、短すぎる場合は False。
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
    """1つの MIDI イベントを ToneFieldNote に変換する。

    正規化 → TF 検索 → 音価検証の順に処理し、いずれかの条件で
    スキップ対象と判断された場合は None を返す。

    Args:
        event: 処理対象の MidiNoteEvent。
        tick_start: イベントが発生した tick（警告メッセージ用）。
        ticks_per_beat: MIDI ファイルの ticks_per_beat（PPQ）。
        min_beats: この拍数より短いノートをスキップする閾値。
        priority: TF 検索に使う優先度リスト（set_priority の出力）。
        norm_info: ナチュラルマイナー正規化情報（build_norm_info の出力）。
        normalize_minor: True の場合、ハーモニック/メロディックマイナーの
            上昇6度・7度をナチュラルマイナーへ写像する。
        warn_label: スキップ警告メッセージに表示するスケール/セット名。
        technique: この tick に適用する奏法（Apex / Slap / NORMAL）。

    Returns:
        変換結果の ToneFieldNote。スキップ対象の場合は None。
    """
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
# Chord emission helpers
# ---------------------------------------------------------------------------

def _emit_chord(
    part_events: list[list[ScoreEvent]],
    tonefields_per_part: list[list[ToneFieldNote]],
    n_parts: int,
    chord_dur_str: DurationStr,
) -> None:
    """全パートに Chord または非表示 Rest を追加する。

    音符が存在するパートには Chord を、存在しないパートには Rest(hidden=True) を追加する。

    Args:
        part_events: パートごとの ScoreEvent リスト（破壊的に変更される）。
        tonefields_per_part: パートごとの ToneFieldNote リスト。
        n_parts: パート数。
        chord_dur_str: 全音符に適用する共通音価文字列。
    """
    for part_index in range(n_parts):
        tonefields = tonefields_per_part[part_index]
        if not tonefields:
            part_events[part_index].append(Rest(duration=chord_dur_str, hidden=True))
        else:
            part_events[part_index].append(Chord(notes=tonefields, duration=chord_dur_str))


def _emit_cross_bar_chord(
    part_events: list[list[ScoreEvent]],
    tonefields_per_part: list[list[ToneFieldNote]],
    n_parts: int,
    dur_str_1: DurationStr,
    dur_str_2: DurationStr,
    generator: Iterator[int],
) -> int:
    """小節またぎ和音をタイで分割して全パートに挿入し、更新後の next_tick を返す。

    Part1（小節前）に Tie を付加し、tied=True の BarLine を挟んで
    Part2（小節後、アーティキュレーション NORMAL）を追加する。
    音符が存在しないパートには各部に Rest(hidden=True) を挿入して全パートの位置を揃える。

    Args:
        part_events: パートごとの ScoreEvent リスト（破壊的に変更される）。
        tonefields_per_part: パートごとの ToneFieldNote リスト。
        n_parts: パート数。
        dur_str_1: 小節前（Part1）の音価文字列。
        dur_str_2: 小節後（Part2）の音価文字列。
        generator: 小節境界 tick を生成するジェネレータ。next() を1回消費する。

    Returns:
        更新後の next_tick（BarLine 挿入後に generator から取得した次の小節境界）。
    """
    # Part1: 小節前の音符を dur_str_1 で emit し、音符があるパートに Tie を追加する。
    part_1: list[list[ToneFieldNote]] = []
    for notes in tonefields_per_part:
        part_1.append([replace(n, duration=dur_str_1) for n in notes])
    _emit_chord(part_events, part_1, n_parts, dur_str_1)
    for part_index, tonefields in enumerate(tonefields_per_part):
        if tonefields:
            part_events[part_index].append(Tie())

    # 全パートに tied=True の BarLine を追加し、小節境界を進める。
    for part_event_list in part_events:
        part_event_list.append(BarLine(tied=True))
    next_tick = next(generator)

    # Part2: 小節後の音符を dur_str_2・Articulation.NORMAL で emit する。
    part_2: list[list[ToneFieldNote]] = []
    for notes in tonefields_per_part:
        part_2.append([replace(n, articulation=Articulation.NORMAL, duration=dur_str_2) for n in notes])
    _emit_chord(part_events, part_2, n_parts, dur_str_2)

    return next_tick


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def events_to_tokens(
    midi_data: MidiData,
    scale: HandpanScale,
    min_duration: DurationStr = "32",
    normalize_minor: bool = False,
) -> list[ScoreEvent]:
    """MidiData を単スケール用の ScoreEvent リストに変換する。

    内部的に HandpanSet（1パート）を生成して events_to_tokens_per_part に委譲する。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        scale: 使用するハンドパンスケール。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。
        normalize_minor: True の場合、ハーモニックマイナー・メロディックマイナーの
            上昇した短6度・短7度をナチュラルマイナーの音へ丸める。

    Returns:
        ScoreEvent のリスト（ToneFieldNote / Chord / Rest / BarLine の混合）。
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
) -> list[list[ScoreEvent]]:
    """MidiData を HandpanSet 用のパートごとの ScoreEvent リストに変換する。

    演奏していないパートの tick には Rest(hidden=True) を挿入して
    全パートのタイミングを揃える。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        handpan_set: 使用するハンドパンセット（複数台構成）。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。
        normalize_minor: True の場合、各パートのルートを基準に
            ハーモニックマイナー・メロディックマイナーの音をナチュラルマイナーへ丸める。

    Returns:
        パートごとの ScoreEvent リスト。インデックスは handpan_set.parts の順に対応。
    """
    _validate_min_duration(min_duration)

    # --- 事前準備 ---
    # MIDI ノート番号 → TF 番号への解決に使う優先度リストと正規化情報を構築する。
    # これらはスケール定義から決まる静的な情報なのでループ外で一度だけ計算する。
    warn_label = handpan_set.name
    priority = set_priority(handpan_set)
    norm_info = build_norm_info(handpan_set, priority)
    min_beats = DUR_TO_BEATS[min_duration]
    ticks_per_beat = midi_data.ticks_per_beat
    n_parts = len(handpan_set.parts)

    # 同時発音ノートを tick でグループ化し、小節境界ジェネレータを初期化する。
    groups, sorted_ticks = _group_by_tick(midi_data.events)
    generator = _bar_ticks(midi_data.time_sig_changes, ticks_per_beat)
    next(generator)  # tick=0 はスキップ（楽譜先頭に小節線は不要）
    next_tick = next(generator)

    # パートごとの ScoreEvent リスト（インデックスは handpan_set.parts の順）
    part_events: list[list[ScoreEvent]] = [[] for _ in range(n_parts)]

    # --- メインループ: tick ごとにイベントを処理 ---
    for event_tick in sorted_ticks:

        # この tick の前に通過した小節境界ぶんの BarLine を全パートに挿入する。
        # ノート間に複数小節の無音区間がある場合は複数回挿入される。
        while event_tick >= next_tick:
            for part_event_list in part_events:
                part_event_list.append(BarLine())
            next_tick = next(generator)

        # 奏法マーカー（Apex / Slap）を分離し、実音ノートだけを取り出す。
        technique, real_notes = _split_markers(groups[event_tick])
        if not real_notes:
            continue

        # この tick の各実音ノートを ToneFieldNote に解決し、パートごとに振り分ける。
        # tonefields_per_part[i] には現在 tick でパート i に属するノートが入る。
        tonefields_per_part: list[list[ToneFieldNote]] = [[] for _ in range(n_parts)]
        chord_dur_beats = 0.0

        for event in real_notes:
            note = _resolve_event(event, event_tick, ticks_per_beat, min_beats, priority, norm_info, normalize_minor, warn_label, technique)
            if note is None:
                continue
            tonefields_per_part[note.part_index].append(note)
            # 同 tick に音価が異なる複数ノートがある場合、最長を和音の共通音価とする。
            chord_dur_beats = max(chord_dur_beats, DUR_TO_BEATS[note.duration])

        # 全ノートがスキップされた tick は何も追加しない。
        if chord_dur_beats == 0.0:
            continue
        chord_dur_str = quantize(chord_dur_beats)

        # 小節またぎチェック: chord の終端が次の小節境界を超える場合はタイで分割する。
        chord_end_tick = event_tick + round(DUR_TO_BEATS[chord_dur_str] * ticks_per_beat)

        if chord_end_tick <= next_tick: # 通常の処理
            _emit_chord(part_events, tonefields_per_part, n_parts, chord_dur_str)
            continue

        #タイの処理
        dur_str_1 = quantize((next_tick - event_tick) / ticks_per_beat)
        dur_str_2 = quantize((chord_end_tick - next_tick) / ticks_per_beat)
        next_tick = _emit_cross_bar_chord(
            part_events, tonefields_per_part, n_parts, dur_str_1, dur_str_2, generator
        )

    return part_events
