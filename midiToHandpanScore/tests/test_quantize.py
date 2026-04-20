import pytest
from miditohandpanscore.quantize import quantize, DUR_TO_BEATS, DURATION_TABLE


class TestQuantizeExactMatch:
    @pytest.mark.parametrize("beats,expected", [
        (4.0,    "1"),
        (3.5,    "2.."),
        (3.0,    "2."),
        (2.0,    "2"),
        (1.75,   "4.."),
        (1.5,    "4."),
        (1.0,    "4"),
        (0.875,  "8.."),
        (0.75,   "8."),
        (0.5,    "8"),
        (0.375,  "16."),
        (0.25,   "16"),
        (0.1875, "32."),
        (0.125,  "32"),
    ])
    def test_exact(self, beats, expected):
        assert quantize(beats) == expected


class TestQuantizeNearest:
    def test_very_small_rounds_to_32nd(self):
        assert quantize(0.01) == "32"

    def test_very_large_rounds_to_whole(self):
        assert quantize(10.0) == "1"

    def test_midpoint_between_whole_and_dotted_half(self):
        # 3.5 = "2.." として定義済みなので正確に一致する
        assert quantize(3.5) == "2.."

    def test_slightly_above_quarter(self):
        assert quantize(1.1) == "4"

    def test_slightly_below_quarter(self):
        # 0.9 は 8..(0.875) の方が 4(1.0) より近い
        assert quantize(0.9) == "8.."


class TestDurToBeats:
    def test_all_entries_present(self):
        assert len(DUR_TO_BEATS) == len(DURATION_TABLE)

    def test_roundtrip(self):
        for beats, dur_str in DURATION_TABLE:
            assert DUR_TO_BEATS[dur_str] == beats

    def test_quarter_note(self):
        assert DUR_TO_BEATS["4"] == 1.0

    def test_whole_note(self):
        assert DUR_TO_BEATS["1"] == 4.0

    def test_32nd_note(self):
        assert DUR_TO_BEATS["32"] == 0.125
