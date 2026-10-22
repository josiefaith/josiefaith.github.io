#!/usr/bin/env python3
"""Reopen original_piano_song.mid and check structure, timing and content."""
import os
import sys
from collections import defaultdict

from mido import MidiFile, tempo2bpm

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'original_piano_song.mid')
mid = MidiFile(path)
ppq = mid.ticks_per_beat
bar = ppq * 4
ok = True


def check(cond, msg):
    global ok
    print(('PASS ' if cond else 'FAIL ') + msg)
    ok &= bool(cond)


check(mid.type == 1, f'MIDI type = {mid.type}')
check(len(mid.tracks) == 2, f'{len(mid.tracks)} tracks: ' + ', '.join(repr(t.name) for t in mid.tracks))
check(ppq == 480, f'resolution = {ppq} PPQ')

tempos, sigs, keys, markers = [], [], [], []
t = 0
for m in mid.tracks[0]:
    t += m.time
    if m.type == 'set_tempo':
        tempos.append((t, round(tempo2bpm(m.tempo), 2)))
    elif m.type == 'time_signature':
        sigs.append((t, f'{m.numerator}/{m.denominator}'))
    elif m.type == 'key_signature':
        keys.append((t, m.key))
    elif m.type == 'marker':
        markers.append((t // bar + 1, m.text))
    elif m.type in ('note_on', 'note_off'):
        check(False, 'note event in tempo track')
check(sigs == [(0, '4/4')], f'time signature {sigs}')
check(keys == [(0, 'Eb')], f'key signature {keys}')
check(tempos[0] == (0, 96.0), f'tempo map {tempos}')

trk = mid.tracks[1]
t, on, notes, programs, cc64 = 0, {}, [], [], 0
channels = set()
for m in trk:
    t += m.time
    if m.type == 'program_change':
        programs.append(m.program)
    if m.type == 'control_change' and m.control == 64:
        cc64 += 1
    if m.type == 'note_on' and m.velocity > 0:
        channels.add(m.channel)
        check(m.note not in on, f'no double note-on (pitch {m.note} @ {t})') if m.note in on else None
        on[m.note] = (t, m.velocity)
    elif m.type in ('note_off', 'note_on'):
        if m.note in on:
            s, v = on.pop(m.note)
            notes.append((s, t, m.note, v))
track_end = t
check(programs == [0], f'program change(s) {programs} (0 = GM Acoustic Grand Piano)')
check(channels == {0}, f'channels used {sorted(channels)}')
check(not on, f'all notes released ({len(on)} hanging)')
check(len(notes) > 1000, f'{len(notes)} note events')
check(cc64 > 50, f'{cc64} sustain-pedal (CC64) events')

durs = [e - s for s, e, _, _ in notes]
check(min(durs) >= 30, f'note lengths {min(durs)}-{max(durs)} ticks')
pitches = [p for *_, p, _ in notes]
check(21 <= min(pitches) and max(pitches) <= 108, f'pitch range {min(pitches)}-{max(pitches)} (piano keyboard 21-108)')
vels = [v for *_, v in notes]
check(len(set(vels)) > 40, f'velocity range {min(vels)}-{max(vels)}, {len(set(vels))} distinct values')

end_tick = 80 * bar
last_off = max(e for _, e, _, _ in notes)
first_on = min(s for s, *_ in notes)
check(first_on == 0, f'first note at tick {first_on}')
check(end_tick - bar // 4 <= last_off <= end_tick, f'last note-off at tick {last_off} (bar 80 ends at {end_tick})')
check(track_end == end_tick and sum(m.time for m in mid.tracks[0]) == end_tick,
      f'both tracks end exactly at bar 80 ({end_tick} ticks)')
check(195 <= mid.length <= 205, f'duration {mid.length:.2f} s = {int(mid.length // 60)}:{mid.length % 60:05.2f}')

# bar-by-bar density, to show the arc and that no bar is empty
per_bar = defaultdict(lambda: [0, 0])
for s, _, _, v in notes:
    b = s // bar + 1
    per_bar[b][0] += 1
    per_bar[b][1] += v
check(all(per_bar[b][0] > 0 for b in range(1, 81)), 'every bar 1-80 contains notes')
print('\nSection markers and density (notes / mean velocity):')
starts = [b for b, _ in markers] + [81]
for (b, text), nxt in zip(markers, starts[1:]):
    cnt = sum(per_bar[x][0] for x in range(b, nxt))
    vel = sum(per_bar[x][1] for x in range(b, nxt)) / max(1, cnt)
    print(f'  bar {b:>2}: {text:<46} {cnt / (nxt - b):5.1f} notes/bar  vel {vel:5.1f}')
check([b for b, _ in markers] == [1, 5, 13, 17, 25, 27, 35, 39, 47, 55, 57, 65, 73],
      'section boundaries at bars 1,5,13,17,25,27,35,39,47,55,57,65,73')
sys.exit(0 if ok else 1)
