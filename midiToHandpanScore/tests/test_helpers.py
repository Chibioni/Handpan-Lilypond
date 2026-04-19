import pytest
from miditohandpanscore.helpers import note_name_to_midi, note_name_to_scale_identifier


class TestNoteNameToMidi:
    def test_natural(self):
        assert note_name_to_midi("C4") == 60
        assert note_name_to_midi("D4") == 62
        assert note_name_to_midi("E4") == 64
        assert note_name_to_midi("F4") == 65
        assert note_name_to_midi("G4") == 67
        assert note_name_to_midi("A4") == 69
        assert note_name_to_midi("B4") == 71

    def test_sharp(self):
        assert note_name_to_midi("C#4") == 61
        assert note_name_to_midi("F#3") == 54

    def test_flat(self):
        assert note_name_to_midi("Bb3") == 58
        assert note_name_to_midi("Eb4") == 63

    def test_double_sharp_x(self):
        assert note_name_to_midi("Cx4") == 62

    def test_double_sharp_hash(self):
        assert note_name_to_midi("C##4") == 62

    def test_double_flat(self):
        assert note_name_to_midi("Dbb3") == 48

    def test_invalid_stem_raises(self):
        with pytest.raises(ValueError):
            note_name_to_midi("X4")

    def test_boundary(self):
        assert note_name_to_midi("C-1") == 0
        assert note_name_to_midi("G9") == 127

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            note_name_to_midi("C-100")
        with pytest.raises(ValueError):
            note_name_to_midi("G100")


class TestNoteNameToScaleIdentifier:
    def test_natural(self):
        assert note_name_to_scale_identifier("C4") == "C"
        assert note_name_to_scale_identifier("D4") == "D"
        assert note_name_to_scale_identifier("E4") == "E"
        assert note_name_to_scale_identifier("F4") == "F"
        assert note_name_to_scale_identifier("G4") == "G"
        assert note_name_to_scale_identifier("A4") == "A"
        assert note_name_to_scale_identifier("B4") == "B"

    def test_sharp(self):
        assert note_name_to_scale_identifier("F#3") == "F_Sharp"

    def test_flat(self):
        assert note_name_to_scale_identifier("Bb3") == "B_Flat"

    def test_double_sharp_x(self):
        assert note_name_to_scale_identifier("Cx4") == "C_Sharp_Sharp"

    def test_double_sharp_hash(self):
        assert note_name_to_scale_identifier("C##4") == "C_Sharp_Sharp"

    def test_double_flat(self):
        assert note_name_to_scale_identifier("Dbb3") == "D_Flat_Flat"

    def test_ly_identifier_via_lower(self):
        assert note_name_to_scale_identifier("F#3").lower() == "f_sharp"
        assert note_name_to_scale_identifier("Bb3").lower() == "b_flat"

    def test_invalid_stem_raises(self):
        with pytest.raises(ValueError):
            note_name_to_scale_identifier("X4")
