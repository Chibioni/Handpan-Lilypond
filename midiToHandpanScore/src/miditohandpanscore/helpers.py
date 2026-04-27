"""Helper functions for note name and MIDI note number conversion."""

from typing import NamedTuple

_NATURAL_SEMITONES: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11
}

_ACCIDENTAL_MAP: dict[str, int] = {
    "": 0, "#": 1, "b": -1, "x": 2, "##": 2, "bb": -2
}

_ACCIDENTAL_NAMES: dict[int, list[str]] = {
    0: [], 1: ["Sharp"], -1: ["Flat"], 2: ["Sharp", "Sharp"], -2: ["Flat", "Flat"]
}


class ParsedNote(NamedTuple):
    stem: str
    accidental: int
    octave: int


def _parse_note_name(name: str) -> ParsedNote:
    """音名文字列をパースして ParsedNote(幹音, 変音記号の半音数, オクターブ) を返す。

    対応する変音記号:
      "#"  → +1、"b"  → -1
      "##" → +2、"x"  → +2（ダブルシャープ）
      "bb" → -2（ダブルフラット）

    Args:
        name: パース対象の音名文字列（例: "D3", "Bb3", "F#4", "Cx4"）。

    Returns:
        ParsedNote（幹音文字, 変音記号の半音数, オクターブ番号）。

    Raises:
        ValueError: 幹音が A–G 以外の場合。
    """
    name = name.strip()
    stem = name[0].upper()
    if stem not in _NATURAL_SEMITONES:
        raise ValueError(f"Invalid note name: {name!r}")

    # オクターブ番号を末尾から先に確定
    oct_idx = len(name)
    while oct_idx > 1 and (name[oct_idx - 1].isdigit() or name[oct_idx - 1] == '-'):
        oct_idx -= 1
    try:
        octave = int(name[oct_idx:])
    except ValueError:
        raise ValueError(f"Invalid octave number in note name: {name!r}") from None

    acc_str = name[1:oct_idx]
    if acc_str not in _ACCIDENTAL_MAP:
        raise ValueError(f"Invalid accidental {acc_str!r} in note name: {name!r}")
    accidental = _ACCIDENTAL_MAP[acc_str]

    return ParsedNote(stem=stem, accidental=accidental, octave=octave)


def note_name_to_midi(name: str) -> int:
    """音名文字列を MIDI ノート番号に変換する。

    例: "D3" → 50、"Bb3" → 58、"C#4" → 61、"Cx4" → 62、"Dbb3" → 48

    Args:
        name: 変換対象の音名文字列（例: "D3", "F#4", "Bb3"）。

    Returns:
        MIDI ノート番号（0–127）。

    Raises:
        ValueError: 音名が不正な場合、または MIDI 範囲（0–127）外の場合。
    """
    parsed = _parse_note_name(name)
    midi = (parsed.octave + 1) * 12 + _NATURAL_SEMITONES[parsed.stem] + parsed.accidental
    if not (0 <= midi <= 127):
        raise ValueError(f"MIDI note number out of range (0–127): {midi!r} from {name!r}")
    return midi


def note_name_to_scale_identifier(note_name: str) -> str:
    """音名文字列（オクターブ付き）からスケール識別子用プレフィックスを返す。

    例: "D3" → "D"、"F#3" → "F_Sharp"、"Bb3" → "B_Flat"、"Cx4" → "C_Sharp_Sharp"

    Args:
        note_name: 変換対象の音名文字列（例: "D3", "F#4", "Bb3"）。

    Returns:
        スケール識別子プレフィックス文字列（例: "D", "F_Sharp", "B_Flat"）。
    """
    parsed = _parse_note_name(note_name)
    parts = [parsed.stem] + _ACCIDENTAL_NAMES[parsed.accidental]
    return "_".join(parts)
