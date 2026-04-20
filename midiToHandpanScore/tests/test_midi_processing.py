"""midi_processing.py のテスト。

d_kurd9.mid フィクスチャ（generate_d_kurd9.py で生成）を使用。
フィクスチャの内容:
  ticks_per_beat=480, tempo=500000(120BPM), 4/4拍子
  16ノートイベント（マーカー含む）
"""

from pathlib import Path

import mido
import pytest

from miditohandpanscore.midi_processing import (
    MidiData,
    TempoChange,
    TimeSignatureChange,
    _read_track,
    _select_tracks,
    read_midi,
)

FIXTURE_MID = Path(__file__).parent / "fixtures" / "d_kurd9.mid"
TPB = 480
Q = TPB
E = TPB // 2
H = TPB * 2
Qd = Q * 3 // 2
Ed = E * 3 // 2
Qdd = Q + Q // 2 + Q // 4
Edd = E + E // 2 + E // 4


# ---------------------------------------------------------------------------
# _read_track
# ---------------------------------------------------------------------------

class TestReadTrack:
    def _make_track(self, messages: list[mido.Message]) -> mido.MidiTrack:
        track = mido.MidiTrack()
        for msg in messages:
            track.append(msg)
        return track

    def test_note_on_off_collected(self):
        track = self._make_track([
            mido.Message("note_on",  note=60, velocity=64, time=0),
            mido.Message("note_off", note=60, velocity=0,  time=480),
        ])
        raw_events, _, _ = _read_track(track)
        assert len(raw_events) == 2

    def test_absolute_tick_accumulated(self):
        track = self._make_track([
            mido.Message("note_on",  note=60, velocity=64, time=0),
            mido.Message("note_off", note=60, velocity=0,  time=480),
            mido.Message("note_on",  note=62, velocity=64, time=240),
        ])
        raw_events, _, _ = _read_track(track)
        ticks = [t for t, _ in raw_events]
        assert ticks == [0, 480, 720]

    def test_tempo_change_collected(self):
        track = self._make_track([
            mido.MetaMessage("set_tempo", tempo=600_000, time=0),
        ])
        _, tempo_changes, _ = _read_track(track)
        assert len(tempo_changes) == 1
        assert tempo_changes[0].tempo == 600_000

    def test_time_signature_collected(self):
        track = self._make_track([
            mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0),
        ])
        _, _, time_sig_changes = _read_track(track)
        assert len(time_sig_changes) == 1
        assert time_sig_changes[0].numerator == 3
        assert time_sig_changes[0].denominator == 4

    def test_other_messages_ignored(self):
        track = self._make_track([
            mido.MetaMessage("track_name", name="test", time=0),
            mido.Message("control_change", channel=0, control=64, value=127, time=0),
        ])
        raw_events, tempo_changes, time_sig_changes = _read_track(track)
        assert raw_events == []
        assert tempo_changes == []
        assert time_sig_changes == []

    def test_tempo_tick_is_absolute(self):
        track = self._make_track([
            mido.Message("note_on",  note=60, velocity=64, time=100),
            mido.MetaMessage("set_tempo", tempo=600_000, time=200),
        ])
        _, tempo_changes, _ = _read_track(track)
        assert tempo_changes[0].tick == 300  # 100 + 200


# ---------------------------------------------------------------------------
# _select_tracks
# ---------------------------------------------------------------------------

class TestSelectTracks:
    def _make_mid(self, n_tracks: int) -> mido.MidiFile:
        mid = mido.MidiFile(type=0 if n_tracks == 1 else 1)
        for _ in range(n_tracks):
            mid.tracks.append(mido.MidiTrack())
        return mid

    def test_none_returns_all_tracks(self):
        mid = self._make_mid(3)
        result = _select_tracks(mid, None)
        assert len(result) == 3

    def test_index_0_returns_first_track(self):
        mid = self._make_mid(2)
        result = _select_tracks(mid, 0)
        assert len(result) == 1

    def test_index_out_of_range_exits(self):
        mid = self._make_mid(2)
        with pytest.raises(SystemExit):
            _select_tracks(mid, 5)


# ---------------------------------------------------------------------------
# read_midi — フィクスチャ MIDI を使った統合テスト
# ---------------------------------------------------------------------------

@pytest.fixture
def midi_data() -> MidiData:
    return read_midi(FIXTURE_MID)


class TestReadMidiFixture:
    def test_ticks_per_beat(self, midi_data):
        assert midi_data.ticks_per_beat == 480

    def test_event_count(self, midi_data):
        assert len(midi_data.events) == 16

    def test_events_sorted_by_tick_then_midi_note(self, midi_data):
        keys = [(e.tick_start, e.midi_note) for e in midi_data.events]
        assert keys == sorted(keys)

    def test_tempo(self, midi_data):
        assert len(midi_data.tempo_changes) == 1
        assert midi_data.tempo_changes[0].tempo == 500_000

    def test_time_signature(self, midi_data):
        assert len(midi_data.time_sig_changes) == 1
        ts = midi_data.time_sig_changes[0]
        assert ts.numerator == 4
        assert ts.denominator == 4

    # --- 個別イベントの検証 ---

    def test_first_event_ding(self, midi_data):
        ev = midi_data.events[0]
        assert ev.midi_note == 50
        assert ev.tick_start == 0
        assert ev.tick_end == Q
        assert ev.velocity == 64

    def test_accent_note(self, midi_data):
        # A3(57) vel=127 アクセント
        ev = next(e for e in midi_data.events if e.midi_note == 57 and e.tick_start == 480)
        assert ev.velocity == 127
        assert ev.tick_end == 960

    def test_ghost_dotted_quarter(self, midi_data):
        # Bb3(58) vel=20 ゴースト 付点4分
        ev = next(e for e in midi_data.events if e.midi_note == 58)
        assert ev.velocity == 20
        assert ev.tick_end - ev.tick_start == Qd

    def test_apex_marker(self, midi_data):
        # MIDI 0 = Apex マーカー
        ev = next(e for e in midi_data.events if e.midi_note == 0)
        assert ev.tick_start == 1920

    def test_slap_marker(self, midi_data):
        # MIDI 1 = Slap マーカー
        ev = next(e for e in midi_data.events if e.midi_note == 1)
        assert ev.tick_start == 2400

    def test_double_dotted_8th(self, midi_data):
        # G4(67) 二重付点8分
        ev = next(e for e in midi_data.events if e.midi_note == 67)
        assert ev.tick_end - ev.tick_start == Edd

    def test_half_note(self, midi_data):
        # D4(62) 2分音符
        ev = next(e for e in midi_data.events if e.midi_note == 62)
        assert ev.tick_end - ev.tick_start == H

    def test_double_dotted_quarter(self, midi_data):
        # A4(69) 二重付点4分
        ev = next(e for e in midi_data.events if e.midi_note == 69)
        assert ev.tick_end - ev.tick_start == Qdd


