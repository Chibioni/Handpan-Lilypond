"""midi_to_score.py (CLI) のテスト。

parse_args() と run() を直接呼び出す。
統合テスト (TestIntegration*) は d_kurd9.mid フィクスチャを使い、
生成された .ly ファイルの内容まで検証する。
"""

import argparse
from pathlib import Path

import pytest

from miditohandpanscore.midi_to_score import parse_args, run

FIXTURE_MID = Path(__file__).parent / "fixtures" / "d_kurd9.mid"
FIXTURE_NORMALIZE_MID = Path(__file__).parent / "fixtures" / "normalize_minor.mid"


def make_args(**kwargs) -> argparse.Namespace:
    """run() に渡す Namespace を手動で組み立てるヘルパー。"""
    defaults = dict(
        input=str(FIXTURE_MID),
        scale="d_kurd9",
        ensemble=None,
        output=None,
        min_duration="32",
        bars_per_chunk=4,
        normalize_minor=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_scale_mode(self):
        args = parse_args([str(FIXTURE_MID), "--scale", "d_kurd9"])
        assert args.scale == "d_kurd9"
        assert args.ensemble is None

    def test_ensemble_mode(self):
        args = parse_args([str(FIXTURE_MID), "--ensemble", "f_sharp_minor18"])
        assert args.ensemble == "f_sharp_minor18"
        assert args.scale is None

    def test_scale_and_ensemble_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            parse_args([str(FIXTURE_MID), "--scale", "d_kurd9", "--ensemble", "f_sharp_minor18"])

    def test_missing_scale_and_ensemble(self):
        with pytest.raises(SystemExit):
            parse_args([str(FIXTURE_MID)])

    def test_missing_input(self):
        with pytest.raises(SystemExit):
            parse_args(["--scale", "d_kurd9"])

    def test_default_bars_per_chunk(self):
        args = parse_args([str(FIXTURE_MID), "--scale", "d_kurd9"])
        assert args.bars_per_chunk == 4

    def test_default_min_duration(self):
        args = parse_args([str(FIXTURE_MID), "--scale", "d_kurd9"])
        assert args.min_duration == "32"

    def test_normalize_minor_default_false(self):
        args = parse_args([str(FIXTURE_MID), "--scale", "d_kurd9"])
        assert args.normalize_minor is False

    def test_normalize_minor_flag(self):
        args = parse_args([str(FIXTURE_MID), "--scale", "d_kurd9", "--normalize-minor"])
        assert args.normalize_minor is True


# ---------------------------------------------------------------------------
# run — --scale モード
# ---------------------------------------------------------------------------

class TestRunScaleMode:
    def test_generates_ly_file(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(output=str(out)))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_contains_version_header(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(output=str(out)))
        assert '\\version "2.24.4"' in out.read_text()

    def test_output_contains_handpan_score(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(output=str(out)))
        assert "\\HandpanScore" in out.read_text()

    def test_default_output_path_uses_ly_suffix(self, tmp_path):
        import shutil
        mid = tmp_path / "d_kurd9.mid"
        shutil.copy(FIXTURE_MID, mid)
        run(make_args(input=str(mid)))
        assert (tmp_path / "d_kurd9.ly").exists()

    def test_unknown_scale_exits(self, tmp_path):
        out = tmp_path / "out.ly"
        with pytest.raises(SystemExit):
            run(make_args(scale="unknown_scale", output=str(out)))

    def test_tempo_in_stderr(self, tmp_path, capsys):
        out = tmp_path / "out.ly"
        run(make_args(output=str(out)))
        err = capsys.readouterr().err
        assert "120 BPM" in err

    def test_bars_per_chunk_splits_output(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(bars_per_chunk=2, output=str(out)))
        assert out.read_text().count("\\HandpanScore") == 2


# ---------------------------------------------------------------------------
# run — --ensemble モード
# ---------------------------------------------------------------------------

class TestRunEnsembleMode:
    def test_generates_ly_file(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(scale=None, ensemble="f_sharp_minor18", output=str(out)))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_contains_simultaneous_block(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(scale=None, ensemble="f_sharp_minor18", output=str(out)))
        content = out.read_text()
        assert "<<" in content
        assert ">>" in content

    def test_unknown_ensemble_exits(self, tmp_path):
        out = tmp_path / "out.ly"
        with pytest.raises(SystemExit):
            run(make_args(scale=None, ensemble="unknown_set", output=str(out)))


# ---------------------------------------------------------------------------
# run — バリデーション
# ---------------------------------------------------------------------------

class TestRunValidation:
    def test_nonexistent_input_exits(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            run(make_args(input=str(tmp_path / "nonexistent.mid")))
        assert "[ERROR]" in capsys.readouterr().err

    def test_bars_per_chunk_zero_exits(self, tmp_path, capsys):
        out = tmp_path / "out.ly"
        with pytest.raises(SystemExit):
            run(make_args(bars_per_chunk=0, output=str(out)))
        assert "[ERROR]" in capsys.readouterr().err

    def test_bars_per_chunk_negative_exits(self, tmp_path, capsys):
        out = tmp_path / "out.ly"
        with pytest.raises(SystemExit):
            run(make_args(bars_per_chunk=-1, output=str(out)))
        assert "[ERROR]" in capsys.readouterr().err

    def test_generated_info_in_stderr(self, tmp_path, capsys):
        out = tmp_path / "out.ly"
        run(make_args(output=str(out)))
        assert "[INFO] Generated:" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# 統合テスト — d_kurd9.mid フィクスチャで生成内容を検証
# ---------------------------------------------------------------------------

# generate_d_kurd9.py の設計から導出した期待トークン列（test_score_generator.py と共通）
EXPECTED_TOKENS = [
    "0-4", "1!-4", "2.-4.", "3-8",       # 小節1
    "O0-4", "S5-4", "6-8.", "7-8..",     # 小節2
    "2^1-4", "3^1-4", "5^2-4.", "6^2-8", # 小節3
    "4-2", "8-4..",                        # 小節4
]


@pytest.fixture
def kurd9_ly(tmp_path) -> str:
    """d_kurd9.mid を d_kurd9 スケールで変換した .ly 内容を返す。"""
    out = tmp_path / "out.ly"
    run(make_args(output=str(out)))
    return out.read_text()


class TestIntegrationScaleMode:
    def test_all_tokens_present(self, kurd9_ly):
        for token in EXPECTED_TOKENS:
            assert token in kurd9_ly, f"token {token!r} が出力に含まれていない"

    def test_bar_line_count(self, kurd9_ly):
        # 4小節 → \\| が 3 回
        assert kurd9_ly.count("|") == 3

    def test_scale_include(self, kurd9_ly):
        assert '\\include "../Scales/D_Kurd9.ly"' in kurd9_ly

    def test_translate_table(self, kurd9_ly):
        assert "\\SetTranslateTable #d_kurd9" in kurd9_ly

    def test_bars_per_chunk_4_single_block(self, tmp_path):
        # デフォルト 4小節/チャンク → 全4小節が 1 ブロックに収まる
        out = tmp_path / "out.ly"
        run(make_args(bars_per_chunk=4, output=str(out)))
        assert out.read_text().count("\\HandpanScore") == 1

    def test_bars_per_chunk_2_two_blocks(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(bars_per_chunk=2, output=str(out)))
        assert out.read_text().count("\\HandpanScore") == 2

    def test_bars_per_chunk_1_four_blocks(self, tmp_path):
        out = tmp_path / "out.ly"
        run(make_args(bars_per_chunk=1, output=str(out)))
        assert out.read_text().count("\\HandpanScore") == 4


# ---------------------------------------------------------------------------
# 統合テスト — normalize_minor.mid フィクスチャで --normalize-minor を検証
#
# normalize_minor.mid の設計（D Kurd 9、120BPM、4/4、1小節）:
#   tick=0:    D4(62)  Q → TF4        通常スケール音
#   tick=480:  C#4(61) Q → TF3        raised 7th（normalize 時）
#   tick=960:  B♮4(71) Q → TF2^1      raised 6th（normalize 時）
#   tick=1440: C#5(73) Q → TF3^1      raised 7th 高音域（normalize 時）
# ---------------------------------------------------------------------------

NM_INPUT = str(FIXTURE_NORMALIZE_MID)


class TestIntegrationNormalizeMinor:
    def test_raised_7th_mapped_with_flag(self, tmp_path: Path) -> None:
        out = tmp_path / "out.ly"
        run(make_args(input=NM_INPUT, normalize_minor=True, output=str(out)))
        assert "3-4" in out.read_text()

    def test_raised_6th_mapped_with_flag(self, tmp_path: Path) -> None:
        out = tmp_path / "out.ly"
        run(make_args(input=NM_INPUT, normalize_minor=True, output=str(out)))
        assert "2^1-4" in out.read_text()

    def test_raised_7th_high_octave_mapped_with_flag(self, tmp_path: Path) -> None:
        out = tmp_path / "out.ly"
        run(make_args(input=NM_INPUT, normalize_minor=True, output=str(out)))
        assert "3^1-4" in out.read_text()

    def test_normal_note_present_regardless_of_flag(self, tmp_path: Path) -> None:
        for flag in (True, False):
            out = tmp_path / f"out_{flag}.ly"
            run(make_args(input=NM_INPUT, normalize_minor=flag, output=str(out)))
            assert "4-4" in out.read_text()

    def test_raised_notes_skipped_without_flag(self, tmp_path: Path) -> None:
        out = tmp_path / "out.ly"
        run(make_args(input=NM_INPUT, normalize_minor=False, output=str(out)))
        content = out.read_text()
        # raised notes はスケール外なのでトークンが出力されない
        assert "3-4" not in content
        assert "2^1-4" not in content
        assert "3^1-4" not in content
