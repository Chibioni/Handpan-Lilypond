"""handpan-generate-scales CLI."""

import argparse
import sys
from pathlib import Path

from .models import HandpanScale, HandpanSet
from .scales.data import SCALES, ENSEMBLES

_COLS = 3


def _format_pairs(pairs: list[tuple[int, int]]) -> str:
    lines = []
    for i in range(0, len(pairs), _COLS):
        chunk = pairs[i:i + _COLS]
        lines.append("  " + " ".join(f"({tf} . {n:2d})" for tf, n in chunk))
    return "\n".join(lines)


def generate_scale_ly(scale: HandpanScale) -> str:
    pitches = scale.ly_pitches
    pairs = list(enumerate(pitches))
    return (
        f'\\version "2.24.4"\n\n'
        f"% {scale.name} スケール定義\n"
        f"% トーンフィールド番号と LilyPond 音高整数の対応表\n"
        f"#(define {scale.ly_name} '(\n"
        f"{_format_pairs(pairs)}\n"
        f"))\n"
        f'#(define {scale.ly_name}-key-signature "{scale.key_signature}")\n'
    )


def generate_ensemble_ly(ensemble: HandpanSet) -> str:
    lines = [
        '\\version "2.24.4"\n',
        f"% {ensemble.name} アンサンブル定義",
    ]
    for i, part in enumerate(ensemble.parts):
        pitches = ensemble.part_ly_pitches(i)
        pairs = list(enumerate(pitches))
        lines.append(f"#(define {part.instrument_name} '(")
        lines.append(_format_pairs(pairs))
        lines.append("))")
    lines.append(f'#(define {ensemble.name}-key-signature "{ensemble.key_signature}")\n')
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(prog="handpan-generate-scales")
    parser.add_argument("--scale", metavar="SCALE_NAME", help="生成するスケール名")
    parser.add_argument("--output-dir", metavar="DIR", default="../Scales", help="出力先ディレクトリ（省略時: ../Scales/）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    targets: list[tuple[str, str]] = []

    if args.scale:
        key = args.scale
        if key in SCALES:
            targets.append(("scale", key))
        elif key in ENSEMBLES:
            targets.append(("ensemble", key))
        else:
            print(f"[ERROR] Scale not found: {key}", file=sys.stderr)
            sys.exit(1)
    else:
        for key in SCALES:
            targets.append(("scale", key))
        for key in ENSEMBLES:
            targets.append(("ensemble", key))

    output_dir.mkdir(parents=True, exist_ok=True)

    for kind, key in targets:
        if kind == "scale":
            scale = SCALES[key]
            content = generate_scale_ly(scale)
            out_path = output_dir / f"{scale.name}.ly"
        else:
            ensemble = ENSEMBLES[key]
            content = generate_ensemble_ly(ensemble)
            out_path = output_dir / f"{ensemble.name}.ly"

        out_path.write_text(content, encoding="utf-8")
        print(f"[INFO] Generated: {out_path}", file=sys.stderr)
