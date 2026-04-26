"""score_generator.py の低レベルヘルパー関数のテスト。"""

import pytest
from miditohandpanscore.models import MidiNoteEvent, HandpanScale, HandpanPart, HandpanSet
from miditohandpanscore.midi_processing import TimeSignatureChange
from miditohandpanscore.ly_writer import _split_chunks
from miditohandpanscore.score_events import (
    Articulation,
    BarLine,
    Chord,
    Rest,
    ScoreEvent,
    Technique,
    ToneFieldNote,
)
from miditohandpanscore.score_generator import (
    _velocity_to_articulation,
    _group_by_tick,
    _split_markers,
    _bar_ticks,
)
from miditohandpanscore.tf_lookup import (
    find_tf,
    find_lookup,
    normalize_midi,
    set_priority,
)


def to_strs(events: list[ScoreEvent]) -> list[str]:
    return [e.to_token() for e in events]


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
        assert _velocity_to_articulation(127) == Articulation.ACCENT

    def test_ghost_lower_bound(self):
        assert _velocity_to_articulation(1) == Articulation.GHOST

    def test_ghost_upper_bound(self):
        assert _velocity_to_articulation(30) == Articulation.GHOST

    def test_normal_just_above_ghost(self):
        assert _velocity_to_articulation(31) == Articulation.NORMAL

    def test_zero(self):
        assert _velocity_to_articulation(0) == Articulation.NORMAL


# ---------------------------------------------------------------------------
# ToneFieldNote
# ---------------------------------------------------------------------------

def make_note(number: int, harmonic: int = 0, technique: Technique = Technique.NORMAL, articulation: Articulation = Articulation.NORMAL, duration: str = "4") -> ToneFieldNote:
    return ToneFieldNote(part_index=0, number=number, harmonic=harmonic, articulation=articulation, technique=technique, duration=duration)


class TestToneFieldNote:
    def test_plain_note(self):
        assert make_note(1).to_token() == "1-4"

    def test_with_technique(self):
        assert make_note(0, technique=Technique.APEX).to_token() == "O0-4"

    def test_with_harmonic1(self):
        assert make_note(2, harmonic=1, duration="8").to_token() == "2^1-8"

    def test_with_harmonic2(self):
        assert make_note(3, harmonic=2, duration="4.").to_token() == "3^2-4."

    def test_with_accent(self):
        assert make_note(1, articulation=Articulation.ACCENT).to_token() == "1!-4"

    def test_with_ghost(self):
        assert make_note(1, articulation=Articulation.GHOST, duration="8").to_token() == "1.-8"

    def test_full_combination(self):
        assert make_note(2, harmonic=1, technique=Technique.SLAP, articulation=Articulation.ACCENT, duration="4.").to_token() == "S2^1!-4."

    def test_duration_override(self):
        assert make_note(1, duration="4").to_token("8") == "1-8"


# ---------------------------------------------------------------------------
# Chord
# ---------------------------------------------------------------------------

class TestChord:
    def test_single_note_passthrough(self):
        chord = Chord(notes=[make_note(1)], duration="4")
        assert chord.to_token() == "1-4"

    def test_two_note_chord(self):
        chord = Chord(notes=[make_note(1), make_note(3)], duration="4")
        assert chord.to_token() == "< 1-4 3-4 >"

    def test_three_note_chord(self):
        chord = Chord(notes=[make_note(1), make_note(3), make_note(5)], duration="4")
        assert chord.to_token() == "< 1-4 3-4 5-4 >"

    def test_with_technique(self):
        chord = Chord(notes=[make_note(1, technique=Technique.APEX), make_note(3, technique=Technique.APEX)], duration="4")
        assert chord.to_token() == "< O1-4 O3-4 >"

    def test_duration_overrides_note_duration(self):
        chord = Chord(notes=[make_note(1, duration="8")], duration="4")
        assert chord.to_token() == "1-4"


