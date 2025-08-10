#!/bin/bash

# lilypond 実行ファイルのパス（必要に応じて修正）
LILYPOND_CMD="lilypond"

# エラーがあれば即終了
set -e

# .ly ファイルを処理する配列（順番に実行）
FILES=(
    "split-score-test.ly"
    "check-bar-line-test.ly"
    "make-duration-obj-test.ly"
    "make-rest-note-test.ly"
    "make-hide-rest-note-test.ly"
    "split-element-test.ly"
    "caret-position-test.ly"
    "parse-caret-numbers-test.ly"
    "translate-table-test.ly"
    "pitch-translate-test.ly"
    "handpan-type-test.ly"
    "parse-note-type-test.ly"
    "make-base-note-test.ly"
    "note-event?-test.ly"
    "note-event-list?-test.ly"
    "make-chord-group-test.ly"
    "make-custom-note-test.ly"
    "parse-left-element-test.ly"
    "parse-note-element-test.ly"
    "parse-block-test.ly"
    "parse-token-list-test.ly"
    "handpan-score-internal-test.ly"
    "bar-check?-test.ly"
    "rest-event?-test.ly"
    "skip-event?-test.ly"
    "playable-event?-test.ly"
    "playable-event-list?-test.ly"
    "add-articulation-to-last-test.ly"
    "make-beam-group-test.ly"
)

# 処理開始
echo "Starting LilyPond batch processing..."

for file in "${FILES[@]}"; do
  echo "Processing: $file"
  if [ -f "$file" ]; then
    $LILYPOND_CMD "$file"
  else
    echo "File not found: $file" >&2
    exit 1
  fi
done

echo "All files processed successfully."
