"""score_generator.py の低レベルヘルパー関数のテスト。"""

import pytest
from miditohandpanscore.models import MidiNoteEvent, HandpanScale
from miditohandpanscore.midi_processing import TimeSignatureChange
from miditohandpanscore.score_generator import (
    _velocity_to_articulation,
    _note_token,
    _chord_token,
    _build_scale_tables,
    _group_by_tick,
    _split_markers,
    _bar_ticks,
    _split_chunks,
    _minor_raised_pcs,
    _apply_minor_normalization,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kurd9():
    # D3=50, A3=57, Bb3=58, C4=60, D4=62, E4=64, F4=65, G4=67, A4=69
    return HandpanScale(
        scale_family="Kurd",
        note_names=["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"],
        key_signature="d \\minor",
    )


def make_event(midi_note: int, tick_start: int, tick_end: int, velocity: int = 64) -> MidiNoteEvent:
    return MidiNoteEvent(
        midi_note=midi_note,
        tick_start=tick_start,
        tick_end=tick_end,
        velocity=velocity,
    )


# ---------------------------------------------------------------------------
# _velocity_to_articulation
# ---------------------------------------------------------------------------

class TestVelocityToArticulation:
    def test_accent(self):
        assert _velocity_to_articulation(127) == "!"

    def test_ghost_lower_bound(self):
        assert _velocity_to_articulation(1) == "."

    def test_ghost_upper_bound(self):
        assert _velocity_to_articulation(30) == "."

    def test_normal_mid(self):
        assert _velocity_to_articulation(64) == ""

    def test_normal_just_above_ghost(self):
        assert _velocity_to_articulation(31) == ""

    def test_zero(self):
        assert _velocity_to_articulation(0) == ""


# ---------------------------------------------------------------------------
# _note_token
# ---------------------------------------------------------------------------

class TestNoteToken:
    def test_plain_note(self):
        assert _note_token(1, 0, "", "", "4") == "1-4"

    def test_with_technique(self):
        assert _note_token(0, 0, "O", "", "4") == "O0-4"

    def test_with_harmonic1(self):
        assert _note_token(2, 1, "", "", "8") == "2^1-8"

    def test_with_harmonic2(self):
        assert _note_token(3, 2, "", "", "4.") == "3^2-4."

    def test_with_accent(self):
        assert _note_token(1, 0, "", "!", "4") == "1!-4"

    def test_with_ghost(self):
        assert _note_token(1, 0, "", ".", "8") == "1.-8"

    def test_full_combination(self):
        assert _note_token(2, 1, "S", "!", "4.") == "S2^1!-4."


# ---------------------------------------------------------------------------
# _chord_token
# ---------------------------------------------------------------------------

class TestChordToken:
    def test_single_note_passthrough(self):
        assert _chord_token(["1-4"]) == "1-4"

    def test_two_note_chord(self):
        assert _chord_token(["1-4", "3-4"]) == "< 1-4 3-4 >"

    def test_three_note_chord(self):
        assert _chord_token(["1-4", "3-4", "5-4"]) == "< 1-4 3-4 5-4 >"

    def test_with_technique(self):
        assert _chord_token(["O1-4", "O3-4"]) == "< O1-4 O3-4 >"


# ---------------------------------------------------------------------------
# _build_scale_tables
# ---------------------------------------------------------------------------

class TestBuildScaleTables:
    def test_base_note_ding(self, kurd9):
        table = _build_scale_tables(kurd9)
        assert table[50] == (0, 0)  # D3 = TF0, harmonic=0

    def test_base_note_all(self, kurd9):
        table = _build_scale_tables(kurd9)
        expected_base = {50: 0, 57: 1, 58: 2, 60: 3, 62: 4, 64: 5, 65: 6, 67: 7, 69: 8}
        for midi, tf in expected_base.items():
            assert table[midi] == (tf, 0)

    def test_harmonic1_octave(self, kurd9):
        table = _build_scale_tables(kurd9)
        # Bb3(58) + 12 = Bb4(70) → TF2, harmonic 1
        assert table[70] == (2, 1)

    def test_harmonic2(self, kurd9):
        table = _build_scale_tables(kurd9)
        # E4(64) + 19 = B5(83) → TF5, harmonic 2
        assert table[83] == (5, 2)
        # F4(65) + 19 = C6(84) → TF6, harmonic 2
        assert table[84] == (6, 2)

    def test_harmonic1_priority_over_harmonic2(self, kurd9):
        table = _build_scale_tables(kurd9)
        # F4(65)+12=F5(77) と Bb3(58)+19=F5(77) が衝突する。
        # 全 TF ハーモニクス1 の登録が先に完了するため TF6 ハーモニクス1 が勝つ。
        assert table[77] == (6, 1)

    def test_base_note_overrides_harmonic(self, kurd9):
        # D3(50)+19=69 は TF0 のハーモニクス2 だが、69 は TF8 (A4) の基音でもある → 基音が優先
        table = _build_scale_tables(kurd9)
        assert table[69] == (8, 0)

    # normalize_minor=True のテスト
    # D Kurd 9 のルートは D3(MIDI 50)。
    # 上昇6度 = D+9半音 = B♮ (PC=11)、上昇7度 = D+11半音 = C# (PC=1)。

    def test_normalize_minor_raised_7th_maps_to_natural(self, kurd9):
        # C#4 (MIDI 61) → C4 (MIDI 60) = TF3 基音
        table = _build_scale_tables(kurd9, normalize_minor=True)
        assert table[61] == (3, 0)

    def test_normalize_minor_raised_6th_maps_to_harmonic(self, kurd9):
        # B♮4 (MIDI 71) → Bb4 (MIDI 70) = TF2 ハーモニクス1
        table = _build_scale_tables(kurd9, normalize_minor=True)
        assert table[71] == (2, 1)

    def test_normalize_minor_raised_7th_higher_octave(self, kurd9):
        # C#5 (MIDI 73) → C5 (MIDI 72) = TF3 ハーモニクス1
        table = _build_scale_tables(kurd9, normalize_minor=True)
        assert table[73] == (3, 1)

    def test_normalize_minor_off_by_default(self, kurd9):
        # normalize_minor=False（デフォルト）では C#4 はテーブルに存在しない
        table = _build_scale_tables(kurd9)
        assert 61 not in table

    def test_normalize_minor_does_not_override_existing(self, kurd9):
        # 既にテーブルにある MIDI ノートは上書きされない
        table_without = _build_scale_tables(kurd9)
        table_with = _build_scale_tables(kurd9, normalize_minor=True)
        for midi, lookup in table_without.items():
            assert table_with[midi] == lookup


# ---------------------------------------------------------------------------
# _minor_raised_pcs
# ---------------------------------------------------------------------------

class TestMinorRaisedPcs:
    def test_d_root(self):
        # D (PC=2): 上昇6度=11 (B♮), 上昇7度=1 (C#)
        assert _minor_raised_pcs(50) == frozenset({11, 1})

    def test_a_root(self):
        # A (PC=9): 上昇6度=6 (F#), 上昇7度=8 (G#)
        assert _minor_raised_pcs(57) == frozenset({6, 8})

    def test_octave_invariant(self):
        # オクターブが違っても同じ結果
        assert _minor_raised_pcs(50) == _minor_raised_pcs(62)


# ---------------------------------------------------------------------------
# _apply_minor_normalization
# ---------------------------------------------------------------------------

class TestApplyMinorNormalization:
    def test_raised_7th_added(self):
        # C4(60) → TF3 がある状態で D ルートの正規化 → C#4(61) が追加される
        table: dict[int, tuple[int, int]] = {60: (3, 0)}
        _apply_minor_normalization(table, root_midi=50)  # D root
        assert 61 in table
        assert table[61] == (3, 0)

    def test_raised_6th_added(self):
        # Bb4(70) → TF2 harmonic=1 がある状態 → B♮4(71) が追加される
        table: dict[int, tuple[int, int]] = {70: (2, 1)}
        _apply_minor_normalization(table, root_midi=50)  # D root
        assert 71 in table
        assert table[71] == (2, 1)

    def test_no_natural_no_mapping(self):
        # 自然短音がテーブルにない場合は写像しない
        table: dict[int, tuple[int, int]] = {}
        _apply_minor_normalization(table, root_midi=50)
        assert 61 not in table
        assert 71 not in table

    def test_existing_entry_not_overwritten(self):
        # 既存エントリは上書きされない
        table: dict[int, tuple[int, int]] = {61: (99, 0), 60: (3, 0)}
        _apply_minor_normalization(table, root_midi=50)
        assert table[61] == (99, 0)


# ---------------------------------------------------------------------------
# _group_by_tick
# ---------------------------------------------------------------------------

class TestGroupByTick:
    def test_single_event(self):
        events = [make_event(60, 0, 480)]
        groups, ticks = _group_by_tick(events)
        assert ticks == [0]
        assert len(groups[0]) == 1

    def test_multiple_ticks(self):
        events = [make_event(60, 0, 480), make_event(62, 480, 960)]
        groups, ticks = _group_by_tick(events)
        assert ticks == [0, 480]

    def test_simultaneous_events_grouped(self):
        events = [make_event(60, 0, 480), make_event(64, 0, 480)]
        groups, ticks = _group_by_tick(events)
        assert ticks == [0]
        assert len(groups[0]) == 2

    def test_ticks_are_sorted(self):
        events = [make_event(62, 960, 1440), make_event(60, 0, 480), make_event(64, 480, 960)]
        _, ticks = _group_by_tick(events)
        assert ticks == [0, 480, 960]


# ---------------------------------------------------------------------------
# _split_markers
# ---------------------------------------------------------------------------

class TestSplitMarkers:
    def test_no_marker(self):
        group = [make_event(60, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == ""
        assert len(real_notes) == 1

    def test_apex_marker(self):
        group = [make_event(0, 0, 480), make_event(50, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == "O"
        assert len(real_notes) == 1
        assert real_notes[0].midi_note == 50

    def test_slap_marker(self):
        group = [make_event(1, 0, 480), make_event(64, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == "S"
        assert len(real_notes) == 1

    def test_only_marker_no_notes(self):
        group = [make_event(0, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == "O"
        assert real_notes == []


# ---------------------------------------------------------------------------
# _bar_ticks
# ---------------------------------------------------------------------------

class TestBarTicks:
    def test_4_4_bar_length(self):
        sig = [TimeSignatureChange(tick=0, numerator=4, denominator=4)]
        gen = _bar_ticks(sig, ticks_per_beat=480)
        ticks = [next(gen) for _ in range(4)]
        assert ticks == [0, 1920, 3840, 5760]

    def test_3_4_bar_length(self):
        sig = [TimeSignatureChange(tick=0, numerator=3, denominator=4)]
        gen = _bar_ticks(sig, ticks_per_beat=480)
        ticks = [next(gen) for _ in range(3)]
        assert ticks == [0, 1440, 2880]

    def test_time_sig_change_mid_song(self):
        sigs = [
            TimeSignatureChange(tick=0,    numerator=4, denominator=4),
            TimeSignatureChange(tick=1920, numerator=3, denominator=4),
        ]
        gen = _bar_ticks(sigs, ticks_per_beat=480)
        ticks = [next(gen) for _ in range(4)]
        # 小節1: 0, 小節2: 1920, 小節3: 1920+1440=3360, 小節4: 3360+1440=4800
        assert ticks == [0, 1920, 3360, 4800]


# ---------------------------------------------------------------------------
# _split_chunks
# ---------------------------------------------------------------------------

class TestSplitChunks:
    def test_single_chunk(self):
        tokens = ["1-4", "2-4", "\\|", "3-4", "4-4"]
        chunks = _split_chunks(tokens, bars_per_chunk=2)
        assert len(chunks) == 1
        assert "\\|" in chunks[0]

    def test_two_chunks(self):
        # 4小節を bars_per_chunk=2 で分割
        tokens = ["1-4", "\\|", "2-4", "\\|", "3-4", "\\|", "4-4"]
        chunks = _split_chunks(tokens, bars_per_chunk=2)
        assert len(chunks) == 2
        assert chunks[0] == ["1-4", "\\|", "2-4"]
        assert chunks[1] == ["3-4", "\\|", "4-4"]

    def test_chunk_boundary_bar_excluded(self):
        # チャンク境界の \\| はどちらのチャンクにも含まれない
        tokens = ["1-4", "\\|", "2-4", "\\|", "3-4"]
        chunks = _split_chunks(tokens, bars_per_chunk=1)
        for chunk in chunks:
            assert chunk[0] != "\\|"
            assert chunk[-1] != "\\|"

    def test_empty_tokens(self):
        assert _split_chunks([], bars_per_chunk=4) == []

    def test_no_bar_lines(self):
        tokens = ["1-4", "2-4", "3-4"]
        chunks = _split_chunks(tokens, bars_per_chunk=4)
        assert chunks == [["1-4", "2-4", "3-4"]]
