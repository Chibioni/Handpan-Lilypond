# データ構造 仕様書

## `HandpanScale`

```python
from dataclasses import dataclass

@dataclass
class HandpanScale:
    scale_family: str        # スケール種別（例: "Kurd", "Low Pygmy"）
    note_names: list[str]    # 実音の音名リスト（例: ["D3", "A3", "Bb3", ...]）
                             # インデックス = トーンフィールド番号
                             # **note_names[0] は必ず Ding でなければならない**
                             # （ピッチが最低音でなくてもよい。例: F Low Pygmy では Db3 より高い F3 が Ding）
                             # TF1 以降は残りのノートを実音昇順で並べる
    key_signature: str       # LilyPond の調号指定文字列（例: "d \\minor", "f \\major"）

    @property
    def midi_notes(self) -> list[int]:
        # 音名リストから MIDI ノート番号リストを導出する
        return [note(n) for n in self.note_names]

    @property
    def name(self) -> str:
        # 例: "D_Kurd9", "F_Low_Pygmy19"
        family = self.scale_family.replace(" ", "_")
        return f"{ding_note_name(self.note_names[0])}_{family}{len(self.note_names)}"

    @property
    def ly_name(self) -> str:
        # LilyPond 識別子（例: "d_kurd9", "f_sharp_minor18", "b_flat_low_pygmy9"）
        family_slug = self.scale_family.lower().replace(" ", "_")
        return f"{ding_ly_note_name(self.note_names[0])}_{family_slug}{len(self.note_names)}"

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
        ding_name = self.parts[0].scale.note_names[0]
        total = sum(len(p.scale.note_names) for p in self.parts)
        family = self.scale_family.replace(" ", "_")
        return f"{ding_note_name(ding_name)}_{family}{total}"

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
    # 変音記号:
    #   "#"  = シャープ（+1半音）
    #   "b"  = フラット（-1半音）
    #   "##" または "x" = ダブルシャープ（+2半音）
    #   "bb" = ダブルフラット（-2半音）
    #   省略可
    # オクターブ番号: 整数（C4 = MIDI 60 を基準）
    # 例: "D3", "Bb3", "C#4", "F#3", "Ab4", "Cx4", "Dbb3"


def ding_note_name(note_name: str) -> str:
    """音名文字列（オクターブ付き）から大文字スケール名プレフィックスを返す。
    例: "D3"→"D", "F#3"→"F_Sharp", "Bb3"→"B_Flat", "Cx4"→"C_Sharp_Sharp"
    """
    # ding_ly_note_name() の結果を先頭大文字・"_" 区切りに変換する
    # 例: "d" → "D"、"f_sharp" → "F_Sharp"、"b_flat" → "B_Flat"

def ding_ly_note_name(note_name: str) -> str:
    """音名文字列（オクターブ付き）から ly_name 用の小文字音名を返す。
    シャープは _sharp、フラットは _flat、ダブルは重ねて付与する。
    例: "D3"→"d", "F#3"→"f_sharp", "Bb3"→"b_flat", "Cx4"→"c_sharp_sharp"
    """
    ...
```

`ding_ly_note_name` の変換規則:

幹音はそのまま小文字化し、変音記号を `_sharp` / `_flat` に変換して連結する。

| 入力例 | 戻り値 |
|--------|--------|
| `C3` | `c` |
| `C#3` | `c_sharp` |
| `Db3` | `d_flat` |
| `D3` | `d` |
| `Cx3`（ダブルシャープ） | `c_sharp_sharp` |
| `Dbb3`（ダブルフラット） | `d_flat_flat` |
| `F#3` | `f_sharp` |
| `Bb3` | `b_flat` |

異名同音の選択は `note_names` に格納された元の音名綴り（`#` か `b`）に従う。

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
        note_names=["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"],
        key_signature="d \\minor",
    ),
}

ENSEMBLES: dict[str, HandpanEnsemble] = {
    "f_sharp_minor18": HandpanEnsemble(
        scale_family="Minor",
        parts=[
            HandpanPart("Grand", HandpanScale(
                scale_family="Grand",
                note_names=["F#3", "A3", "C#4", "E4", "G#4", "B4", "D5", "F#5", "A5"],
                key_signature="fis \\minor",
            )),
            HandpanPart("Leon", HandpanScale(
                scale_family="Leon",
                note_names=["G#3", "B3", "D4", "F#4", "A4", "C#5", "E5", "G#5", "B5"],
                key_signature="fis \\minor",
            )),
        ],
        key_signature="fis \\minor",
    ),
}
```
