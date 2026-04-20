# midiToHandpanScore

MIDI ファイルをハンドパン用 LilyPond 記法に変換するツール群。

## 必要環境

- Python 3.12 以上
- LilyPond 2.24.4（楽譜のコンパイルに使用）

## インストール

```bash
cd midiToHandpanScore
pip install .
```

または [uv](https://docs.astral.sh/uv/) を使う場合:

```bash
cd midiToHandpanScore
uv sync
```

インストール後、以下の 2 つのコマンドが使えるようになります。

---

## コマンド一覧

### `handpan-generate-scales` — スケール定義ファイルの生成

ハンドパンのスケール定義（トーンフィールド番号 → 音高の対応表）を LilyPond ファイルとして出力します。

```
handpan-generate-scales [--scale SCALE_NAME] [--output-dir DIR]
```

| オプション           | 説明                                             | デフォルト     |
|----------------------|--------------------------------------------------|----------------|
| `--scale SCALE_NAME` | 特定のスケールのみ生成。省略時は全スケールを生成 | （全スケール） |
| `--output-dir DIR`   | 出力先ディレクトリ                               | `../Scales`    |

**使用例:**

```bash
# D Kurd9 スケールのみ生成
handpan-generate-scales --scale d_kurd9 --output-dir ./Scales

# 登録されている全スケールを生成
handpan-generate-scales --output-dir ./Scales
```

**利用可能なスケール名:**

| スケール名 | 内容                                             |
|------------|--------------------------------------------------|
| `d_kurd9`  | D Kurd 9音 (D3, A3, Bb3, C4, D4, E4, F4, G4, A4) |

**利用可能なセット名（複数台ハンドパン）:**

| セット名          | 内容                                     |
|-------------------|------------------------------------------|
| `f_sharp_minor18` | F# Minor 18音（Grand + Leon の 2台構成） |

---

### `handpan-midi-to-score` — MIDI からハンドパン記譜への変換

MIDI ファイルを読み込み、ハンドパン記法の LilyPond ファイルを生成します。

```
handpan-midi-to-score input.mid (--scale SCALE_NAME | --ensemble SET_NAME) [options]
```

| オプション            | 説明                                                             | デフォルト               |
|-----------------------|------------------------------------------------------------------|--------------------------|
| `--scale SCALE_NAME`  | 使用するスケール名（`--ensemble` と排他）                        | —                        |
| `--ensemble SET_NAME` | 使用するセット名（`--scale` と排他）                             | —                        |
| `--output FILE`       | 出力 `.ly` ファイルパス                                          | `input.ly`（入力と同名） |
| `--tempo BPM`         | テンポを BPM で上書き（MIDI 内テンポを無視）                     | MIDI から自動取得        |
| `--min-duration DUR`  | この音価より短いノートはスキップ（`4`, `8`, `16`, `32` など）    | `32`                     |
| `--track N`           | 読み込む MIDI トラック番号（0 始まり）。省略時は全トラックを統合 | （全トラック）           |
| `--bars-per-chunk N`  | 出力の 1 行あたりの小節数                                        | `4`                      |

**使用例:**

```bash
# D Kurd9 スケールで変換（出力は my_song.ly）
handpan-midi-to-score my_song.mid --scale d_kurd9

# 出力ファイルを指定
handpan-midi-to-score my_song.mid --scale d_kurd9 --output score.ly

# テンポを 80 BPM に固定し、16分音符より短いノートをスキップ
handpan-midi-to-score my_song.mid --scale d_kurd9 --tempo 80 --min-duration 16

# 2台ハンドパン構成で変換
handpan-midi-to-score my_song.mid --ensemble f_sharp_minor18

# MIDI の 2 番目のトラックのみ使用
handpan-midi-to-score my_song.mid --scale d_kurd9 --track 1
```

---

## 典型的なワークフロー

```bash
# 1. スケール定義ファイルを生成
handpan-generate-scales --scale d_kurd9 --output-dir ../Scales

# 2. MIDI を LilyPond 記法に変換
handpan-midi-to-score my_song.mid --scale d_kurd9 --output my_song.ly

# 3. LilyPond でコンパイル（PDF 生成）
lilypond my_song.ly
```

---

## 入力 MIDI の仕様

### 対応フォーマット

| フォーマット                 | 対応                                       |
|------------------------------|--------------------------------------------|
| Format 0（シングルトラック） | 対応                                       |
| Format 1（マルチトラック）   | 対応。`--track` 未指定時は全トラックを統合 |
| Format 2                     | 非対応（エラー終了）                       |

### Velocity → アーティキュレーション

DAW で打ち込む際に velocity を使ってアーティキュレーションを指定します。

| velocity | 意味           | 記法   |
|----------|----------------|--------|
| 127      | アクセント     | `1!-4` |
| 1–30     | ゴーストノート | `2.-8` |
| 31–126   | 通常           | `1-4`  |

### 奏法マーカーノート

MIDI ノート 0・1 は奏法マーカーとして予約されています。通常のハンドパン音域では使用しません。

| MIDI ノート | 効果                                              |
|-------------|---------------------------------------------------|
| 0           | 同じタイミングの音符に `O`（Apex リング打）を付加 |
| 1           | 同じタイミングの音符に `S`（スラップ）を付加      |

マーカーノート自体は音符として出力されません。velocity によるアーティキュレーションと組み合わせ可能です（例: `S1!-4`、`O2.-8`）。

### ハーモニクス

ハーモニクスは実際に鳴る音高（基音 + 12 半音 または + 19 半音）で MIDI に記録します。変換ツールが自動的に `^1` / `^2` に変換します。

| 音高のオフセット                          | 記法      |
|-------------------------------------------|-----------|
| 基音 + 12 半音（1オクターブ上）           | `^1`（◆） |
| 基音 + 19 半音（1オクターブ + 完全5度上） | `^2`（◇） |

---

## 出力フォーマット

`handpan-midi-to-score` が生成する `.ly` ファイルは、`\HandpanScore` 関数で使用できるハンドパン記法のトークン列を含みます。

```lilypond
\version "2.24.4"
\include "../Handpan.ily"
\include "../Scales/D_Kurd9.ly"

\SetTranslateTable #d_kurd9

\score {
  \new Staff {
    \HandpanScore "
      1-4 2-8 [ 3-16 4-16 ] \| 5-4. R-8 \|
    "
  }
}
```

### 記法の読み方

| 記号                | 意味                                | 例                     |
|---------------------|-------------------------------------|------------------------|
| `0`〜`N`            | トーンフィールド番号（2桁以上も可） | `1-4`（TF1、四分音符） |
| `-4` / `-8` / `-16` | 音価（四分 / 八分 / 十六分）        | `2-8`                  |
| `-4.` / `-4..`      | 付点・二重付点                      | `3-4.`                 |
| `!`                 | アクセント（velocity 127）          | `1!-4`                 |
| `.`                 | ゴーストノート（velocity 1–30）     | `2.-8`                 |
| `O`                 | Apex リング打                       | `O1-4`                 |
| `S`                 | スラップ                            | `S2-4`                 |
| `^1` / `^2`         | ハーモニクス 1 / 2                  | `3^1-4`                |
| `R`                 | 休符                                | `R-4`                  |
| `[ ... ]`           | 連桁グループ                        | `[ 3-8 4-8 ]`          |
| `< ... >`           | 和音                                | `< 1-4 3-4 >`          |
| `\|`                | 小節線                              | `1-4 \|`               |
