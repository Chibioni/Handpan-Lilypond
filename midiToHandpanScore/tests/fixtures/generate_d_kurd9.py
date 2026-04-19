"""D Kurd 9 テスト用 MIDI ファイル生成スクリプト。

D Kurd 9: D3(50) A3(57) Bb3(58) C4(60) D4(62) E4(64) F4(65) G4(67) A4(69)

カバーする要件:
  - 通常ノート（全 TF）
  - アクセント（velocity=127）
  - ゴーストノート（velocity=20）
  - Ding への O リング打奏（MIDI 0 マーカー + D3）
  - スラップ（MIDI 1 マーカー）
  - ハーモニクス1（基音 + 12半音）: Bb4(70)=Bb3+12, C5(72)=C4+12
  - ハーモニクス2（基音 + 19半音）: F5(77)=Bb3+19, G5(79)=C4+19
  - 付点4分音符（Q.）
  - 付点8分音符（E.）
  - 二重付点4分音符（Q..）
  - 二重付点8分音符（E..）
  - 2分音符（H）

ノート列（4/4拍子、120BPM、ticks_per_beat=480）:
  小節1: 通常ノート + アーティキュレーション
    tick=0:    D3(50)  Q    vel=64  通常 Ding
    tick=480:  A3(57)  Q    vel=127 アクセント
    tick=960:  Bb3(58) Q.   vel=20  ゴースト 付点4分
    tick=1680: C4(60)  E    vel=64  通常 8分

  小節2: 奏法マーカー + 付点・二重付点
    tick=1920: MIDI_0+D3(50) Q    vel=64  Ding O リング打奏
    tick=2400: MIDI_1+E4(64) Q    vel=64  スラップ
    tick=2880: F4(65)        E.   vel=64  付点8分
    tick=3240: G4(67)        E..  vel=64  二重付点8分

  小節3: ハーモニクス
    tick=3840: Bb4(70) Q    vel=64  ハーモニクス1 (Bb3+12)
    tick=4320: C5(72)  Q    vel=64  ハーモニクス1 (C4+12)
    tick=4800: F5(77)  Q.   vel=64  ハーモニクス2 (Bb3+19) 付点4分
    tick=5520: G5(79)  E    vel=64  ハーモニクス2 (C4+19)

  小節4: 残りのスケール音 + 二重付点
    tick=5760: D4(62)  H    vel=64  2分音符
    tick=6720: A4(69)  Q..  vel=64  二重付点4分
"""

from pathlib import Path
import mido

TICKS_PER_BEAT = 480
TEMPO = 500_000  # 120 BPM

Q   = TICKS_PER_BEAT          # 480  4分
E   = TICKS_PER_BEAT // 2     # 240  8分
H   = TICKS_PER_BEAT * 2      # 960  2分
Qd  = Q * 3 // 2              # 720  付点4分
Ed  = E * 3 // 2              # 360  付点8分
Qdd = Q + Q // 2 + Q // 4     # 840  二重付点4分
Edd = E + E // 2 + E // 4     # 420  二重付点8分


def make_events(
    notes: list[tuple[int, int, int, int]],  # (abs_tick, midi_note, duration, velocity)
) -> list[tuple[int, mido.Message]]:
    """(abs_tick, Message) のリストに展開する。"""
    events: list[tuple[int, mido.Message]] = []
    for tick, note, duration, velocity in notes:
        events.append((tick,          mido.Message("note_on",  note=note, velocity=velocity, time=0)))
        events.append((tick+duration, mido.Message("note_off", note=note, velocity=0,        time=0)))
    return events


def main() -> None:
    notes: list[tuple[int, int, int, int]] = [
        # 小節1
        (0,    50, Q,   64),   # D3  通常 Ding
        (480,  57, Q,   127),  # A3  アクセント
        (960,  58, Qd,  20),   # Bb3 ゴースト 付点4分
        (1680, 60, E,   64),   # C4  通常 8分

        # 小節2: 奏法マーカー（同 tick に MIDI 0/1 を配置）
        (1920, 0,  Q,   64),   # Apex マーカー
        (1920, 50, Q,   64),   # D3 Ding + O リング打奏
        (2400, 1,  Q,   64),   # Slap マーカー
        (2400, 64, Q,   64),   # E4 + スラップ
        (2880, 65, Ed,  64),   # F4 付点8分
        (3240, 67, Edd, 64),   # G4 二重付点8分

        # 小節3: ハーモニクス
        (3840, 70, Q,   64),   # Bb4 = Bb3+12  ハーモニクス1
        (4320, 72, Q,   64),   # C5  = C4+12   ハーモニクス1
        (4800, 77, Qd,  64),   # F5  = Bb3+19  ハーモニクス2 付点4分
        (5520, 79, E,   64),   # G5  = C4+19   ハーモニクス2 8分

        # 小節4: 残りのスケール音
        (5760, 62, H,   64),   # D4 2分音符
        (6720, 69, Qdd, 64),   # A4 二重付点4分
    ]

    events = make_events(notes)
    events.sort(key=lambda e: (e[0], e[1].type))  # note_off を note_on より前に

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

    out = Path(__file__).parent / "d_kurd9.mid"
    mid.save(str(out))
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
