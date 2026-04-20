"""MidiData → Handpan notation tokens → LilyPond .ly content."""

import sys
from collections.abc import Iterator
from typing import Literal, NamedTuple, TypeAlias

from .midi_processing import MidiData, TimeSignatureChange
from .models import MidiNoteEvent, HandpanScale, HandpanSet
from .quantize import DUR_TO_BEATS, DurationStr, quantize

# ---------------------------------------------------------------------------
# Domain type aliases
# ---------------------------------------------------------------------------

Token: TypeAlias = str
Articulation: TypeAlias = Literal["", "!", "."]
Technique: TypeAlias = Literal["", "O", "S"]

_TECHNIQUE_MIDI: dict[int, Technique] = {0: "O", 1: "S"}


# ---------------------------------------------------------------------------
# Named tuples
# ---------------------------------------------------------------------------

class HarmonicInterval(NamedTuple):
    semitones: int
    harmonic_number: int


_HARMONIC_INTERVALS: tuple[HarmonicInterval, ...] = (
    HarmonicInterval(semitones=12, harmonic_number=1),
    HarmonicInterval(semitones=19, harmonic_number=2),
)


class ScaleLookup(NamedTuple):
    tone_field_number: int
    harmonic: int


class SetLookup(NamedTuple):
    part_index: int
    tone_field_number: int
    harmonic: int


class GroupedEvents(NamedTuple):
    groups: dict[int, list[MidiNoteEvent]]
    sorted_ticks: list[int]


class MarkerSplit(NamedTuple):
    technique: Technique
    real_notes: list[MidiNoteEvent]


class BarGenState(NamedTuple):
    generator: Iterator[int]
    next_tick: int


class ResolvedNote(NamedTuple):
    tone_field_number: int
    harmonic: int
    articulation: Articulation
    duration_str: DurationStr


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
        return "!"
    if 1 <= velocity <= 30:
        return "."
    return ""


def _note_token(
    tone_field_number: int,
    harmonic: int,
    technique: Technique,
    articulation: Articulation,
    duration_str: DurationStr,
) -> Token:
    """単音のハンドパン記法トークン文字列を組み立てる。

    Args:
        tone_field_number: トーンフィールド番号（0 = Ding）。
        harmonic: ハーモニクス番号（0 = 基音、1 = ^1、2 = ^2）。
        technique: 奏法プレフィックス（"O"、"S"、または ""）。
        articulation: アーティキュレーション（"!"、"."、または ""）。
        duration_str: 音価文字列（例: "4", "8.", "16"）。

    Returns:
        ハンドパン記法トークン（例: "1-4", "O2!-8", "3^1-4."）。
    """
    token = technique + str(tone_field_number)
    if harmonic:
        token += f"^{harmonic}"
    token += articulation + f"-{duration_str}"
    return token


def _chord_token(note_tokens: list[Token]) -> Token:
    """単音トークンのリストから和音トークンを組み立てる。

    Args:
        note_tokens: 単音トークンのリスト（_note_token の出力）。

    Returns:
        単音トークン（要素が 1 つの場合）または和音トークン（例: "< 1-4 3-4 >"）。
    """
    if len(note_tokens) == 1:
        return note_tokens[0]
    return f"< {' '.join(note_tokens)} >"


def _build_scale_tables(scale: HandpanScale) -> dict[int, ScaleLookup]:
    """スケールから MIDI ノート番号の変換テーブルを構築する。

    Args:
        scale: 変換対象の HandpanScale。

    Returns:
        MIDI ノート番号 → ScaleLookup(トーンフィールド番号, ハーモニクス番号) の辞書。
        基音は harmonic=0、ハーモニクス1は harmonic=1、ハーモニクス2は harmonic=2。
    """
    midi_to_resolved: dict[int, ScaleLookup] = {}
    for tone_field_number, midi in enumerate(scale.midi_notes):
        midi_to_resolved[midi] = ScaleLookup(tone_field_number=tone_field_number, harmonic=0)
        for interval in _HARMONIC_INTERVALS:
            harmonic_midi = midi + interval.semitones
            if harmonic_midi not in midi_to_resolved:
                midi_to_resolved[harmonic_midi] = ScaleLookup(
                    tone_field_number=tone_field_number, harmonic=interval.harmonic_number
                )
    return midi_to_resolved


