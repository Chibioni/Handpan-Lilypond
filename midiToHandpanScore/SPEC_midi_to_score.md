# MIDI → 楽譜変換 仕様書

## 概要

MIDI ファイルを読み込み、ハンドパン記法文字列を経由して LilyPond `.ly` ファイルを生成する。

```
MIDIファイル
  ↓ MIDI読み込み（SPEC_midi_processing.md）
MidiNoteEvent リスト（MIDIノート番号 + ティック位置）
  ↓ テンポ処理 + 量子化（SPEC_midi_processing.md）
MidiNoteEvent リスト（MIDIノート番号 + 音価文字列）
  ↓ トーンフィールド変換（HandpanScale / SPEC_data_structures.md）
ハンドパン記法トークン列（"1-4", "2-8", ...）
  ↓ テンプレート埋め込み
LilyPond .ly ファイル
```

---

## CLI ツール: `handpan-midi-to-score`

```
handpan-midi-to-score <input.mid> --scale <scale_name> [options]
```

| 引数・オプション | 必須 | 説明 |
|---|---|---|
| `input.mid` | 必須 | 入力 MIDI ファイルパス |
| `--scale` | `--ensemble` と排他・どちらか必須 | 使用するスケール名（例: `d_kurd9`） |
| `--ensemble` | `--scale` と排他・どちらか必須 | 使用するアンサンブル名（例: `f_sharp_minor18`） |
| `--output` | 任意 | 出力 `.ly` ファイルパス（省略時: 入力ファイルと同ディレクトリ・同名の `.ly`） |
| `--tempo` | 任意 | BPM を上書き（省略時: MIDI 内の `set_tempo` を使用、なければ 120） |
| `--min-duration` | 任意 | 量子化対象の最小音価（省略時: `32`）。これより短いノートはスキップ |
| `--track` | 任意 | 変換対象トラック番号・0始まり（省略時: 全トラック統合） |
| `--bars-per-chunk` | 任意 | 1つの `\HandpanScore` に収める小節数（省略時: `4`） |

**実行例:**
```
$ handpan-midi-to-score song.mid --scale d_kurd9
[INFO] Tempo: 120 BPM (from MIDI)
[WARN] Skipped MIDI note 65 (F4) at tick 480: not in scale d_kurd9
[WARN] Skipped MIDI note 71 (B4) at tick 960: duration too short (0.06 beats)
[INFO] Generated: song.ly
```

**エラー例:**
```
$ handpan-midi-to-score song.mid --scale unknown
[ERROR] Scale not found: unknown

$ handpan-midi-to-score missing.mid --scale d_kurd9
[ERROR] File not found: missing.mid

$ handpan-midi-to-score song.mid --scale d_kurd9 --ensemble f_sharp_minor18
[ERROR] --scale and --ensemble are mutually exclusive

$ handpan-midi-to-score song.mid --scale d_kurd9 --bars-per-chunk 0
[ERROR] --bars-per-chunk must be a positive integer
```

---

## 変換仕様

### MIDI ノート番号 → トーンフィールド番号

変換開始時に、基音テーブルとハーモニクステーブルを構築する。

```python
# 基音テーブル
midi_to_tf: dict[int, int] = {
    midi: tf_num
    for tf_num, midi in enumerate(scale.midi_notes)
}

# ハーモニクステーブル（基音 + 12 = ハーモニクス1、基音 + 19 = ハーモニクス2）
midi_to_harmonic: dict[int, tuple[int, int]] = {}
for tf_num, midi in enumerate(scale.midi_notes):
    midi_to_harmonic[midi + 12] = (tf_num, 1)
    midi_to_harmonic[midi + 19] = (tf_num, 2)
```

ノートの判定順序:
1. `midi_to_tf` に存在する → 通常ノート
2. `midi_to_harmonic` に存在する → ハーモニクスノート（`TFn^1` または `TFn^2`）
3. どちらにも存在しない → スキップ

### スキップ条件

以下のいずれかに該当するノートはスキップし、`[WARN]` を stderr に出力する。

| 条件 | ログ例 |
|------|--------|
| 基音・ハーモニクスいずれにも該当しない MIDI ノート番号 | `[WARN] Skipped MIDI note 65 (F4) at tick 480: not in scale d_kurd9` |
| 量子化後の音価が `--min-duration` 未満 | `[WARN] Skipped MIDI note 69 (A4) at tick 240: duration too short (0.06 beats)` |

スキップされたノートは出力トークン列に含めない（休符にもしない）。

### 同時発音（和音）の扱い

`tick_start` が同一の複数ノートは和音（`< ... >`）として出力する。

- 和音内の音価は最長のものを採用する
- 和音内にスキップノートが含まれる場合、そのノートのみ除外し和音を継続する
- スキップの結果、和音が1音になった場合は通常の単音トークンとして出力する

### トークンの順序

`tick_start` 昇順でトークンを並べる。

---

## LilyPond 出力仕様

### `.ly` ファイルテンプレート

```lilypond
\version "2.24.4"

\include "../Handpan.ily"
\include "../Scales/{Name}.ly"

\SetTranslateTable #{ly_name}

\score {
  \header {
    title = "{scale.name}"
  }
  \new Staff {
    \clef treble
    \key {key_signature}
    {HandpanScore blocks}
  }
}
```

