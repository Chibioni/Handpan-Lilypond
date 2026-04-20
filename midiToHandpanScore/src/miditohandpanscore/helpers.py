"""Helper functions for note name and MIDI note number conversion."""

from typing import NamedTuple

_NATURAL_SEMITONES: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11
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
    """
    name = name.strip()
    stem = name[0].upper()
    if stem not in _NATURAL_SEMITONES:
        raise ValueError(f"Invalid note name: {name!r}")

    index = 1
    accidental = 0
    # ダブルシャープ: "##" または "x"
    if name[index:index + 2] == "##":
        accidental = 2
        index += 2
    elif index < len(name) and name[index] == "x":
        accidental = 2
        index += 1
    # ダブルフラット: "bb"
    elif name[index:index + 2] == "bb":
        accidental = -2
        index += 2
    # シングル
    elif index < len(name) and name[index] == "#":
        accidental = 1
        index += 1
    elif index < len(name) and name[index] == "b":
        accidental = -1
        index += 1

    octave = int(name[index:])
    return ParsedNote(stem=stem, accidental=accidental, octave=octave)


def note_name_to_midi(name: str) -> int:
    """音名文字列を MIDI ノート番号に変換。

    例: "D3"→50, "Bb3"→58, "C#4"→61, "Cx4"→62, "Dbb3"→48
    有効範囲は 0〜127（MIDI 規格）。範囲外は ValueError を送出する。
    """
    parsed = _parse_note_name(name)
    midi = (parsed.octave + 1) * 12 + _NATURAL_SEMITONES[parsed.stem] + parsed.accidental
    if not (0 <= midi <= 127):
        raise ValueError(f"MIDI note number out of range (0–127): {midi!r} from {name!r}")
    return midi


def note_name_to_scale_identifier(note_name: str) -> str:
    """音名文字列（オクターブ付き）からスケール識別子用プレフィックスを返す。

    例: "D3"→"D", "F#3"→"F_Sharp", "Bb3"→"B_Flat", "Cx4"→"C_Sharp_Sharp"
    """
    parsed = _parse_note_name(note_name)
    parts = [parsed.stem]
    if parsed.accidental == 1:
        parts.append("Sharp")
    elif parsed.accidental == -1:
        parts.append("Flat")
    elif parsed.accidental == 2:
        parts += ["Sharp", "Sharp"]
    elif parsed.accidental == -2:
        parts += ["Flat", "Flat"]
    return "_".join(parts)
