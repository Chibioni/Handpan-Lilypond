"""Scale and ensemble definitions."""

from ..models import HandpanScale, HandpanPart, HandpanSet

SCALES: dict[str, HandpanScale] = {
    "d_kurd9": HandpanScale(
        scale_family="Kurd",
        note_names=["D3", "A3", "Bb3", "C4", "D4", "E4", "F4", "G4", "A4"],
        key_signature="d \\minor",
    ),
}

ENSEMBLES: dict[str, HandpanSet] = {
    "f_sharp_minor18": HandpanSet(
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
    ),
}
