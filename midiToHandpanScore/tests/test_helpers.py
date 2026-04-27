"""helpers.py のテスト。"""

import pytest

from miditohandpanscore.helpers import note_name_to_midi, note_name_to_scale_identifier


# ---------------------------------------------------------------------------
# note_name_to_midi
# ---------------------------------------------------------------------------

class TestNoteNameToMidi:
    @pytest.mark.parametrize("name,expected", [
        ("C4",   60),
        ("D3",   50),
        ("A3",   57),
        ("Bb3",  58),
        ("F#3",  54),
        ("C#4",  61),
        ("Cx4",  62),   # ダブルシャープ (x 表記)
        ("C##4", 62),   # ダブルシャープ (## 表記)
        ("Dbb3", 48),   # ダブルフラット
        ("C-1",   0),   # MIDI 最小値 (octave=-1 → (−1+1)*12=0)
        ("G9",  127),   # 最大値
    ])
    def test_known_notes(self, name, expected):
        assert note_name_to_midi(name) == expected

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            note_name_to_midi("C10")  # 128 以上

    def test_invalid_stem_raises(self):
        with pytest.raises((ValueError, KeyError)):
            note_name_to_midi("H4")

    def test_invalid_accidental_raises(self):
        with pytest.raises(ValueError, match="Invalid accidental"):
            note_name_to_midi("C$4")

    def test_missing_octave_raises(self):
        with pytest.raises(ValueError, match="Invalid octave number"):
            note_name_to_midi("C#")

    def test_double_minus_octave_raises(self):
        with pytest.raises(ValueError):
            note_name_to_midi("C--1")


# ---------------------------------------------------------------------------
# note_name_to_scale_identifier
# ---------------------------------------------------------------------------

class TestNoteNameToScaleIdentifier:
    @pytest.mark.parametrize("name,expected", [
        ("D3",   "D"),
        ("F#3",  "F_Sharp"),
        ("Bb3",  "B_Flat"),
        ("Cx4",  "C_Sharp_Sharp"),
        ("Dbb3", "D_Flat_Flat"),
        ("A4",   "A"),
    ])
    def test_known_names(self, name, expected):
        assert note_name_to_scale_identifier(name) == expected
