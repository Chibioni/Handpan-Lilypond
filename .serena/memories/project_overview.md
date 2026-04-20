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
