"""handpan-midi-to-score CLI."""

import argparse
import sys
from pathlib import Path

from .ly_writer import generate_score_ly, generate_set_score_ly
from .midi_processing import read_midi
from .scales.data import SCALES, SETS
from .score_generator import events_to_tokens, events_to_tokens_per_part


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数をパースして argparse.Namespace を返す。

    Args:
        argv: パース対象の引数リスト。None の場合は sys.argv を使用する。

    Returns:
        パース結果の argparse.Namespace。
    """
    parser = argparse.ArgumentParser(prog="handpan-midi-to-score")
    parser.add_argument("input", metavar="input.mid", help="入力 MIDI ファイル")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scale", metavar="SCALE_NAME", help="スケール名 (例: d_kurd9)")
    mode.add_argument("--handpan-set", metavar="SET_NAME", help="ハンドパンセット名 (例: f_sharp_minor18)")

    parser.add_argument("--output", metavar="FILE", help="出力 .ly ファイルパス")
    parser.add_argument("--min-duration", default="32", metavar="DUR", help="最小音価 (デフォルト: 32)")
    parser.add_argument("--bars-per-chunk", type=int, default=4, metavar="N", help="チャンクあたりの小節数")
    parser.add_argument(
        "--normalize-minor",
        action="store_true",
        help="ハーモニックマイナー・メロディックマイナーの音をナチュラルマイナーへ丸める",
    )

    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    """パース済み引数を受け取り、MIDI → LilyPond 変換を実行して .ly ファイルを出力する。

    Args:
        args: parse_args の戻り値。

    Raises:
        SystemExit: 入力ファイルが存在しない、スケール/セット名が未登録、
            または --bars-per-chunk が 0 以下の場合。
    """
    if args.bars_per_chunk <= 0:
        print("[ERROR] --bars-per-chunk must be a positive integer", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".ly")

    midi_data = read_midi(input_path)

    bpm = round(60_000_000 / midi_data.tempo_changes[0].tempo)
    print(f"[INFO] Tempo: {bpm} BPM", file=sys.stderr)

    if args.scale:
        if args.scale not in SCALES:
            print(f"[ERROR] Scale not found: {args.scale}", file=sys.stderr)
            sys.exit(1)
        scale = SCALES[args.scale]
        tokens = events_to_tokens(midi_data, scale, args.min_duration, args.normalize_minor)
        content = generate_score_ly(tokens, scale, args.bars_per_chunk)
    else:
        if args.handpan_set not in SETS:
            print(f"[ERROR] Handpan set not found: {args.handpan_set}", file=sys.stderr)
            sys.exit(1)
        handpan_set = SETS[args.handpan_set]
        part_tokens = events_to_tokens_per_part(midi_data, handpan_set, args.min_duration, args.normalize_minor)
        content = generate_set_score_ly(part_tokens, handpan_set, args.bars_per_chunk)

    output_path.write_text(content, encoding="utf-8")
    print(f"[INFO] Generated: {output_path}", file=sys.stderr)


def main() -> None:
    """CLI エントリポイント。引数をパースして run() に委譲する。"""
    run(parse_args())
