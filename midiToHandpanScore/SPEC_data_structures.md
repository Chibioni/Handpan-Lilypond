# データ構造 仕様書

## `HandpanScale`

```python
from dataclasses import dataclass

@dataclass
class HandpanScale:
    scale_family: str       # スケール種別（例: "Kurd", "Low Pygmy"）
    midi_notes: list[int]   # 実音の MIDI ノート番号リスト
                            # インデックス = トーンフィールド番号
                            # 0 = Ding（中央）、1〜 = 外周・ボトムトーンフィールド
                            # 実音昇順で TF1 から付番する
    key_signature: str      # LilyPond の調号指定文字列（例: "d \\minor", "f \\major"）

    @property
    def name(self) -> str:
        # 例: "D_Kurd9", "F_Low_Pygmy19"
        family = self.scale_family.replace(" ", "_")
        return f"{ding_note_name(self.midi_notes[0])}_{family}{len(self.midi_notes)}"

    @property
    def ly_name(self) -> str:
        # LilyPond 識別子（例: "d_kurd9", "f_sharp_minor18", "b_flat_low_pygmy9"）
        family_slug = self.scale_family.lower().replace(" ", "_")
        return f"{ding_ly_note_name(self.midi_notes[0])}_{family_slug}{len(self.midi_notes)}"

    @property
    def ly_pitches(self) -> list[int]:
        # 位置記譜法に基づく N 値リスト
        # compute_ly_pitches(self.midi_notes) の結果を返す（SPEC_generate_scales.md 参照）
        return compute_ly_pitches(self.midi_notes)
```

出力ファイル名は `{HandpanScale.name}.ly`（例: `D_Kurd9.ly`）とする。

---

## `HandpanPart` / `HandpanEnsemble`

複数のハンドパンで1つのスケールをカバーするアンサンブル定義。

```python
@dataclass
class HandpanPart:
    instrument_name: str  # LilyPond 変数名（例: "Grand", "Leon"）
    scale: HandpanScale

@dataclass
class HandpanEnsemble:
    scale_family: str         # 例: "Minor"
    parts: list[HandpanPart]  # パートリスト（順序 = MIDI重複時の優先順位）
    key_signature: str

    @property
    def name(self) -> str:
        # 例: "F_Sharp_Minor18"
        ding = self.parts[0].scale.midi_notes[0]
        total = sum(len(p.scale.midi_notes) for p in self.parts)
        family = self.scale_family.replace(" ", "_")
        return f"{ding_note_name(ding)}_{family}{total}"

    def part_ly_pitches(self, part_index: int) -> list[int]:
        # 全パートの MIDI ノートを統合した昇順リストを基準に N 値を導出する
        all_midis = sorted(set(m for p in self.parts for m in p.scale.midi_notes))
        ding = self.parts[0].scale.midi_notes[0]
        ding_pos = all_midis.index(ding)
        n_map = {ding: -1}
        for i, m in enumerate(reversed(all_midis[:ding_pos])):
            n_map[m] = -2 - i
        for i, m in enumerate(all_midis[ding_pos + 1:]):
            n_map[m] = 1 + i
        return [n_map[m] for m in self.parts[part_index].scale.midi_notes]
```

出力ファイル名は `{HandpanEnsemble.name}.ly`（例: `F_Sharp_Minor18.ly`）とする。

---

## `MidiNoteEvent`

```python
@dataclass
class MidiNoteEvent:
    midi_note: int    # MIDIノート番号 (0–127)
    tick_start: int   # note_on のティック位置
    tick_end: int     # note_off のティック位置
    velocity: int     # note_on の velocity (1–127)
```

---

## ヘルパー関数

```python
def note(name: str) -> int:
    """音名文字列を MIDI ノート番号に変換。例: "D3"→50, "Bb3"→58, "C#4"→61"""
    # フォーマット: <幹音>[変音記号][オクターブ番号]
    # 幹音: A–G（大文字・小文字どちらも可）
    # 変音記号: "#"（シャープ）または "b"（フラット）、省略可
    # オクターブ番号: 整数（C4 = MIDI 60 を基準）
    # 例: "D3", "Bb3", "C#4", "F#3", "Ab4"

def notes(names: str) -> list[int]:
    """スペース区切りの音名文字列を MIDI ノート番号リストに変換。"""
    return [note(n) for n in names.split()]

def ding_note_name(midi: int) -> str:
    """Ding の MIDI ノート番号から大文字音名を返す。例: 50→"D", 66→"F_Sharp", 58→"B_Flat" """
    # ding_ly_note_name() と同じ変換規則だが、先頭を大文字・区切りを "_" にする
    # 例: "d" → "D"、"f_sharp" → "F_Sharp"、"b_flat" → "B_Flat"

def ding_ly_note_name(midi: int) -> str:
    """Ding の MIDI ノート番号から ly_name 用の小文字音名を返す。
    シャープは _sharp、フラットは _flat サフィックスを付与する。
    例: 50→"d", 66→"f_sharp", 58→"b_flat"
    """
    ...
```

`ding_ly_note_name` の変換規則:

| 音名 | 戻り値 |
|------|--------|
| C | `c` |
| C# / Db | `c_sharp` / `d_flat` |
| D | `d` |
| D# / Eb | `d_sharp` / `e_flat` |
| E | `e` |
| F | `f` |
| F# / Gb | `f_sharp` / `g_flat` |
| G | `g` |
| G# / Ab | `g_sharp` / `a_flat` |
| A | `a` |
| A# / Bb | `a_sharp` / `b_flat` |
| B | `b` |

異名同音の選択は `note()` に渡した元の音名（`#` か `b`）に従う。

| 幹音 | C | D | E | F | G | A | B |
|------|---|---|---|---|---|---|---|
| 半音 | 0 | 2 | 4 | 5 | 7 | 9 | 11 |

変音記号: `b` = フラット（-1半音）、`#` = シャープ（+1半音）  
オクターブ: C4 = MIDI 60 を基準とする。

---

## スケールデータ

スケールデータは `src/miditohandpanscore/scales/data.py` に定義する。

```python
SCALES: dict[str, HandpanScale] = {
    "d_kurd9": HandpanScale(
        scale_family="Kurd",
        midi_notes=notes("D3 A3 Bb3 C4 D4 E4 F4 G4 A4"),
        key_signature="d \\minor",
    ),
}

ENSEMBLES: dict[str, HandpanEnsemble] = {
    "f_sharp_minor18": HandpanEnsemble(
        scale_family="Minor",
        parts=[
            HandpanPart("Grand", HandpanScale(
                scale_family="Grand",
                midi_notes=notes("F#3 A3 C#4 E4 G#4 B4 D5 F#5 A5"),
                key_signature="fis \\minor",
            )),
            HandpanPart("Leon", HandpanScale(
                scale_family="Leon",
                midi_notes=notes("G#3 B3 D4 F#4 A4 C#5 E5 G#5 B5"),
                key_signature="fis \\minor",
            )),
        ],
        key_signature="fis \\minor",
    ),
}
```
