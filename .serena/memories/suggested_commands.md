# Suggested Commands

## テスト実行
```bash
cd /Users/chibioni/Github/Handpan-Lilypond/tests
bash Handpan-test.sh
```
全テスト（28ファイル）を順番に `lilypond` コマンドで実行。エラーがあれば即終了。

## 単一テストファイルの実行
```bash
cd /Users/chibioni/Github/Handpan-Lilypond/tests
lilypond split-score-test.ly
```

## LilyPond で楽譜を生成
```bash
lilypond my-score.ly
```
PDF と MIDI が生成される。

## Python サブプロジェクト（midiToHandpanScore）
```bash
cd /Users/chibioni/Github/Handpan-Lilypond/midiToHandpanScore
uv run python main.py
```

## Git
```bash
git status
git log --oneline -10
git diff
```

## ファイル検索
```bash
grep -r "関数名" /Users/chibioni/Github/Handpan-Lilypond/
find . -name "*.ly" -o -name "*.ily"
```