- `{Name}`: `HandpanScale.name`（例: `D_Kurd9`）
- `{ly_name}`: `HandpanScale.ly_name`（例: `d_kurd9`）
- `{key_signature}`: `HandpanScale.key_signature`（例: `d \minor`）
- `{HandpanScore blocks}`: `--bars-per-chunk` 小節ごとに分割した `\HandpanScore` 呼び出しの列

### `\HandpanScore` 分割規則

トークン列を `--bars-per-chunk`（デフォルト: 4）小節単位で分割し、各チャンクを独立した `\HandpanScore "..."` として出力する。

```
\HandpanScore "{chunk1_tokens}"
\HandpanScore "{chunk2_tokens}"
...
```

- 小節線トークン `\|` はチャンク先頭・末尾には含めない
- チャンク内にトークンがない場合（全ノートがスキップされた小節など）はそのチャンクを省略する

### 出力例

```lilypond
\version "2.24.4"

\include "../Handpan.ily"
\include "../Scales/D_Kurd9.ly"

\SetTranslateTable #d_kurd9

\score {
  \header {
    title = "D_Kurd9"
  }
  \new Staff {
    \clef treble
    \key d \minor
    \HandpanScore "1-4 2-8 3-8 4-4 \| 5-4 6-8 7-8 8-4 \| 1-2 2-4 R-4 \| 3-4 4-4 5-4 6-4"
    \HandpanScore "7-4 8-4 1-4 2-4 \| 3-8 4-8 5-4 R-4 \| 6-4 7-4 8-2 \| 1-1"
  }
}
```

---

## アンサンブル出力仕様

`--ensemble` 指定時は1段2声で出力する。

### テンプレート

```lilypond
\version "2.24.4"

\include "../Handpan.ily"
\include "../Scales/{ensemble.name}.ly"

\score {
  \header {
    title = "{ensemble.name}"
  }
  \new Staff {
    \clef treble
    \key {key_signature}
    <<
      \SetTranslateTable #{part0.instrument_name}
      \absolute { \HandpanScore "{tokens_part0}" } \\
      \SetTranslateTable #{part1.instrument_name}
      \absolute { \HandpanScore "{tokens_part1}" }
    >>
  }
}
```

### MIDI → パート割り当て

1. 全パートの `midi_notes` を結合し `midi_to_part: dict[int, (part_index, tf_num)]` を構築
2. 同一 MIDI ノートが複数パートに存在する場合は先のパート（インデックス小）を優先
3. 各パートのトークン列を独立して生成し、相手パートが演奏する時刻は `H`（非表示休符）で埋める
   - `H` の音価は、その `tick_start` に該当するノートの量子化後音価を使用する
   - 和音の場合は和音内の最長音価を使用する（単音トークンと同じ規則）

```python
midi_to_part: dict[int, tuple[int, int]] = {}
for part_idx, part in enumerate(ensemble.parts):
    for tf_num, midi in enumerate(part.scale.midi_notes):
        if midi in midi_to_part:
            first = ensemble.parts[midi_to_part[midi][0]].instrument_name
            print(f"[WARN] Overlapping MIDI note {midi} in ensemble: "
                  f"{part.instrument_name} TF{tf_num} shadowed by {first}",
                  file=sys.stderr)
        else:
            midi_to_part[midi] = (part_idx, tf_num)
```

`--bars-per-chunk` 小節ごとに `<< ... \\ ... >>` ブロック単位で分割する。

### 出力例（F_Sharp_Minor18）

```lilypond
\version "2.24.4"

\include "../Handpan.ily"
\include "../Scales/F_Sharp_Minor18.ly"

\score {
  \header {
    title = "F_Sharp_Minor18"
  }
  \new Staff {
    \clef treble
    \key fis \minor
    <<
      \SetTranslateTable #Grand
      \absolute { \HandpanScore "0-4 H-4 1-4 H-4 \| 2-4 H-4 3-4 H-4" } \\
      \SetTranslateTable #Leon
      \absolute { \HandpanScore "H-4 0-4 H-4 1-4 \| H-4 2-4 H-4 3-4" }
    >>
    <<
      \SetTranslateTable #Grand
      \absolute { \HandpanScore "4-4 H-4 5-4 H-4" } \\
      \SetTranslateTable #Leon
      \absolute { \HandpanScore "H-4 4-4 H-4 5-4" }
    >>
  }
}
```

---

## ログ仕様

出力先: 標準エラー出力（stderr）

| レベル | 用途 |
|--------|------|
| `[INFO]` | テンポ・出力ファイルパスなどの正常処理情報 |
| `[WARN]` | スキップされたノート、アンサンブルの重複ノート |
| `[ERROR]` | 処理中断（ファイル未発見、スケール名不正、非対応フォーマットなど） |

---

## 既知の制限・将来課題

| 項目 | 内容 |
|------|------|
| 自動休符挿入 | 小節内の空白を休符で補完する処理は未実装 |
| 連桁の自動生成 | `[ ]` グループは出力しない |
| Format 2 MIDI | 非対応 |
