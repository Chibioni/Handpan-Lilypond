import pytest
from miditohandpanscore.generate_scales import _format_pairs, generate_scale_ly, generate_set_ly
from miditohandpanscore.models import HandpanScale, HandpanSet, HandpanPart


@pytest.fixture
def kurd9():
    return HandpanScale(
        scale_family="Kurd",
        note_names=["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"],
        key_signature="d \\minor",
    )


@pytest.fixture
def minor18():
    return HandpanSet(
        scale_family="Minor",
        parts=[
            HandpanPart("Grand", HandpanScale(
                scale_family="Grand",
                note_names=["F#3", "A3", "C#4", "E4", "G#4", "B4", "D5", "F#5", "A5"],
                key_signature="fis \\minor",
            )),
            HandpanPart("Leon", HandpanScale(
                scale_family="Leon",
                note_names=["G#3", "B3", "D4", "F#4", "A4", "C#5", "E5", "G#5", "B5"],
                key_signature="fis \\minor",
            )),
        ],
        key_signature="fis \\minor",
    )


class TestFormatPairs:
    def test_single_row(self):
        result = _format_pairs([(0, -1), (1, 1), (2, 2)])
        assert result == "  (0 . -1) (1 .  1) (2 .  2)"

    def test_multiple_rows(self):
        pairs = [(i, i) for i in range(6)]
        lines = _format_pairs(pairs).split("\n")
        assert len(lines) == 2

    def test_empty(self):
        assert _format_pairs([]) == ""


class TestGenerateScaleLy:
    def test_version_header(self, kurd9):
        result = generate_scale_ly(kurd9)
        assert '\\version "2.24.4"' in result

    def test_scale_name_in_comment(self, kurd9):
        result = generate_scale_ly(kurd9)
        assert "% D_Kurd9 スケール定義" in result

    def test_define_ly_name(self, kurd9):
        result = generate_scale_ly(kurd9)
        assert "#(define d_kurd9 '(" in result

    def test_key_signature(self, kurd9):
        result = generate_scale_ly(kurd9)
        assert '#(define d_kurd9-key-signature "d \\minor")' in result

    def test_pitches_present(self, kurd9):
        result = generate_scale_ly(kurd9)
        assert "(0 . -1)" in result


class TestGenerateSetLy:
    def test_version_header(self, minor18):
        result = generate_set_ly(minor18)
        assert '\\version "2.24.4"' in result

    def test_set_name_in_comment(self, minor18):
        result = generate_set_ly(minor18)
        assert "% F_Sharp_Minor18 セット定義" in result

    def test_each_part_defined(self, minor18):
        result = generate_set_ly(minor18)
        assert "#(define Grand '(" in result
        assert "#(define Leon '(" in result

    def test_key_signature(self, minor18):
        result = generate_set_ly(minor18)
        assert '#(define F_Sharp_Minor18-key-signature "fis \\minor")' in result
