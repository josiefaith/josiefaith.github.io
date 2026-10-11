#!/usr/bin/env python3
"""Build chord_guide.mid: plain block chords for Logic's Chord Track detection.

Every chord is spelled in full root position (root, 3rd, 5th, 7th, extensions),
with the bass note (the slash note on slash chords) alone underneath. That is
much easier for Logic to analyse than the real piano part, whose jazz
voicings usually leave out the root.

Reads the chord chart from generate_piano.py and the tempo map from
piano_only.mid. Writes chord_guide.mid next to this script.
Run: python3 generate_chord_guide.py   (needs: pip install mido)
"""
import ast
import os
import re

from mido import Message, MetaMessage, MidiFile, MidiTrack

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = HERE
orig = MidiFile(os.path.join(SRC_DIR, 'piano_only.mid'))
PPQ = orig.ticks_per_beat
S16 = PPQ // 4
BAR = S16 * 16
END = sum(m.time for m in orig.tracks[1])

tree = ast.parse(open(os.path.join(SRC_DIR, 'generate_piano.py')).read())
ns = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in
            {'CH', 'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'}
            for t in node.targets):
        exec(compile(ast.Module([node], []), 'src', 'exec'), ns)
CH, FORM = ns['CH'], ns['FORM']

PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
QUALITY = {  # semitones above the root
    '': (0, 4, 7), 'maj7': (0, 4, 7, 11), 'maj9': (0, 4, 7, 11, 14),
    'maj7#11': (0, 4, 7, 11, 18), 'm7': (0, 3, 7, 10), 'm9': (0, 3, 7, 10, 14),
    'm11': (0, 3, 7, 10, 14, 17), 'm6': (0, 3, 7, 9), 'm7b5': (0, 3, 6, 10),
    'dim7': (0, 3, 6, 9), '9': (0, 4, 7, 10, 14), '7b9': (0, 4, 7, 10, 13),
    '9sus4': (0, 5, 7, 10, 14), '13': (0, 4, 7, 10, 14, 21),
}


def pc_of(name):
    p = PC[name[0]] - name[1:].count('b')
    return p % 12


def spell(chord):
    m = re.fullmatch(r'([A-G]b?)([^/]*)(?:/([A-G]b?))?', chord)
    root, qual, slash = m.group(1), m.group(2), m.group(3)
    r = pc_of(root)
    bass = pc_of(slash) if slash else r
    assert bass == CH[chord][0], f'{chord}: bass disagrees with the original chart'
    root_note = 48 + r                     # C3-B3 in standard numbering (Logic: C2-B2)
    upper = [root_note + iv for iv in QUALITY[qual]]
    bass_note = 36 + bass                  # C2-B2 (Logic: C1-B1), always below the chord
    return bass_note, upper


track = MidiTrack()
track.append(MetaMessage('track_name', name='Chord Guide (mute me)'))
track.append(Message('program_change', channel=4, program=0))
track.append(Message('control_change', channel=4, control=7, value=90))
events, bar = [], 1
for _, _, chords, _, _ in FORM:
    for bc in chords:
        half = 16 // len(bc)
        for k, c in enumerate(bc):
            t0 = (bar - 1) * BAR + k * half * S16
            t1 = min(t0 + half * S16, END)
            off = t1 if t1 == END else t1 - 20     # tiny gap so each chord reads separately
            bass_note, upper = spell(c)
            for p in [bass_note] + upper:
                events.append((t0, 1, Message('note_on', channel=4, note=p, velocity=80)))
                events.append((off, 0, Message('note_off', channel=4, note=p, velocity=64)))
        bar += 1
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
print(f'wrote {path}: {bar - 1} bars, {len(events) // 2} notes, {out.length:.2f} s')