class TestReadMidiTrackIndex:
    def test_track_index_0_same_as_none(self):
        data_none = read_midi(FIXTURE_MID, track_index=None)
        data_0    = read_midi(FIXTURE_MID, track_index=0)
        assert len(data_none.events) == len(data_0.events)

    def test_track_index_out_of_range_exits(self):
        with pytest.raises(SystemExit):
            read_midi(FIXTURE_MID, track_index=99)


class TestReadMidiDefaults:
    def test_default_tempo_when_absent(self, tmp_path):
        # テンポ指定のない MIDI → デフォルト 500_000
        mid = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        track.append(mido.Message("note_on",  note=60, velocity=64, time=0))
        track.append(mido.Message("note_off", note=60, velocity=0,  time=480))
        mid.tracks.append(track)
        path = tmp_path / "no_tempo.mid"
        mid.save(str(path))

        data = read_midi(path)
        assert data.tempo_changes[0].tempo == 500_000

    def test_default_time_sig_when_absent(self, tmp_path):
        # 拍子指定のない MIDI → デフォルト 4/4
        mid = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        track.append(mido.Message("note_on",  note=60, velocity=64, time=0))
        track.append(mido.Message("note_off", note=60, velocity=0,  time=480))
        mid.tracks.append(track)
        path = tmp_path / "no_timesig.mid"
        mid.save(str(path))

        data = read_midi(path)
        ts = data.time_sig_changes[0]
        assert ts.numerator == 4
        assert ts.denominator == 4

    def test_format2_exits(self, tmp_path):
        mid = mido.MidiFile(type=2, ticks_per_beat=480)
        mid.tracks.append(mido.MidiTrack())
        path = tmp_path / "format2.mid"
        mid.save(str(path))

        with pytest.raises(SystemExit):
            read_midi(path)


# ---------------------------------------------------------------------------
# read_midi — エッジケース
# ---------------------------------------------------------------------------

def _save_mid(tmp_path, filename: str, messages: list) -> Path:
    mid = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    for msg in messages:
        track.append(msg)
    mid.tracks.append(track)
    path = tmp_path / filename
    mid.save(str(path))
    return path


class TestReadMidiEdgeCases:
    def test_note_on_velocity_zero_acts_as_note_off(self, tmp_path):
        # note_on vel=0 は note_off として扱われる
        path = _save_mid(tmp_path, "vel0.mid", [
            mido.Message("note_on", note=60, velocity=64, time=0),
            mido.Message("note_on", note=60, velocity=0,  time=480),
        ])
        data = read_midi(path)
        assert len(data.events) == 1
        ev = data.events[0]
        assert ev.midi_note == 60
        assert ev.tick_start == 0
        assert ev.tick_end == 480
        assert ev.velocity == 64

    def test_overlapping_same_note(self, tmp_path):
        # 同じノートを note_off なしで再打鍵: 2 発目の note_on が来た瞬間に 1 発目を閉じる
        path = _save_mid(tmp_path, "overlap.mid", [
            mido.Message("note_on",  note=60, velocity=64, time=0),
            mido.Message("note_on",  note=60, velocity=80, time=240),
            mido.Message("note_off", note=60, velocity=0,  time=240),
            mido.Message("note_off", note=60, velocity=0,  time=240),
        ])
        data = read_midi(path)
        assert len(data.events) == 2
        # 1 発目 (tick_start=0, vel=64) は 2 発目の note_on 到着 tick=240 で閉じられる
        first = next(e for e in data.events if e.tick_start == 0)
        assert first.velocity == 64
        assert first.tick_end == 240
        # 2 発目 (tick_start=240, vel=80) は 1 発目の note_off 到着 tick=480 で閉じられる
        second = next(e for e in data.events if e.tick_start == 240)
        assert second.velocity == 80
        assert second.tick_end == 480

    def test_unclosed_note_closed_at_last_tick(self, tmp_path):
        # note_off のないノートは最後のイベント tick で閉じる
        path = _save_mid(tmp_path, "unclosed.mid", [
            mido.Message("note_on",  note=60, velocity=64, time=0),
            mido.Message("note_on",  note=62, velocity=64, time=0),
            mido.Message("note_off", note=62, velocity=0,  time=960),
        ])
        data = read_midi(path)
        assert len(data.events) == 2
        ev60 = next(e for e in data.events if e.midi_note == 60)
        assert ev60.tick_end == 960  # 最後のイベント tick