def _build_set_tables(handpan_set: HandpanSet) -> dict[int, SetLookup]:
    """HandpanSet から MIDI ノート番号の変換テーブルを構築する。

    Args:
        handpan_set: 変換対象の HandpanSet。

    Returns:
        MIDI ノート番号 → SetLookup(パートインデックス, トーンフィールド番号, ハーモニクス番号) の辞書。
        基音は harmonic=0、ハーモニクス1は harmonic=1、ハーモニクス2は harmonic=2。
        同じ MIDI ノートが複数パートに存在する場合は先着優先で登録し警告を出す。
    """
    midi_to_resolved: dict[int, SetLookup] = {}
    for part_index, part in enumerate(handpan_set.parts):
        for tone_field_number, midi in enumerate(part.scale.midi_notes):
            if midi in midi_to_resolved:
                first = handpan_set.parts[midi_to_resolved[midi].part_index].instrument_name
                print(
                    f"[WARN] Overlapping MIDI note {midi} in set: "
                    f"{part.instrument_name} TF{tone_field_number} shadowed by {first}",
                    file=sys.stderr,
                )
            else:
                midi_to_resolved[midi] = SetLookup(
                    part_index=part_index, tone_field_number=tone_field_number, harmonic=0
                )
            for interval in _HARMONIC_INTERVALS:
                harmonic_midi = midi + interval.semitones
                if harmonic_midi not in midi_to_resolved:
                    midi_to_resolved[harmonic_midi] = SetLookup(
                        part_index=part_index, tone_field_number=tone_field_number, harmonic=interval.harmonic_number
                    )
    return midi_to_resolved


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
    technique: Technique = ""
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


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def events_to_tokens(
    midi_data: MidiData,
    scale: HandpanScale,
    min_duration: DurationStr = "32",
    scale_label: str = "",
) -> list[Token]:
    """MidiData を単スケール用のハンドパン記法トークンリストに変換する。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        scale: 使用するハンドパンスケール。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。
        scale_label: 警告メッセージに表示するスケール名。省略時は scale.ly_name を使用。

    Returns:
        ハンドパン記法トークンのリスト（例: ["1-4", "\\|", "< 2-8 3-8 >"]）。
    """
    _validate_min_duration(min_duration)

    midi_to_resolved = _build_scale_tables(scale)
    min_beats = DUR_TO_BEATS[min_duration]
    ticks_per_beat = midi_data.ticks_per_beat
    label = scale_label or scale.ly_name

    groups, sorted_ticks = _group_by_tick(midi_data.events)
    generator, next_tick = _init_bar_gen(midi_data.time_sig_changes, ticks_per_beat)

    tokens: list[Token] = []

    for tick_start in sorted_ticks:
        while tick_start >= next_tick:
            tokens.append("\\|")
            next_tick = next(generator)

        technique, real_notes = _split_markers(groups[tick_start])
        if not real_notes:
            continue

        resolved: list[ResolvedNote] = []
        for event in real_notes:
            if event.midi_note not in midi_to_resolved:
                print(f"[WARN] Skipped MIDI note {event.midi_note} at tick {tick_start}: not in {label}", file=sys.stderr)
                continue
            beats = (event.tick_end - event.tick_start) / ticks_per_beat
            if not _check_duration(event.midi_note, tick_start, beats, min_beats):
                continue
            lookup = midi_to_resolved[event.midi_note]
            resolved.append(ResolvedNote(
                tone_field_number=lookup.tone_field_number,
                harmonic=lookup.harmonic,
                articulation=_velocity_to_articulation(event.velocity),
                duration_str=quantize(beats),
            ))

        if resolved:
            chord_dur_str = max(resolved, key=lambda r: DUR_TO_BEATS[r.duration_str]).duration_str
            note_tokens = [_note_token(r.tone_field_number, r.harmonic, technique, r.articulation, chord_dur_str) for r in resolved]
            tokens.append(_chord_token(note_tokens))

    return tokens