# ---------------------------------------------------------------------------
# Rest / BarLine
# ---------------------------------------------------------------------------

class TestRest:
    def test_visible_rest(self):
        assert Rest(duration="4").to_token() == "R-4"

    def test_hidden_rest(self):
        assert Rest(duration="2", hidden=True).to_token() == "H-2"

    def test_dotted_rest(self):
        assert Rest(duration="4.").to_token() == "R-4."


class TestBarLine:
    def test_to_token(self):
        assert BarLine().to_token() == "|"


# ---------------------------------------------------------------------------
# _find_tf / _scale_priority（旧 _build_scale_tables の相当テスト）
# ---------------------------------------------------------------------------

def _priority_lookup(midi_note: int, scale: HandpanScale, normalize_minor: bool = False):
    """テスト用: priority list を使って (tf, harmonic) を返す。"""
    single_set = HandpanSet(
        scale_family=scale.scale_family,
        parts=[HandpanPart(instrument_name="test", scale=scale)],
        key_signature=scale.key_signature,
    )
    priority = set_priority(single_set)
    all_reachable = frozenset(n for tonefields, _, _ in priority for n in tonefields)
    norm_info = [(scale.midi_notes[0], all_reachable)]
    midi = normalize_midi(midi_note, norm_info) if normalize_minor else midi_note
    result = find_lookup(midi, priority)
    return (result.tone_field_number, result.harmonic) if result is not None else None


class TestFindTf:
    def test_found(self):
        assert find_tf(62, [50, 57, 62, 65]) == 2

    def test_not_found(self):
        assert find_tf(99, [50, 57, 62]) is None

    def test_first_occurrence(self):
        assert find_tf(50, [50, 50]) == 0


class TestScalePriority:
    def test_base_note_ding(self, kurd9):
        assert _priority_lookup(50, kurd9) == (0, 0)  # D3 = TF0, harmonic=0

    def test_base_note_all(self, kurd9):
        expected_base = {50: 0, 57: 1, 58: 2, 60: 3, 62: 4, 64: 5, 65: 6, 67: 7, 69: 8}
        for midi, tf in expected_base.items():
            assert _priority_lookup(midi, kurd9) == (tf, 0)

    def test_harmonic1_octave(self, kurd9):
        # Bb3(58) + 12 = Bb4(70) → TF2, harmonic 1
        assert _priority_lookup(70, kurd9) == (2, 1)

    def test_harmonic2(self, kurd9):
        # E4(64) + 19 = B5(83) → TF5, harmonic 2
        assert _priority_lookup(83, kurd9) == (5, 2)
        # F4(65) + 19 = C6(84) → TF6, harmonic 2
        assert _priority_lookup(84, kurd9) == (6, 2)

    def test_harmonic1_priority_over_harmonic2(self, kurd9):
        # F4(65)+12=F5(77) と Bb3(58)+19=F5(77) が衝突する。
        # 基音 → ハーモニクス1 → ハーモニクス2 の順なので TF6 ハーモニクス1 が勝つ。
        assert _priority_lookup(77, kurd9) == (6, 1)

    def test_base_note_overrides_harmonic(self, kurd9):
        # D3(50)+19=69 は TF0 のハーモニクス2 だが、69 は TF8 (A4) の基音でもある → 基音が優先
        assert _priority_lookup(69, kurd9) == (8, 0)

    def test_not_in_scale(self, kurd9):
        assert _priority_lookup(61, kurd9) is None

    # normalize_minor=True のテスト
    # D Kurd 9 のルートは D3(MIDI 50)。
    # 上昇6度 = D+9半音 = B♮ (PC=11)、上昇7度 = D+11半音 = C# (PC=1)。

    def test_normalize_minor_raised_7th_maps_to_natural(self, kurd9):
        # C#4 (MIDI 61) → C4 (MIDI 60) = TF3 基音
        assert _priority_lookup(61, kurd9, normalize_minor=True) == (3, 0)

    def test_normalize_minor_raised_6th_maps_to_harmonic(self, kurd9):
        # B♮4 (MIDI 71) → Bb4 (MIDI 70) = TF2 ハーモニクス1
        assert _priority_lookup(71, kurd9, normalize_minor=True) == (2, 1)

    def test_normalize_minor_raised_7th_higher_octave(self, kurd9):
        # C#5 (MIDI 73) → C5 (MIDI 72) = TF3 ハーモニクス1
        assert _priority_lookup(73, kurd9, normalize_minor=True) == (3, 1)

    def test_normalize_minor_off_by_default(self, kurd9):
        # normalize_minor=False（デフォルト）では C#4 はスケールにない
        assert _priority_lookup(61, kurd9) is None

    def test_normalize_minor_does_not_change_existing(self, kurd9):
        # スケール内の既存 MIDI ノートは normalize_minor=True でも変わらない
        for midi in kurd9.midi_notes:
            assert _priority_lookup(midi, kurd9) == _priority_lookup(midi, kurd9, normalize_minor=True)


