"""score_generator.py の高レベル関数のテスト。

d_kurd9.mid フィクスチャ（generate_d_kurd9.py で生成）を使用。

D Kurd 9: D3=50(TF0) A3=57(TF1) Bb3=58(TF2) C4=60(TF3)
          D4=62(TF4) E4=64(TF5) F4=65(TF6) G4=67(TF7) A4=69(TF8)
"""

from pathlib import Path

import pytest

from miditohandpanscore.midi_processing import MidiData, TempoChange, TimeSignatureChange, read_midi
from miditohandpanscore.models import HandpanPart, HandpanScale, HandpanSet, MidiNoteEvent
from miditohandpanscore.scales.data import SCALES, SETS
from miditohandpanscore.score_generator import (
    events_to_tokens,
    events_to_tokens_per_part,
    generate_score_ly,
    generate_set_score_ly,
)

FIXTURE_MID = Path(__file__).parent / "fixtures" / "d_kurd9.mid"
TPB = 480
Q = TPB
H = TPB * 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_event(midi_note: int, tick_start: int, duration: int, velocity: int = 64) -> MidiNoteEvent:
    return MidiNoteEvent(
        midi_note=midi_note,
        tick_start=tick_start,
        tick_end=tick_start + duration,
        velocity=velocity,
    )


def make_midi_data(
    events: list[MidiNoteEvent],
    ticks_per_beat: int = TPB,
    numerator: int = 4,
    denominator: int = 4,
) -> MidiData:
    return MidiData(
        ticks_per_beat=ticks_per_beat,
        events=events,
        tempo_changes=[TempoChange(tick=0, tempo=500_000)],
        time_sig_changes=[TimeSignatureChange(tick=0, numerator=numerator, denominator=denominator)],
    )


@pytest.fixture
def kurd9() -> HandpanScale:
    return SCALES["d_kurd9"]


@pytest.fixture
def midi_data() -> MidiData:
    return read_midi(FIXTURE_MID)


# ---------------------------------------------------------------------------
# events_to_tokens — フィクスチャ MIDI を使った統合テスト
# ---------------------------------------------------------------------------

# generate_d_kurd9.py のコメントから導出した期待トークン列
EXPECTED_TOKENS = [
    # 小節1: 通常ノート + アーティキュレーション
    "0-4",    # D3  vel=64  通常
    "1!-4",   # A3  vel=127 アクセント
    "2.-4.",  # Bb3 vel=20  ゴースト 付点4分
    "3-8",    # C4  vel=64  通常 8分
    "\\|",
    # 小節2: 奏法マーカー + 付点・二重付点
    "O0-4",   # D3 + Apex リング打奏
    "S5-4",   # E4 + スラップ
    "6-8.",   # F4 付点8分
    "7-8..",  # G4 二重付点8分
    "\\|",
    # 小節3: ハーモニクス
    "2^1-4",  # Bb4 = Bb3+12 ハーモニクス1
    "3^1-4",  # C5  = C4+12  ハーモニクス1
    "2^2-4.", # F5  = Bb3+19 ハーモニクス2 付点4分
    "3^2-8",  # G5  = C4+19  ハーモニクス2
    "\\|",
    # 小節4: 残りのスケール音
    "4-2",    # D4 2分音符
    "8-4..",  # A4 二重付点4分 (840ticks = 1.75beats)
]


