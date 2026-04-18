# Task Completion Checklist

タスク完了時に行うべき手順:

## 新しい関数を追加した場合
1. `Handpan.ily` に関数を追加
2. `tests/` に `関数名-test.ly` を作成（`test-ok` / `test-error` 使用）
3. `tests/Handpan-test.sh` の `FILES` 配列にテストファイル名を追加
4. `cd tests && bash Handpan-test.sh` でテスト実行・全件パス確認

## 既存関数を修正した場合
1. 該当する `-test.ly` ファイルを更新（または新規テスト追加）
2. `cd tests && bash Handpan-test.sh` でテスト実行・全件パス確認

## 新しいスケールを追加した場合
1. `Scales/スケール名.ly` を作成
2. README.md の記法表に追記（必要なら）

## テスト実行コマンド
```bash
cd /Users/chibioni/Github/Handpan-Lilypond/tests
bash Handpan-test.sh
```

## 注意事項
- LilyPond はコンパイル時に Scheme を実行するため、テストは `lilypond` コマンド経由で走る
- テスト失敗時は stderr に出力される；`set -e` により最初の失敗で停止
- フォーマッターやリンターは現時点では未設定
