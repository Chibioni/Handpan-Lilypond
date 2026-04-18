"""Helper functions for note name and MIDI note number conversion."""

_NATURAL_SEMITONES: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11
}


def _parse_note_name(name: str) -> tuple[str, int, int]:
    """音名文字列をパースして (幹音, 変音記号の半音数, オクターブ) を返す。

    対応する変音記号:
      "#"  → +1、"b"  → -1
      "##" → +2、"x"  → +2（ダブルシャープ）
      "bb" → -2（ダブルフラット）
    """
    name = name.strip()
    stem = name[0].upper()
    if stem not in _NATURAL_SEMITONES:
        raise ValueError(f"Invalid note name: {name!r}")

    idx = 1
    accidental = 0
    # ダブルシャープ: "##" または "x"
    if name[idx:idx + 2] == "##":
        accidental = 2
        idx += 2
    elif idx < len(name) and name[idx] == "x":
        accidental = 2
        idx += 1
    # ダブルフラット: "bb"
    elif name[idx:idx + 2] == "bb":
        accidental = -2
        idx += 2
    # シングル
    elif idx < len(name) and name[idx] == "#":
        accidental = 1
        idx += 1
    elif idx < len(name) and name[idx] == "b":
        accidental = -1
        idx += 1

    octave = int(name[idx:])
    return stem, accidental, octave


def note(name: str) -> int:
    """音名文字列を MIDI ノート番号に変換。

    例: "D3"→50, "Bb3"→58, "C#4"→61, "Cx4"→62, "Dbb3"→48
    """
    stem, accidental, octave = _parse_note_name(name)
    return (octave + 1) * 12 + _NATURAL_SEMITONES[stem] + accidental


def ding_ly_note_name(note_name: str) -> str:
    """音名文字列（オクターブ付き）から ly_name 用の小文字音名を返す。

    例: "D3"→"d", "F#3"→"f_sharp", "Bb3"→"b_flat", "Cx4"→"c_sharp_sharp"
    """
    stem, accidental, _ = _parse_note_name(note_name)
    parts = [stem.lower()]
    if accidental == 1:
        parts.append("sharp")
    elif accidental == -1:
        parts.append("flat")
    elif accidental == 2:
        parts += ["sharp", "sharp"]
    elif accidental == -2:
        parts += ["flat", "flat"]
    return "_".join(parts)


def ding_note_name(note_name: str) -> str:
    """音名文字列（オクターブ付き）から大文字スケール名プレフィックスを返す。

    例: "D3"→"D", "F#3"→"F_Sharp", "Bb3"→"B_Flat", "Cx4"→"C_Sharp_Sharp"
    """
    ly = ding_ly_note_name(note_name)
    return "_".join(part.capitalize() for part in ly.split("_"))
