# Style and Conventions

## LilyPond / Scheme (Handpan.ily)

- **言語**: LilyPond 2.24.4 + 組み込み Scheme (Guile)
- **コメント**: `%` で始まる行コメント（Scheme 内は `;`）
- **関数名**: `kebab-case`（例: `parse-note-element`, `make-beam-group`）
- **定数名**: `SCREAMING-KEBAB-CASE`（例: `HANDPAN-TYPE-NORMAL`, `HANDPAN-TYPE-ACCENT`）
- **テスト注記**: 各関数定義の直前に `% テスト書いた` コメントを付ける慣習

## テストの書き方

`tests/test-functions.ily` で定義された3つのヘルパーを使う:

```scheme
; 正常系テスト: 関数・テストケースリストを渡す
(test-ok func '(
  ((arg1 arg2) . expected-result)
  ...
))

; エラー系テスト: エラーが発生することを確認
(test-error func '(
  (bad-arg1 bad-arg2)
  ...
))

; 単一値テスト
(value-test actual-value expected-value)
```

各テストファイルは `tests/` ディレクトリに `関数名-test.ly` という命名規則で配置する。

## スケール定義（Scales/）

```scheme
#(define scale-name '(
  (tone-field-number . pitch-integer)
  ...
))
```
`pitch-integer` は LilyPond の `ly:make-pitch 0 N NATURAL` の `N` に対応する整数。

## Python (midiToHandpanScore)

- Python 3.14+、uv でパッケージ管理
- コードスタイル: まだ初期段階のため未確立
