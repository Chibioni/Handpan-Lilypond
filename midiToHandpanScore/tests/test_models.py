import pytest
from miditohandpanscore.models import compute_ly_pitches, HandpanScale, HandpanPart, HandpanSet


# D3=50, A3=57, Bb3=58, C4=60, D4=62, E4=64, F4=65, G4=67, A4=69
KURD9_NOTES = ["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"]
KURD9_MIDIS = [50, 57, 58, 60, 62, 64, 65, 67, 69]


class TestComputeLyPitches:
    def test_ding_is_minus_one(self):
        result = compute_ly_pitches(KURD9_MIDIS)
        assert result[0] == -1

    def test_ascending_above_ding(self):
        result = compute_ly_pitches(KURD9_MIDIS)
        assert result == [-1, 1, 2, 3, 4, 5, 6, 7, 8]

    def test_notes_below_ding(self):
        # ding=D4=62, C#4=61 は Ding より低い
        midis = [62, 61]
        assert compute_ly_pitches(midis) == [-1, -2]

    def test_mixed_order_preserved(self):
        # 入力順が出力に反映される
        midis = [62, 67, 60]  # D4(ding), G4, C4
        result = compute_ly_pitches(midis)
        assert result[0] == -1   # D4 = ding
        assert result[1] == 1    # G4 = ding の上の唯一の音
        assert result[2] == -2   # C4 = ding より低い


class TestHandpanScale:
    @pytest.fixture
    def kurd9(self):
        return HandpanScale(
            scale_family="Kurd",
            note_names=KURD9_NOTES,
            key_signature="2b",
        )

    def test_midi_notes(self, kurd9):
        assert kurd9.midi_notes == KURD9_MIDIS

    def test_name(self, kurd9):
        assert kurd9.name == "D_Kurd9"

    def test_ly_name(self, kurd9):
        assert kurd9.ly_name == "d_kurd9"

    def test_ly_pitches(self, kurd9):
        assert kurd9.ly_pitches == [-1, 1, 2, 3, 4, 5, 6, 7, 8]

    def test_name_with_sharp(self):
        scale = HandpanScale(
            scale_family="Kurd",
            note_names=["F#3", "C#4", "D4", "E4", "F#4", "G#4", "A4", "B4", "C#5"],
            key_signature="3#",
        )
        assert scale.name == "F_Sharp_Kurd9"
        assert scale.ly_name == "f_sharp_kurd9"

    def test_name_with_space_in_family(self):
        scale = HandpanScale(
            scale_family="Celtic Minor",
            note_names=KURD9_NOTES,
            key_signature="2b",
        )
        assert scale.name == "D_Celtic_Minor9"
        assert scale.ly_name == "d_celtic_minor9"


class TestHandpanSet:
    @pytest.fixture
    def ensemble(self):
        scale_a = HandpanScale("Kurd", ["D4", "A4", "Bb4", "C5", "D5"], "2b")
        scale_b = HandpanScale("Kurd", ["A3", "E4", "F4", "G4", "A4"], "2b")
        return HandpanSet(
            scale_family="Kurd",
            parts=[HandpanPart("Player 1", scale_a), HandpanPart("Player 2", scale_b)],
            key_signature="2b",
        )

    def test_name(self, ensemble):
        assert ensemble.name == "D_Kurd10"

    def test_part_ly_pitches_ding_is_minus_one(self, ensemble):
        pitches = ensemble.part_ly_pitches(0)
        assert pitches[0] == -1  # D4 = ding of ensemble

    def test_part_ly_pitches_uses_all_notes(self, ensemble):
        # part 1 の A3 は全音符でソートすると ding(D4) より低い → 負の値
        pitches_b = ensemble.part_ly_pitches(1)
        assert pitches_b[0] < -1  # A3 < D4
