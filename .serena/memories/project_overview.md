# Handpan-Lilypond: Project Overview

## Purpose
LilyPond ライブラリ。ハンドパン専用の独自記法文字列（例: `"1-4 2^1!-8 R-4"`）を LilyPond の音楽オブジェクトへ変換する。作曲者はトーンフィールド番号ベースの簡潔な記法で楽譜を記述でき、LilyPond が五線譜に描画する。

## Tech Stack
- **LilyPond 2.24.4** + 組み込み **Scheme (Guile)**: メインライブラリ
- **Python 3.14+ / uv**: `midiToHandpanScore/` サブプロジェクト（MIDI → ハンドパン記法変換）
- **mido**: MIDI 読み込みライブラリ

## Entry Points
- LilyPond ライブラリとして使用: `.ly` ファイルで `\include "Handpan.ily"` → `\SetTranslateTable` → `\HandpanScore "..."` 
- MIDI → 楽譜変換: `cd midiToHandpanScore && uv run handpan-midi-to-score input.mid --scale d_kurd9`
- スケール定義ファイル生成: `cd midiToHandpanScore && uv run handpan-generate-scales`

## handpan-midi-to-score の主なオプション

| オプション | 説明 |
|---|---|
| `--scale` / `--handpan-set` | スケール名またはセット名（排他・必須） |
| `--min-duration DUR` | 最小音価（デフォルト: 32） |
| `--bars-per-chunk N` | 1チャンクあたりの小節数（デフォルト: 4） |
| `--output FILE` | 出力 .ly ファイルパス |
| `--normalize-minor` | ハーモニックマイナー・メロディックマイナーの音（長6度・長7度）をナチュラルマイナーへ丸める |

## 実装済みの主な機能（直近）

- タイ `~` による小節またぎサポート（cross-bar chord）
- テンポは MIDI から自動読み取り（`--tempo` オプション廃止）
- 複数音符トラックを持つ MIDI は拒否（`--track` オプション廃止）

## 実装済み: ノート間ギャップへの自動休符挿入

- `_emit_rests_and_bars` でギャップを `Rest`・`BarLine` に分解して挿入
