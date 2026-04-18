# Handpan-Lilypond

ハンドパン用の独自記法を LilyPond の音楽オブジェクトへ変換する LilyPond ライブラリ。

> ハンドパンという楽器の構造・スケール・このプロジェクトの記譜法については [HANDPAN_SPEC.md](HANDPAN_SPEC.md) を参照すること。

## プロジェクト構成

```
Handpan.ily          # メインライブラリ（Scheme + LilyPond）
Scales/              # 音階定義ファイル（トーンフィールド番号→音高の対応表）
  Kurd9.ly           # Kurd9 スケール定義
tests/               # テストスイート
  Handpan-test.sh    # テスト実行スクリプト
  *.ly               # 各関数のテストファイル
  utils/             # テスト用ユーティリティ
  test-functions.ily # test-ok / test-error / value-test ヘルパー
midiToHandpanScore/  # MIDI → ハンドパン記法変換ツール（Python）
```

## テストの実行

```bash
cd tests
bash Handpan-test.sh
```

LilyPond 2.24.4 が必要。各テストファイルは `lilypond` コマンドで実行される。

## 主要な関数（Handpan.ily）

| 関数 | 役割 |
|------|------|
| `HandpanScore` | 記法文字列を受け取り LilyPond 音楽オブジェクトへ変換するメイン関数 |
| `SetTranslateTable` | スケール定義テーブルをセット |
| `handpan-score-internal` | 文字列をトークン分割 → パース → SequentialMusic に変換 |
| `parse-token-list` | トークンリストを音符・連桁・和音・小節線に振り分け |
| `parse-note-element` | 1トークン（例: `2^1!-8`）を LilyPond NoteEvent に変換 |
| `make-custom-note` | 音高・音価・符頭スタイル・修飾（アクセント/ゴースト）から音符を生成 |
| `pitch-translate` | トーンフィールド番号を五線譜上の音高（整数）に変換 |

## 記法ルール

記法の構造: `[奏法] トーンフィールド番号 [^ハーモニクス] [!アクセント | .ゴースト] - 音価[.]`

| 記号 | 意味 |
|------|------|
| `1`〜`9` | トーンフィールド番号 |
| `^1` / `^2` | ハーモニクス1（◆）/ ハーモニクス2（◇） |
| `!` | アクセント |
| `.` (音価の前) | ゴーストノート |
| `O` | Apex リング打奏 |
| `S` | スラップ |
| `R` | 休符 |
| `H` | 非表示休符（空白休符） |
| `-4` / `-8` / `-4.` / `-8..` | 音価（四分・八分・付点・二重付点） |
| `< ... >` | 和音 |
| `[ ... ]` | 連桁グループ |
| `\|` | 小節線チェック |

## ドキュメント調査に Context7 を使う

LilyPond・Python・Scheme の仕様を調べる際は、Context7 MCP を積極的に利用する。
Web 検索より正確で最新のドキュメントを取得できる。

### 手順

1. `resolve-library-id` で対象ライブラリの ID を取得する
2. `get-library-docs` でドキュメントを取得する

### 利用例

```
# LilyPond の ly:make-pitch を調べる
resolve-library-id: "lilypond"
get-library-docs: <取得した ID>, topic="ly:make-pitch"

# Python mido ライブラリを調べる
resolve-library-id: "mido"
get-library-docs: <取得した ID>, topic="MidiFile ticks_per_beat"

# Guile Scheme の文字列関数を調べる
resolve-library-id: "guile"
get-library-docs: <取得した ID>, topic="string-tokenize"
```

---

## 新しいスケールの追加

`Scales/` に `.ly` ファイルを作成し、`translate-table` 形式のリストを定義する。

```lilypond
\version "2.24.4"
#(define my-scale '(
  (0 . -1) (1 . 0) (2 . 2) ...
))
```

楽譜ファイルで `\SetTranslateTable #my-scale` を呼んで使用する。

## ドキュメント調査に Context7 を使う

LilyPond・Python・Scheme の仕様を調べる際は、Context7 MCP を積極的に利用する。
Web 検索より正確で最新のドキュメントを取得できる。

### 手順

1. `resolve-library-id` で対象ライブラリの ID を取得する
2. `get-library-docs` でドキュメントを取得する

### 利用例

```
# LilyPond の ly:make-pitch を調べる
resolve-library-id: "lilypond"
get-library-docs: <取得した ID>, topic="ly:make-pitch"

# Python mido ライブラリを調べる
resolve-library-id: "mido"
get-library-docs: <取得した ID>, topic="MidiFile ticks_per_beat"

# Guile Scheme の文字列関数を調べる
resolve-library-id: "guile"
get-library-docs: <取得した ID>, topic="string-tokenize"
```

---

## 使用例

```lilypond
\include "Handpan.ily"
\include "Scales/Kurd9.ly"

\SetTranslateTable #kurd9

\score {
  \new Staff {
    \HandpanScore "1-4 2-8 [ 3-16 4-16 ] < 1-4 3-4 > R-4"
  }
}
```