class TestEventsToTokensFromFixture:
    def test_full_token_list(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        assert tokens == EXPECTED_TOKENS

    def test_bar_line_count(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        assert tokens.count("\\|") == 3

    def test_bar1_articulation(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        bar1 = tokens[: tokens.index("\\|")]
        assert "1!-4" in bar1   # アクセント
        assert "2.-4." in bar1  # ゴースト

    def test_bar2_techniques(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        bars = [t for t in tokens if t != "\\|"]
        bar2_start = tokens.index("\\|") + 1
        bar2_end = tokens.index("\\|", bar2_start)
        bar2 = tokens[bar2_start:bar2_end]
        assert "O0-4" in bar2
        assert "S5-4" in bar2

    def test_bar3_harmonics(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        separators = [i for i, t in enumerate(tokens) if t == "\\|"]
        bar3 = tokens[separators[1] + 1 : separators[2]]
        assert "2^1-4" in bar3
        assert "3^1-4" in bar3
        assert "2^2-4." in bar3
        assert "3^2-8" in bar3

    def test_bar4_durations(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        bar_indices = [i for i, t in enumerate(tokens) if t == "\\|"]
        bar4 = tokens[bar_indices[-1] + 1:]
        assert "4-2" in bar4    # 2分音符
        assert "8-4.." in bar4  # 二重付点4分


# ---------------------------------------------------------------------------
# events_to_tokens — min_duration フィルタ
# ---------------------------------------------------------------------------

class TestEventsToTokensMinDuration:
    def test_default_min_duration_32nd(self, kurd9):
        # 32分音符（0.125 beats）はデフォルトで通過する
        events = [make_event(57, 0, TPB // 8)]  # 60 ticks = 0.125 beats
        tokens = events_to_tokens(make_midi_data(events), kurd9, min_duration="32")
        assert tokens != []

    def test_min_duration_filters_short_note(self, kurd9, capsys):
        # 8分音符の長さで min_duration="4"（1 beat）を指定 → スキップ
        events = [make_event(57, 0, Q // 2)]
        tokens = events_to_tokens(make_midi_data(events), kurd9, min_duration="4")
        assert tokens == []
        assert "[WARN]" in capsys.readouterr().err

    def test_unknown_min_duration_exits(self, kurd9):
        events = [make_event(57, 0, Q)]
        with pytest.raises(SystemExit):
            events_to_tokens(make_midi_data(events), kurd9, min_duration="99")


# ---------------------------------------------------------------------------
# events_to_tokens_per_part — 手動構築 MidiData でテスト
# ---------------------------------------------------------------------------

@pytest.fixture
def two_part_set() -> HandpanSet:
    # PartA: D4(62), A4(69)  /  PartB: A3(57), E4(64)
    scale_a = HandpanScale("Kurd", ["D4", "A4"], "d \\minor")
    scale_b = HandpanScale("Kurd", ["A3", "E4"], "d \\minor")
    return HandpanSet(
        scale_family="Kurd",
        parts=[HandpanPart("PartA", scale_a), HandpanPart("PartB", scale_b)],
        key_signature="d \\minor",
    )


class TestEventsToTokensPerPart:
    def test_note_routed_to_part_a(self, two_part_set):
        events = [make_event(62, 0, Q)]  # D4 = PartA のみ
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert "H-" not in part_tokens[0][0]   # PartA に実音
        assert part_tokens[1][0].startswith("H-")  # PartB は非表示休符

    def test_note_routed_to_part_b(self, two_part_set):
        events = [make_event(57, 0, Q)]  # A3 = PartB のみ
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert part_tokens[0][0].startswith("H-")  # PartA は非表示休符
        assert "H-" not in part_tokens[1][0]        # PartB に実音

    def test_simultaneous_notes_split(self, two_part_set):
        events = [make_event(62, 0, Q), make_event(57, 0, Q)]  # 同 tick: PartA + PartB
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert "H-" not in part_tokens[0][0]
        assert "H-" not in part_tokens[1][0]

    def test_hidden_rest_matches_chord_duration(self, two_part_set):
        events = [make_event(62, 0, H)]  # D4 = PartA, 2分音符
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert part_tokens[1][0] == "H-2"

    def test_bar_lines_in_all_parts(self, two_part_set):
        events = [
            make_event(62, 0,        Q),
            make_event(57, Q * 4,    Q),  # 次の小節
        ]
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert "\\|" in part_tokens[0]
        assert "\\|" in part_tokens[1]

    def test_note_in_neither_part_skipped(self, two_part_set: HandpanSet, capsys: pytest.CaptureFixture[str]) -> None:
        events = [make_event(99, 0, Q)]  # どのパートにも属さない MIDI 99
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert part_tokens == [[], []]
        assert "[WARN]" in capsys.readouterr().err

    def test_min_duration_filters_short_note(self, two_part_set: HandpanSet, capsys: pytest.CaptureFixture[str]) -> None:
        events = [make_event(62, 0, Q // 2)]  # D4、8分音符 < min_duration="4"
        part_tokens = events_to_tokens_per_part(
            make_midi_data(events), two_part_set, min_duration="4"
        )
        assert part_tokens == [[], []]
        assert "[WARN]" in capsys.readouterr().err

    def test_technique_marker_applied_to_correct_part(self, two_part_set: HandpanSet) -> None:
        # MIDI 0 (Apex) + D4(62) → PartA に "O0-4"、PartB は非表示休符
        events = [make_event(0, 0, Q), make_event(62, 0, Q)]
        part_tokens = events_to_tokens_per_part(make_midi_data(events), two_part_set)
        assert part_tokens[0][0] == "O0-4"
        assert part_tokens[1][0].startswith("H-")


# ---------------------------------------------------------------------------
# generate_score_ly
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# normalize_minor オプション
# ---------------------------------------------------------------------------

# D Kurd 9 のルートは D3(MIDI 50)。
# 上昇7度: C#4 (MIDI 61) → C4 (MIDI 60) = TF3 基音
# 上昇6度: B♮4 (MIDI 71) → Bb4 (MIDI 70) = TF2 ハーモニクス1

class TestNormalizeMinorEventsToTokens:
    def test_raised_7th_mapped_to_natural(self, kurd9):
        events = [make_event(61, 0, Q)]  # C#4 → C4(TF3)
        tokens = events_to_tokens(make_midi_data(events), kurd9, normalize_minor=True)
        assert tokens == ["3-4"]

    def test_raised_6th_mapped_to_harmonic(self, kurd9):
        events = [make_event(71, 0, Q)]  # B♮4 → Bb4 harmonic1(TF2^1)
        tokens = events_to_tokens(make_midi_data(events), kurd9, normalize_minor=True)
        assert tokens == ["2^1-4"]

    def test_raised_note_skipped_without_flag(self, kurd9, capsys):
        events = [make_event(61, 0, Q)]  # C#4: スケールにない
        tokens = events_to_tokens(make_midi_data(events), kurd9, normalize_minor=False)
        assert tokens == []
        assert "[WARN]" in capsys.readouterr().err

    def test_normal_notes_unaffected(self, kurd9):
        events = [make_event(60, 0, Q)]  # C4(TF3): 正規化の有無で変わらない
        tokens_with = events_to_tokens(make_midi_data(events), kurd9, normalize_minor=True)
        tokens_without = events_to_tokens(make_midi_data(events), kurd9, normalize_minor=False)
        assert tokens_with == tokens_without == ["3-4"]

    def test_raised_note_no_natural_in_scale_skipped(self, kurd9, capsys):
        # E Kurd 9 など C# がナチュラルマイナーにある場合は別だが、
        # D Kurd 9 の D+9=B♮ は Bb がスケールにあるので写像される。
        # 逆に写像先がスケールにない例として、TF 存在しない MIDI 番号を直接検証。
        # ここでは「上昇7度だが 1半音下もスケールにない」状況を手動構築する。
        scale_no_c = HandpanScale("Test", ["D4", "E4", "F4"], "d \\minor")
        # D4 root (PC=2): 上昇7度 = C#5 (MIDI 73), 自然7度 = C5 (MIDI 72)
        # C5 は scale_no_c に含まれない → スキップ
        events = [make_event(73, 0, Q)]
        tokens = events_to_tokens(make_midi_data(events), scale_no_c, normalize_minor=True)
        assert tokens == []
        assert "[WARN]" in capsys.readouterr().err


@pytest.fixture
def normalize_minor_set() -> HandpanSet:
    # PartA: D4(62), C4(60)  ← D root、C はナチュラル7度
    # PartB: A3(57), G3(55)  ← A root、G はナチュラル7度
    # → PartA の C#4(61) は C4(60) に正規化されて PartA へ
    scale_a = HandpanScale("Test", ["D4", "C4"], "d \\minor")
    scale_b = HandpanScale("Test", ["A3", "G3"], "a \\minor")
    return HandpanSet(
        scale_family="Test",
        parts=[HandpanPart("PartA", scale_a), HandpanPart("PartB", scale_b)],
        key_signature="d \\minor",
    )


class TestNormalizeMinorEventsToTokensPerPart:
    def test_raised_note_routed_to_correct_part(self, normalize_minor_set):
        # C#4(61) → C4(60) = PartA TF1
        events = [make_event(61, 0, Q)]
        part_tokens = events_to_tokens_per_part(
            make_midi_data(events), normalize_minor_set, normalize_minor=True
        )
        assert "H-" not in part_tokens[0][0]       # PartA に実音
        assert part_tokens[1][0].startswith("H-")  # PartB は非表示休符

    def test_raised_note_skipped_without_flag(self, normalize_minor_set, capsys):
        # normalize_minor=False では C#4(61) はスキップ
        events = [make_event(61, 0, Q)]
        part_tokens = events_to_tokens_per_part(
            make_midi_data(events), normalize_minor_set, normalize_minor=False
        )
        assert part_tokens == [[], []]
        assert "[WARN]" in capsys.readouterr().err


class TestGenerateScoreLy:
    def test_version_header(self, kurd9):
        result = generate_score_ly([], kurd9)
        assert '\\version "2.24.4"' in result

    def test_scale_include(self, kurd9):
        result = generate_score_ly([], kurd9)
        assert '\\include "../Scales/D_Kurd9.ly"' in result

    def test_set_translate_table(self, kurd9):
        result = generate_score_ly([], kurd9)
        assert "\\SetTranslateTable #d_kurd9" in result

    def test_handpan_score_tokens(self, kurd9):
        tokens = ["0-4", "1-4"]
        result = generate_score_ly(tokens, kurd9)
        assert '\\HandpanScore "0-4 1-4"' in result

    def test_chunk_split_creates_two_blocks(self, kurd9):
        # 8小節分（bars_per_chunk=4）→ HandpanScore ブロックが 2 つ
        tokens = ["0-4"] + ["\\|"] * 7 + ["1-4"]
        result = generate_score_ly(tokens, kurd9, bars_per_chunk=4)
        assert result.count("\\HandpanScore") == 2

    def test_from_fixture_midi(self, midi_data, kurd9):
        tokens = events_to_tokens(midi_data, kurd9)
        result = generate_score_ly(tokens, kurd9, bars_per_chunk=4)
        assert '\\version "2.24.4"' in result
        assert "\\HandpanScore" in result


# ---------------------------------------------------------------------------
# generate_set_score_ly
# ---------------------------------------------------------------------------

class TestGenerateSetScoreLy:
    def test_version_header(self, two_part_set):
        result = generate_set_score_ly([[], []], two_part_set)
        assert '\\version "2.24.4"' in result

    def test_both_translate_tables(self, two_part_set):
        result = generate_set_score_ly([["0-4"], ["0-4"]], two_part_set)
        assert "\\SetTranslateTable #PartA" in result
        assert "\\SetTranslateTable #PartB" in result

    def test_simultaneous_block_markers(self, two_part_set):
        result = generate_set_score_ly([["0-4"], ["0-4"]], two_part_set)
        assert "<<" in result
        assert ">>" in result

    def test_chunk_split_creates_two_blocks(self, two_part_set):
        tokens_a = ["0-4"] + ["\\|"] * 7 + ["1-4"]
        tokens_b = ["H-4"] + ["\\|"] * 7 + ["H-4"]
        result = generate_set_score_ly([tokens_a, tokens_b], two_part_set, bars_per_chunk=4)
        assert result.count("<<") == 2

    def test_scale_include_present(self, two_part_set: HandpanSet) -> None:
        result = generate_set_score_ly([[], []], two_part_set)
        assert '\\include "../Scales/' in result

    def test_handpan_score_tokens_per_part(self, two_part_set: HandpanSet) -> None:
        result = generate_set_score_ly([["0-4"], ["1-4"]], two_part_set)
        assert result.count("\\HandpanScore") == 2
        assert '"0-4"' in result
        assert '"1-4"' in result
