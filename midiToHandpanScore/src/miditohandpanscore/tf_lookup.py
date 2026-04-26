"""MIDI note number → ToneField lookup utilities."""

from typing import NamedTuple, TypeAlias

from .models import HandpanSet


class HarmonicInterval(NamedTuple):
    semitones: int
    harmonic_number: int


_HARMONIC_INTERVALS: tuple[HarmonicInterval, ...] = (
    HarmonicInterval(semitones=12, harmonic_number=1),
    HarmonicInterval(semitones=19, harmonic_number=2),
)


class SetLookup(NamedTuple):
    part_index: int
    tone_field_number: int
    harmonic: int


# (tonefields, part_index, harmonic) のリスト。先頭が最高優先度。
PriorityEntry: TypeAlias = tuple[list[int], int, int]

# (root_midi, reachable_midi_set) のリスト。ナチュラルマイナー正規化に使用。
NormInfo: TypeAlias = list[tuple[int, frozenset[int]]]


def find_tf(midi_note: int, tonefields: list[int]) -> int | None:
    """tonefields（MIDI ノート番号のリスト）内で midi_note を探し、インデックス（= TF 番号）を返す。"""
    try:
        return tonefields.index(midi_note)
    except ValueError:
        return None


def normalize_midi(midi_note: int, norm_info: NormInfo) -> int:
    """ハーモニックマイナー・メロディックマイナー由来の上昇6度・上昇7度をナチュラルマイナーへ写像する。

    norm_info を順に試み、最初に正規化できた値を返す。対象外はそのまま返す。
    """
    for root_midi, reachable in norm_info:
        raised_pcs = frozenset({(root_midi + 9) % 12, (root_midi + 11) % 12})
        if midi_note % 12 in raised_pcs:
            natural = midi_note - 1
            if natural in reachable:
                return natural
    return midi_note


def set_priority(handpan_set: HandpanSet) -> list[PriorityEntry]:
    """セット用の優先度リストを返す（各ハーモニクスレベルで全パートを走査）。"""
    offsets = [(0, 0), *((i.semitones, i.harmonic_number) for i in _HARMONIC_INTERVALS)]
    return [
        ([m + offset for m in part.scale.midi_notes], part_idx, harmonic)
        for offset, harmonic in offsets
        for part_idx, part in enumerate(handpan_set.parts)
    ]


def build_norm_info(handpan_set: HandpanSet, priority: list[PriorityEntry]) -> NormInfo:
    """各パートの正規化情報（ルート音・到達可能ノート集合）を構築する。"""
    norm_info: NormInfo = []
    for part_idx, part in enumerate(handpan_set.parts):
        reachable: set[int] = set()
        for tonefields, pi, _ in priority:
            if pi == part_idx:
                reachable.update(tonefields)
        norm_info.append((part.scale.midi_notes[0], frozenset(reachable)))
    return norm_info


def find_lookup(midi: int, priority: list[PriorityEntry]) -> SetLookup | None:
    """priority リストを先頭から走査し、最初にヒットした SetLookup を返す。未発見は None。"""
    for tonefields, part_idx, harmonic in priority:
        tf_num = find_tf(midi, tonefields)
        if tf_num is not None:
            return SetLookup(part_index=part_idx, tone_field_number=tf_num, harmonic=harmonic)
    return None