def events_to_tokens_per_part(
    midi_data: MidiData,
    handpan_set: HandpanSet,
    min_duration: DurationStr = "32",
) -> list[list[Token]]:
    """MidiData を HandpanSet 用のパートごとのトークンリストに変換する。

    他パートが演奏する tick には H（非表示休符）を挿入して、パート間の
    タイミングを揃える。

    Args:
        midi_data: 読み込み済みの MIDI データ。
        handpan_set: 使用するハンドパンセット（複数台構成）。
        min_duration: この音価より短いノートをスキップする（例: "16", "32"）。

    Returns:
        パートごとのトークンリスト。インデックスは handpan_set.parts の順に対応。
    """
    _validate_min_duration(min_duration)

    midi_to_resolved = _build_set_tables(handpan_set)
    min_beats = DUR_TO_BEATS[min_duration]
    ticks_per_beat = midi_data.ticks_per_beat
    n_parts = len(handpan_set.parts)

    groups, sorted_ticks = _group_by_tick(midi_data.events)
    generator, next_tick = _init_bar_gen(midi_data.time_sig_changes, ticks_per_beat)

    part_tokens: list[list[Token]] = [[] for _ in range(n_parts)]

    for tick_start in sorted_ticks:
        while tick_start >= next_tick:
            for part_token_list in part_tokens:
                part_token_list.append("\\|")
            next_tick = next(generator)

        technique, real_notes = _split_markers(groups[tick_start])
        if not real_notes:
            continue

        part_resolved: list[list[ResolvedNote]] = [[] for _ in range(n_parts)]
        chord_dur_beats = 0.0

        for event in real_notes:
            note = event.midi_note
            beats = (event.tick_end - event.tick_start) / ticks_per_beat

            if note not in midi_to_resolved:
                print(f"[WARN] Skipped MIDI note {note} at tick {tick_start}: not in set", file=sys.stderr)
                continue
            lookup = midi_to_resolved[note]

            if not _check_duration(note, tick_start, beats, min_beats):
                continue

            duration_str = quantize(beats)
            part_resolved[lookup.part_index].append(ResolvedNote(
                tone_field_number=lookup.tone_field_number,
                harmonic=lookup.harmonic,
                articulation=_velocity_to_articulation(event.velocity),
                duration_str=duration_str,
            ))
            chord_dur_beats = max(chord_dur_beats, DUR_TO_BEATS[duration_str])

        if chord_dur_beats == 0.0:
            continue
        chord_dur_str = quantize(chord_dur_beats)

        for part_index in range(n_parts):
            resolved = part_resolved[part_index]
            if not resolved:
                part_tokens[part_index].append(f"H-{chord_dur_str}")
            else:
                note_tokens = [_note_token(r.tone_field_number, r.harmonic, technique, r.articulation, chord_dur_str) for r in resolved]
                part_tokens[part_index].append(_chord_token(note_tokens))

    return part_tokens


# ---------------------------------------------------------------------------
# LilyPond output
# ---------------------------------------------------------------------------

