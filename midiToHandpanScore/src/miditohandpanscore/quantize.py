"""Duration quantization utilities."""

from typing import Literal, NamedTuple, TypeAlias

DurationStr: TypeAlias = Literal[
    "1", "2..", "2.", "2", "4..", "4.", "4", "8..", "8.", "8", "16.", "16", "32.", "32"
]


class DurationEntry(NamedTuple):
    beats: float
    duration_str: DurationStr


DURATION_TABLE: list[DurationEntry] = [
    DurationEntry(4.0,    "1"),
    DurationEntry(3.5,    "2.."),
    DurationEntry(3.0,    "2."),
    DurationEntry(2.0,    "2"),
    DurationEntry(1.75,   "4.."),
    DurationEntry(1.5,    "4."),
    DurationEntry(1.0,    "4"),
    DurationEntry(0.875,  "8.."),
    DurationEntry(0.75,   "8."),
    DurationEntry(0.5,    "8"),
    DurationEntry(0.375,  "16."),
    DurationEntry(0.25,   "16"),
    DurationEntry(0.1875, "32."),
    DurationEntry(0.125,  "32"),
]

DUR_TO_BEATS: dict[str, float] = {entry.duration_str: entry.beats for entry in DURATION_TABLE}


def quantize(beats: float) -> DurationStr:
    """拍数を最近傍の音価文字列に変換する。

    DURATION_TABLE の中から beats との差が最小のエントリを選ぶ。
    正確に一致するエントリがない場合は最も近い音価を返す。

    Args:
        beats: 量子化対象の拍数（例: 1.0 → "4"、0.5 → "8"）。

    Returns:
        最近傍の音価文字列（例: "4", "8.", "4.."）。
    """
    return min(DURATION_TABLE, key=lambda entry: abs(entry.beats - beats)).duration_str
