# Codebase Structure

```
Handpan-Lilypond/
├── Handpan.ily              # メインライブラリ（全 Scheme 関数）
├── Scales/
│   └── Kurd9.ly             # Kurd9 スケール定義（translate-table）
├── tests/
│   ├── Handpan-test.sh      # テスト実行スクリプト（bash）
│   ├── test-functions.ily   # test-ok / test-error / value-test ヘルパー
│   ├── utils/
│   │   ├── test-variables.ly
│   │   ├── utility-functions.ily
│   │   └── expected-articulation-note-list.ily
│   └── *-test.ly            # 各関数ごとのテストファイル（28個）
├── midiToHandpanScore/      # Python サブプロジェクト（MIDI → ハンドパン記法変換）
│   ├── src/miditohandpanscore/
│   │   ├── midi_to_score.py     # CLI: handpan-midi-to-score
│   │   ├── generate_scales.py   # CLI: handpan-generate-scales
│   │   ├── score_generator.py   # MidiData → トークン → .ly 生成
│   │   ├── midi_processing.py   # MIDI 読み込み・パース
│   │   ├── models.py            # HandpanScale / HandpanPart / HandpanSet / MidiNoteEvent
│   │   ├── quantize.py          # 音価量子化
│   │   ├── helpers.py           # ノート名→MIDI 変換等ユーティリティ
│   │   └── scales/
│   │       ├── __init__.py
│   │       └── data.py          # SCALES / SETS 定義辞書
│   ├── pyproject.toml
│   └── uv.lock
├── README.md                # 記法リファレンス（日本語）
└── CLAUDE.md                # Claude Code 向けドキュメント
```

## 主要関数の依存関係（Handpan.ily）

```
HandpanScore
└── handpan-score-internal
    ├── split-score          → トークン分割
    └── parse-token-list     → トークン → 音楽オブジェクトリスト
        ├── parse-block      → 連桁・和音ブロック検出
        ├── make-beam-group  → 連桁
        ├── make-chord-group → 和音
        ├── check-bar-line   → 小節線チェック
        └── parse-note-element
            ├── split-element
            └── parse-left-element
                ├── parse-note-type    → !アクセント / .ゴースト
                ├── parse-caret-numbers → ^ハーモニクス
                ├── pitch-translate    → トーンフィールド→音高
                └── make-custom-note
                    ├── make-base-note
                    └── make-duration-obj
```
