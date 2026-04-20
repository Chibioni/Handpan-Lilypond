"""normalize_minor オプション用テスト MIDI ファイル生成スクリプト。

D Kurd 9: D3(50) A3(57) Bb3(58) C4(60) D4(62) E4(64) F4(65) G4(67) A4(69)
D ルート (PC=2) の raised 音:
  raised 6th: B♮ (PC=11) — 例: B♮4 = MIDI 71
  raised 7th: C#  (PC=1)  — 例: C#4 = MIDI 61, C#5 = MIDI 73

カバーする要件:
  - 通常スケール音（そのまま TF4 へ変換）
  - raised 7th C#4(61)   → normalize_minor 時: C4(60)=TF3 基音
  - raised 6th B♮4(71)   → normalize_minor 時: Bb4(70)=TF2 ハーモニクス1
  - raised 7th C#5(73)   → normalize_minor 時: C5(72)=TF3 ハーモニクス1
  - normalize_minor なし → 上記 3 音はスキップ（スケール外）

ノート列（4/4拍子、120BPM、ticks_per_beat=480）:
  小節1:
    tick=0:    D4(62)  Q  vel=64  通常スケール音 → TF4
    tick=480:  C#4(61) Q  vel=64  raised 7th → TF3（normalize 時）
    tick=960:  B♮4(71) Q  vel=64  raised 6th → TF2^1（normalize 時）
    tick=1440: C#5(73) Q  vel=64  raised 7th 高音域 → TF3^1（normalize 時）
"""

from pathlib import Path
import mido

TICKS_PER_BEAT = 480
TEMPO = 500_000  # 120 BPM
Q = TICKS_PER_BEAT  # 480 = 4分音符


def make_events(
    notes: list[tuple[int, int, int, int]],  # (abs_tick, midi_note, duration, velocity)
) -> list[tuple[int, mido.Message]]:
    events: list[tuple[int, mido.Message]] = []
    for tick, note, duration, velocity in notes:
        events.append((tick,          mido.Message("note_on",  note=note, velocity=velocity, time=0)))
        events.append((tick+duration, mido.Message("note_off", note=note, velocity=0,        time=0)))
    return events


def main() -> None:
    notes: list[tuple[int, int, int, int]] = [
        (0,    62, Q, 64),  # D4   通常スケール音 TF4
        (480,  61, Q, 64),  # C#4  raised 7th → normalize: TF3
        (960,  71, Q, 64),  # B♮4  raised 6th → normalize: TF2^1
        (1440, 73, Q, 64),  # C#5  raised 7th 高音域 → normalize: TF3^1
    ]

    events = make_events(notes)
    events.sort(key=lambda e: (e[0], e[1].type))

    mid = mido.MidiFile(type=0, ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage("set_tempo", tempo=TEMPO, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))

    prev_tick = 0
    for abs_tick, msg in events:
        msg.time = abs_tick - prev_tick
        track.append(msg)
        prev_tick = abs_tick

    out = Path(__file__).parent / "normalize_minor.mid"
    mid.save(str(out))
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