def _split_chunks(tokens: list[Token], bars_per_chunk: int) -> list[list[Token]]:
    """トークン列を bars_per_chunk 小節ごとのチャンクに分割する。

    チャンク先頭・末尾の \\| は除外する。

    Args:
        tokens: ハンドパン記法トークンのリスト（\\| を含む）。
        bars_per_chunk: 1 チャンクあたりの小節数。

    Returns:
        チャンクのリスト。各チャンクはトークンのリスト。
    """
    chunks: list[list[Token]] = []
    current: list[Token] = []
    bar_count = 0

    for token in tokens:
        if token == "\\|":
            bar_count += 1
            if bar_count % bars_per_chunk == 0:
                if current:
                    chunks.append(current)
                current = []
            else:
                current.append(token)
        else:
            current.append(token)

    if current:
        chunks.append(current)

    return chunks


def _ly_preamble(title: str, scale_name: str, key_sig: str) -> str:
    """LilyPond ファイルのヘッダー部分を生成する。

    Args:
        title: 楽譜タイトル。
        scale_name: スケール定義ファイル名（拡張子なし）。
        key_sig: LilyPond の調号文字列（例: "d \\minor"）。

    Returns:
        LilyPond ヘッダー文字列。
    """
    return (
        '\\version "2.24.4"\n\n'
        '\\include "../Handpan.ily"\n'
        f'\\include "../Scales/{scale_name}.ly"\n\n'
        "\\score {\n"
        "  \\header {\n"
        f'    title = "{title}"\n'
        "  }\n"
        "  \\new Staff {\n"
        "    \\clef treble\n"
        f"    \\key {key_sig}\n"
    )


_LY_SUFFIX = "  }\n}\n"


def generate_score_ly(
    tokens: list[Token],
    scale: HandpanScale,
    bars_per_chunk: int = 4,
) -> str:
    """ハンドパン記法トークン列から単スケール用 LilyPond ファイル文字列を生成する。

    Args:
        tokens: ハンドパン記法トークンのリスト。
        scale: 使用するハンドパンスケール。
        bars_per_chunk: 1 行あたりの小節数。

    Returns:
        LilyPond ファイルの内容文字列。
    """
    chunks = _split_chunks(tokens, bars_per_chunk)
    score_blocks = "\n    ".join(f'\\HandpanScore "{" ".join(chunk)}"' for chunk in chunks)
    return (
        _ly_preamble(scale.name, scale.name, scale.key_signature)
        + f"    \\SetTranslateTable #{scale.ly_name}\n"
        + f"    {score_blocks}\n"
        + _LY_SUFFIX
    )


def generate_set_score_ly(
    part_tokens: list[list[Token]],
    handpan_set: HandpanSet,
    bars_per_chunk: int = 4,
) -> str:
    """ハンドパン記法トークン列から HandpanSet 用 LilyPond ファイル文字列を生成する。

    Args:
        part_tokens: パートごとのトークンリスト（events_to_tokens_per_part の出力）。
        handpan_set: 使用するハンドパンセット。
        bars_per_chunk: 1 行あたりの小節数。

    Returns:
        LilyPond ファイルの内容文字列。
    """
    n_parts = len(handpan_set.parts)
    chunks_per_part = [_split_chunks(pt, bars_per_chunk) for pt in part_tokens]
    n_chunks = max(len(chunks) for chunks in chunks_per_part)

    chunk_blocks: list[str] = []
    for chunk_index in range(n_chunks):
        lines = ["    <<"]
        for part_index, part in enumerate(handpan_set.parts):
            chunk_tokens = chunks_per_part[part_index][chunk_index] if chunk_index < len(chunks_per_part[part_index]) else []
            lines.append(f"      \\SetTranslateTable #{part.instrument_name}")
            lines.append(f'      \\absolute {{ \\HandpanScore "{" ".join(chunk_tokens)}" }}')
            if part_index < n_parts - 1:
                lines.append("      \\\\")
        lines.append("    >>")
        chunk_blocks.append("\n".join(lines))

    return (
        _ly_preamble(handpan_set.name, handpan_set.name, handpan_set.key_signature)
        + "\n".join(chunk_blocks) + "\n"
        + _LY_SUFFIX
    )
