#!/usr/bin/env python3
"""Build chord_guide.mid: plain block chords for Logic's Chord Track detection.

Every chord is spelled in root position (root, 3rd, 5th, 7th, extensions) with the bass note
(the slash note on slash chords) alone underneath. Logic analyses that far more reliably than the
real piano part, whose voicings usually leave out the root.

Reads the chart from song.py and the tempo map from piano_only.mid. Writes chord_guide.mid.
Run: python3 generate_chord_guide.py   (needs: pip install mido)
"""
import os

from mido import Message, MetaMessage, MidiFile, MidiTrack

from song import BAR, CH, END, PPQ, QUALITY, S16, parse, timeline

HERE = os.path.dirname(os.path.abspath(__file__))
orig = MidiFile(os.path.join(HERE, 'piano_only.mid'))


def spell(chord):
    r, qual, bass, _ = parse(chord)
    assert bass == CH[chord][0], f'{chord}: bass disagrees with the chart'
    upper = [48 + r + iv for iv in QUALITY[qual]]   # root in C3-B3 (Logic: C2-B2)
    return 36 + bass, upper                         # bass in C2-B2 (Logic: C1-B1), always below


track = MidiTrack()
track.append(MetaMessage('track_name', name='Chord Guide (mute me)'))
track.append(Message('program_change', channel=4, program=0))
events = []
for bar, cells in sorted(timeline().items()):
    for st, ln, c in cells:
        t0 = (bar - 1) * BAR + st * S16
        t1 = min(t0 + ln * S16, END)
        off = t1 if t1 == END else t1 - 20             # tiny gap so each chord reads separately
        bass_note, upper = spell(c)
        for p in [bass_note] + upper:
            events.append((t0, 1, Message('note_on', channel=4, note=p, velocity=80)))
            events.append((off, 0, Message('note_off', channel=4, note=p, velocity=64)))
events.sort(key=lambda e: (e[0], e[1]))
now = 0
for t, _, m in events:
    track.append(m.copy(time=t - now))
    now = t
track.append(MetaMessage('end_of_track', time=END - now))

out = MidiFile(type=1, ticks_per_beat=PPQ)
cond = MidiTrack()
for m in orig.tracks[0]:
    cond.append(m.copy())
out.tracks.append(cond)
out.tracks.append(track)
path = os.path.join(HERE, 'chord_guide.mid')
out.save(path)
print(f'wrote {path}: {len(events) // 2} notes, {out.length:.2f} s')
