"""generate_scales.py と helpers.py のテスト。"""

import argparse
from pathlib import Path

import pytest

from miditohandpanscore.generate_scales import (
    _format_pairs,
    generate_scale_ly,
    generate_set_ly,
    parse_args,
    run,
)
from miditohandpanscore.models import HandpanPart, HandpanScale, HandpanSet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kurd9() -> HandpanScale:
    return HandpanScale(
        scale_family="Kurd",
        note_names=["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"],
        key_signature="d \\minor",
    )


@pytest.fixture
def two_part_set() -> HandpanSet:
    scale_a = HandpanScale("Kurd", ["D3", "A3", "C4"], "d \\minor")
    scale_b = HandpanScale("Kurd", ["E3", "G3", "B3"], "d \\minor")
    return HandpanSet(
        scale_family="Kurd",
        parts=[HandpanPart("PartA", scale_a), HandpanPart("PartB", scale_b)],
        key_signature="d \\minor",
    )


def make_run_args(**kwargs) -> argparse.Namespace:
    defaults = dict(scale=None, output_dir=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _format_pairs
# ---------------------------------------------------------------------------

class TestFormatPairs:
    def test_single_row(self):
        pairs = [(0, -1), (1, 1), (2, 2)]
        result = _format_pairs(pairs)
        assert result == "  (0 . -1) (1 .  1) (2 .  2)"

    def test_wraps_at_three_cols(self):
        pairs = [(i, i) for i in range(4)]
        lines = _format_pairs(pairs).splitlines()
        assert len(lines) == 2

    def test_exact_three_cols_one_row(self):
        pairs = [(0, 1), (1, 2), (2, 3)]
        lines = _format_pairs(pairs).splitlines()
        assert len(lines) == 1

    def test_empty_pairs(self):
        assert _format_pairs([]) == ""


# ---------------------------------------------------------------------------
# generate_scale_ly
# ---------------------------------------------------------------------------

class TestGenerateScaleLy:
    def test_version_header(self, kurd9):
        assert '\\version "2.24.4"' in generate_scale_ly(kurd9)

    def test_define_statement(self, kurd9):
        content = generate_scale_ly(kurd9)
        assert f"#(define {kurd9.ly_name} '(" in content

    def test_key_signature_line(self, kurd9):
        content = generate_scale_ly(kurd9)
        assert f'#(define {kurd9.ly_name}-key-signature "d \\minor")' in content

    def test_ding_is_tf0_with_n_minus1(self, kurd9):
        # TF0（Ding）は N値 = -1
        content = generate_scale_ly(kurd9)
        assert "(0 . -1)" in content

    def test_note_count_matches_scale(self, kurd9):
        # 9音: 3行 × 3列
        content = generate_scale_ly(kurd9)
        tf_count = sum(1 for line in content.splitlines() for _ in [line] if "(" in line and ". " in line)
        assert tf_count == 3


# ---------------------------------------------------------------------------
# generate_set_ly
# ---------------------------------------------------------------------------

class TestGenerateSetLy:
    def test_version_header(self, two_part_set):
        assert '\\version "2.24.4"' in generate_set_ly(two_part_set)

    def test_both_parts_defined(self, two_part_set):
        content = generate_set_ly(two_part_set)
        assert "#(define PartA '(" in content
        assert "#(define PartB '(" in content

    def test_key_signature_line(self, two_part_set):
        content = generate_set_ly(two_part_set)
        assert '-key-signature "d \\minor"' in content


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_no_args_scale_is_none(self):
        args = parse_args([])
        assert args.scale is None

    def test_scale_arg(self):
        args = parse_args(["--scale", "d_kurd9"])
        assert args.scale == "d_kurd9"

    def test_default_output_dir(self):
        args = parse_args([])
        assert args.output_dir == "../Scales"

    def test_custom_output_dir(self):
        args = parse_args(["--output-dir", "/tmp/out"])
        assert args.output_dir == "/tmp/out"


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

class TestRun:
    def test_generates_scale_ly_file(self, tmp_path):
        run(make_run_args(scale="d_kurd9", output_dir=str(tmp_path)))
        assert len(list(tmp_path.glob("*.ly"))) == 1

    def test_scale_file_content(self, tmp_path):
        run(make_run_args(scale="d_kurd9", output_dir=str(tmp_path)))
        content = next(tmp_path.glob("*.ly")).read_text()
        assert '\\version "2.24.4"' in content
        assert "d_kurd9" in content

    def test_generates_ensemble_ly_file(self, tmp_path):
        run(make_run_args(scale="f_sharp_minor18", output_dir=str(tmp_path)))
        assert len(list(tmp_path.glob("*.ly"))) == 1

    def test_all_scales_generated_when_no_scale_arg(self, tmp_path):
        from miditohandpanscore.scales.data import SCALES, SETS
        run(make_run_args(scale=None, output_dir=str(tmp_path)))
        assert len(list(tmp_path.glob("*.ly"))) == len(SCALES) + len(SETS)

    def test_unknown_scale_exits(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            run(make_run_args(scale="unknown", output_dir=str(tmp_path)))
        assert "[ERROR]" in capsys.readouterr().err

    def test_output_dir_created_if_missing(self, tmp_path):
        nested = tmp_path / "a" / "b"
        run(make_run_args(scale="d_kurd9", output_dir=str(nested)))
        assert nested.exists()

    def test_info_in_stderr(self, tmp_path, capsys):
        run(make_run_args(scale="d_kurd9", output_dir=str(tmp_path)))
        assert "[INFO] Generated:" in capsys.readouterr().err

