# スケールファイル生成 仕様書

データ構造は `SPEC_data_structures.md` を参照。

---

## CLI ツール: `handpan-generate-scales`

```
handpan-generate-scales [--scale <scale_name>] [--output-dir <dir>]
```

| オプション | 必須 | 説明 |
|---|---|---|
| `--scale` | 任意 | 生成するスケール名（省略時: 全スケールを生成） |
| `--output-dir` | 任意 | 出力先ディレクトリ（省略時: `../Scales/`） |

**実行例:**
```
$ handpan-generate-scales
[INFO] Generated: ../Scales/D_Kurd9.ly

$ handpan-generate-scales --scale d_kurd9 --output-dir ./out
[INFO] Generated: ./out/D_Kurd9.ly
```

**エラー例:**
```
$ handpan-generate-scales --scale unknown
[ERROR] Scale not found: unknown
```

---

## `Scales/*.ly` 生成仕様

### 出力フォーマット

```lilypond
\version "2.24.4"

% {scale.name} スケール定義
% トーンフィールド番号と LilyPond 音高整数の対応表
#(define {scale.ly_name} '(
  ({tf_num} . {ly_pitch}) ...
))
#(define {scale.ly_name}-key-signature "{scale.key_signature}")
```

**出力例（D_Kurd9）:**
```lilypond
\version "2.24.4"

% D_Kurd9 スケール定義
% トーンフィールド番号と LilyPond 音高整数の対応表
#(define d_kurd9 '(
  (0 . -1) (1 . 1) (2 . 2)
  (3 .  3) (4 . 4) (5 . 5)
  (6 .  6) (7 . 7) (8 . 8)
))
#(define d_kurd9-key-signature "d \\minor")
```

### アンサンブル出力フォーマット

各パートの translate-table を1ファイルにまとめて出力する。

```lilypond
\version "2.24.4"

% {ensemble.name} アンサンブル定義
#(define {part.instrument_name} '(
  ({tf_num} . {ly_pitch}) ...
))
...
#(define {ensemble.name}-key-signature "{ensemble.key_signature}")
```

**出力例（F_Sharp_Minor18）:**
```lilypond
\version "2.24.4"

% F_Sharp_Minor18 アンサンブル定義
#(define Grand '(
  (0 . -1) (1 .  2) (2 .  4)
  (3 .  6) (4 .  8) (5 . 10)
  (6 . 12) (7 . 14) (8 . 16)
))
#(define Leon '(
  (0 .  1) (1 .  3) (2 .  5)
  (3 .  7) (4 .  9) (5 . 11)
  (6 . 13) (7 . 15) (8 . 17)
))
#(define F_Sharp_Minor18-key-signature "fis \\minor")
```

---

## `ly_pitches` 導出アルゴリズム（位置記譜法）

`ly_pitches` は `midi_notes` から自動導出する。詳細は [HANDPAN_SPEC.md](../HANDPAN_SPEC.md) の位置記譜法を参照。

```python
def compute_ly_pitches(midi_notes: list[int]) -> list[int]:
    ding = midi_notes[0]
    sorted_midis = sorted(midi_notes)
    ding_pos = sorted_midis.index(ding)
    n_map = {ding: -1}
    for i, m in enumerate(reversed(sorted_midis[:ding_pos])):
        n_map[m] = -2 - i
    for i, m in enumerate(sorted_midis[ding_pos + 1:]):
        n_map[m] = 1 + i
    return [n_map[m] for m in midi_notes]
```

D_Kurd9 での検証:
- Ding = D3(50) → N=-1、残り昇順で N=1〜8
- 結果: `[-1, 1, 2, 3, 4, 5, 6, 7, 8]` ✓

### 変音記号の扱い

ハンドパンは非クロマティック楽器のため、演奏中に臨時記号を追加することは不可能。
`Handpan.ily` は `ly:make-pitch 0 N NATURAL` で音高を表現し、音符ごとの変音記号は付与しない。
スケールのフラット・シャープ構成は `HandpanScale.key_signature` による調号と楽譜先頭のスケール名で示す。

---

## ログ仕様

出力先: 標準エラー出力（stderr）

| レベル | 用途 |
|--------|------|
| `[INFO]` | 生成完了（出力ファイルパス） |
| `[ERROR]` | 処理中断（スケール名不正、書き込み失敗など） |