# ---------------------------------------------------------------------------
# normalize_midi（単エントリによる個別ノート変換のテスト）
# ---------------------------------------------------------------------------

class TestNormalizeMidiNote:
    def test_raised_7th_normalized(self):
        assert normalize_midi(61, [(50, frozenset({60}))]) == 60

    def test_raised_6th_normalized(self):
        assert normalize_midi(71, [(50, frozenset({70}))]) == 70

    def test_no_natural_no_mapping(self):
        assert normalize_midi(61, [(50, frozenset())]) == 61

    def test_unrelated_note_unchanged(self):
        assert normalize_midi(60, [(50, frozenset({60}))]) == 60

    def test_a_root_raised_6th(self):
        assert normalize_midi(66, [(57, frozenset({65}))]) == 65

    def test_a_root_raised_7th(self):
        assert normalize_midi(68, [(57, frozenset({67}))]) == 67

    def test_octave_invariant(self):
        assert normalize_midi(73, [(50, frozenset({72}))]) == 72  # C#5 → C5


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
        assert technique == Technique.NORMAL
        assert len(real_notes) == 1

    def test_apex_marker(self):
        group = [make_event(0, 0, 480), make_event(50, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == Technique.APEX
        assert len(real_notes) == 1
        assert real_notes[0].midi_note == 50

    def test_slap_marker(self):
        group = [make_event(1, 0, 480), make_event(64, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == Technique.SLAP
        assert len(real_notes) == 1

    def test_only_marker_no_notes(self):
        group = [make_event(0, 0, 480)]
        technique, real_notes = _split_markers(group)
        assert technique == Technique.APEX
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

def _r(dur: str = "4") -> Rest:
    return Rest(duration=dur)


class TestSplitChunks:
    def test_single_chunk(self):
        events = [_r(), _r(), BarLine(), _r(), _r()]
        chunks = _split_chunks(events, bars_per_chunk=2)
        assert len(chunks) == 1
        assert any(isinstance(e, BarLine) for e in chunks[0])

    def test_two_chunks(self):
        events = [_r(), BarLine(), _r(), BarLine(), _r(), BarLine(), _r()]
        chunks = _split_chunks(events, bars_per_chunk=2)
        assert len(chunks) == 2
        assert to_strs(chunks[0]) == ["R-4", "|", "R-4"]
        assert to_strs(chunks[1]) == ["R-4", "|", "R-4"]

    def test_chunk_boundary_bar_excluded(self):
        events = [_r(), BarLine(), _r(), BarLine(), _r()]
        chunks = _split_chunks(events, bars_per_chunk=1)
        for chunk in chunks:
            assert not isinstance(chunk[0], BarLine)
            assert not isinstance(chunk[-1], BarLine)

    def test_empty_tokens(self):
        assert _split_chunks([], bars_per_chunk=4) == []

    def test_no_bar_lines(self):
        events = [_r(), _r(), _r()]
        chunks = _split_chunks(events, bars_per_chunk=4)
        assert to_strs(chunks[0]) == ["R-4", "R-4", "R-4"]


# ---------------------------------------------------------------------------
# set_priority
# ---------------------------------------------------------------------------

@pytest.fixture
def two_scale_set():
    """Part A: [D3=50, A3=57]、Part B: [C4=60, D4=62] の 2 台セット。"""
    scale_a = HandpanScale(scale_family="TestA", note_names=["D3", "A3"], key_signature="d \\minor")
    scale_b = HandpanScale(scale_family="TestB", note_names=["C4", "D4"], key_signature="c \\major")
    return HandpanSet(
        scale_family="Test",
        parts=[
            HandpanPart(instrument_name="partA", scale=scale_a),
            HandpanPart(instrument_name="partB", scale=scale_b),
        ],
        key_signature="c \\major",
    )


class TestSetPriority:
    def test_priority_order_base_before_harmonics(self, two_scale_set):
        # 基音エントリが全てハーモニクスより前に来る
        priority = set_priority(two_scale_set)
        harmonic_indices = [i for i, (_, _, h) in enumerate(priority) if h > 0]
        base_indices = [i for i, (_, _, h) in enumerate(priority) if h == 0]
        assert max(base_indices) < min(harmonic_indices)

    def test_parts_interleaved_within_level(self, two_scale_set):
        # 各ハーモニクスレベルで part 0 → part 1 の順に並ぶ
        priority = set_priority(two_scale_set)
        base_entries = [(pi, h) for _, pi, h in priority if h == 0]
        assert base_entries == [(0, 0), (1, 0)]

    def test_base_note_routes_to_part_a(self, two_scale_set):
        # D3(50) は Part A の基音 → part_index=0, harmonic=0
        priority = set_priority(two_scale_set)
        result = find_lookup(50, priority)
        assert result is not None
        assert result.part_index == 0
        assert result.harmonic == 0

    def test_base_note_routes_to_part_b(self, two_scale_set):
        # C4(60) は Part B の基音 → part_index=1, harmonic=0
        priority = set_priority(two_scale_set)
        result = find_lookup(60, priority)
        assert result is not None
        assert result.part_index == 1
        assert result.harmonic == 0

    def test_harmonic_note_routes_correctly(self, two_scale_set):
        # D3(50)+12=D4(62) は Part A のハーモニクス1 だが D4 は Part B の基音でもある
        # 基音が先に来るため Part B 基音が勝つ
        priority = set_priority(two_scale_set)
        result = find_lookup(62, priority)
        assert result is not None
        assert result.part_index == 1
        assert result.harmonic == 0

    def test_note_in_neither_part_returns_none(self, two_scale_set):
        priority = set_priority(two_scale_set)
        assert find_lookup(99, priority) is None


# ---------------------------------------------------------------------------
# normalize_midi
# ---------------------------------------------------------------------------

class TestNormalizeMidi:
    def test_first_entry_normalizes(self):
        # 最初のエントリで正規化できる場合
        norm_info = [(50, frozenset({60})), (57, frozenset({65}))]
        assert normalize_midi(61, norm_info) == 60

    def test_second_entry_tried_when_first_fails(self):
        # 最初のエントリでは正規化できず、2番目で成功する場合
        norm_info = [(50, frozenset()), (57, frozenset({65}))]
        assert normalize_midi(66, norm_info) == 65

    def test_no_entry_normalizes_returns_original(self):
        # どのエントリでも正規化できない場合は元の値を返す
        norm_info = [(50, frozenset()), (57, frozenset())]
        assert normalize_midi(61, norm_info) == 61

    def test_empty_norm_info_returns_original(self):
        assert normalize_midi(61, []) == 61
