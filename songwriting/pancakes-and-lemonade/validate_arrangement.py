#!/usr/bin/env python3
"""Reopen every Pancakes and Lemonade MIDI file and check structure, alignment and musical sanity."""
import ast
import os
import sys
from collections import defaultdict

from mido import MidiFile, tempo2bpm

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = HERE
ok = True


def check(cond, msg):
    global ok
    print(('PASS ' if cond else 'FAIL ') + msg)
    ok &= bool(cond)


def notes_of(track):
    t, on, out, chans, ccs = 0, {}, [], set(), 0
    for m in track:
        t += m.time
        if m.type == 'note_on' and m.velocity > 0:
            on[(m.channel, m.note)] = (t, m.velocity)
            chans.add(m.channel)
        elif m.type in ('note_on', 'note_off') and (m.channel, m.note) in on:
            s, v = on.pop((m.channel, m.note))
            out.append((s, t, m.note, v))
        elif m.type == 'control_change':
            ccs += 1
    return out, chans, on, t, ccs


orig = MidiFile(os.path.join(SRC, 'piano_only.mid'))
full = MidiFile(os.path.join(HERE, 'full_song_multitrack.mid'))
PPQ = full.ticks_per_beat
BAR = PPQ * 4
BARS = 88
END = BARS * BAR

print('== full_song_multitrack.mid ==')
check(full.type == 1, f'Standard MIDI File type {full.type}')
names = [t.name for t in full.tracks]
check(names == ['Tempo & Meter', 'Grand Piano', 'Drums (Brushes)', 'Drums (Sticks)', 'Bass', 'Organ', 'Shaker & Tambourine'],
      f'{len(names)} tracks: {names}')
check(PPQ == 480, f'{PPQ} PPQ')

t, tempos, sigs, keys, marks = 0, [], [], [], []
for m in full.tracks[0]:
    t += m.time
    if m.type == 'set_tempo':
        tempos.append((t // BAR + 1, round(tempo2bpm(m.tempo), 1)))
    elif m.type == 'time_signature':
        sigs.append((t, f'{m.numerator}/{m.denominator}'))
    elif m.type == 'key_signature':
        keys.append((t, m.key))
    elif m.type == 'marker':
        marks.append(t // BAR + 1)
check(sigs == [(0, '4/4')] and keys == [(0, 'Eb')], f'meter {sigs}, key {keys}')
check(tempos[0] == (1, 96.0) and len(tempos) == 5, f'tempo map (bar, BPM): {tempos}')
check(marks == [1, 5, 13, 21, 25, 33, 35, 43, 47, 55, 63, 65, 73, 81], f'section markers at bars {marks}')
check(215 <= full.length <= 225, f'duration {full.length:.2f} s ({int(full.length // 60)}:{full.length % 60:05.2f})')

EXPECT = {'Grand Piano': ({0}, 0), 'Drums (Brushes)': ({9}, 40), 'Drums (Sticks)': ({9}, 0), 'Bass': ({1}, 33), 'Organ': ({2}, 16),
          'Shaker & Tambourine': ({9}, 0)}
data = {}
for tr in full.tracks[1:]:
    ns, chans, hanging, end, ccs = notes_of(tr)
    progs = [m.program for m in tr if m.type == 'program_change']
    data[tr.name] = ns
    exp_ch, exp_prog = EXPECT[tr.name]
    check(chans == exp_ch and progs == [exp_prog],
          f'{tr.name:<20} channel {sorted(c + 1 for c in chans)}, program {[p + 1 for p in progs]} (1-based GM), '
          f'{len(ns)} notes, {ccs} CCs')
    check(not hanging and end == END, f'{tr.name:<20} no hanging notes; track ends at bar {BARS} ({end} ticks)')
    check(all(0 <= s < e <= END for s, e, _, _ in ns), f'{tr.name:<20} all notes inside bars 1-{BARS}')
    check(min(e - s for s, e, _, _ in ns) >= 25, f'{tr.name:<20} note lengths >= 25 ticks')

check([m for m in full.tracks[1]] == [m for m in orig.tracks[1]], 'piano track identical to piano_only.mid, event for event')
check([m for m in full.tracks[0]] == [m for m in orig.tracks[0]], 'tempo/meter/marker track identical to piano_only.mid')

GM = {36, 37, 38, 42, 43, 44, 45, 46, 48, 49, 51, 53, 54, 82}
drums = data['Drums (Brushes)'] + data['Drums (Sticks)']
check({p for *_, p, _ in drums} <= GM, f'drum notes all in documented GM map: {sorted({p for *_, p, _ in drums})}')
check({p for *_, p, _ in data['Shaker & Tambourine']} <= {54, 82}, 'aux track uses only tambourine 54 / shaker 82')
dv = [v for *_, v in drums]
check(min(dv) >= 15 and max(dv) <= 120 and len(set(dv)) > 50, f'drum velocities {min(dv)}-{max(dv)}, {len(set(dv))} distinct')
bp = [p for *_, p, _ in data['Bass']]
check(28 <= min(bp) and max(bp) <= 55, f'bass range {min(bp)}-{max(bp)} (4-string E1-G3 = 28-55)')

# every instrument ends together on the last downbeat
for nm in ('Grand Piano', 'Drums (Brushes)', 'Bass', 'Organ'):
    last_on = max(s for s, *_ in data[nm])
    check(last_on // BAR + 1 == BARS, f'{nm:<20} last note starts in the last bar')
check(max(e for nm in data for _, e, _, _ in data[nm]) == END, f'final notes end exactly at the end of bar {BARS} (no trailing silence)')

# ---- musical checks against the chord chart ----
tree = ast.parse(open(os.path.join(SRC, 'generate_piano.py')).read())
ns = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in
            {'CH', 'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'} for t in node.targets):
        exec(compile(ast.Module([node], []), 'g', 'exec'), ns)
timeline, bar = {}, 1
for _, _, chords, _, _ in ns['FORM']:
    for bc in chords:
        half = 16 // len(bc)
        timeline[bar] = [(k * half, half, c) for k, c in enumerate(bc)]
        bar += 1


def chord_at(tk):
    b, pos = tk // BAR + 1, (tk % BAR) / (PPQ / 4)
    for st, ln, c in timeline[b]:
        if st <= pos < st + ln:
            return c, pos - st
    return timeline[b][-1][2], 0


CH = ns['CH']
wrong_root = sum(1 for s, _, p, _ in data['Bass']
                 if chord_at(s + 8)[1] < 0.5 and p % 12 != CH[chord_at(s + 8)[0]][0])
starts = sum(1 for s, *_ in data['Bass'] if chord_at(s + 8)[1] < 0.5)
check(wrong_root == 0, f'bass plays the chord\'s bass note on every chord change ({starts} changes checked)')
out_bass = [(s // BAR + 1, round((s % BAR) / 120, 1), p, chord_at(s + 8)[0]) for s, _, p, _ in data['Bass']
            if p % 12 not in set(CH[chord_at(s + 8)[0]][1]) | {CH[chord_at(s + 8)[0]][0],
                                 (CH[chord_at(s + 8)[0]][0] + CH[chord_at(s + 8)[0]][2]) % 12}
            and (s + 8) % BAR // 120 != 14]
check(len(out_bass) == 0, f'bass non-chord tones (outside the original piano chord + LH notes) only as pickups on the last 16th-pair of a bar ({len(out_bass)} elsewhere{": " + str(out_bass) if out_bass else ""})')
out_org = [s for s, _, p, _ in data['Organ'] if p % 12 not in set(CH[chord_at(s + 8)[0]][1])]
check(len(out_org) == 0, f'organ plays only chord tones ({len(data["Organ"])} notes checked)')

kick_ticks = [s for s, _, p, _ in drums if p == 36]
locked = sum(1 for k in kick_ticks if any(abs(k - s) <= 12 for s, *_ in data['Bass']))
check(locked / len(kick_ticks) > 0.7, f'kick/bass lock: {locked}/{len(kick_ticks)} kicks land with a bass note')

print('\nPer-section density (notes per bar):')
print(f'  {"section":<34}' + ''.join(f'{n[:7]:>9}' for n in data))
sec_bounds = marks + [BARS + 1]
t = 0
labels = [m.text for m in full.tracks[0] if m.type == 'marker']
for k, (a, b) in enumerate(zip(sec_bounds, sec_bounds[1:])):
    row = []
    for nm in data:
        c = sum(1 for s, *_ in data[nm] if a <= s // BAR + 1 < b)
        row.append(f'{c / (b - a):9.1f}')
    print(f'  {labels[k][:34]:<34}' + ''.join(row))

# brushes and sticks never play at the same time (bar 76 hands over mid-bar)
bb = {s // BAR + 1 for s, *_ in data['Drums (Brushes)']}
sb = {s // BAR + 1 for s, *_ in data['Drums (Sticks)']}
check(bb & sb <= {76}, f'brushes and sticks never overlap (shared bars: {sorted(bb & sb)})')
check(min(bb) == 3 and max(bb | sb) == BARS and len(set(range(3, BARS + 1)) - bb - sb) == 0,
      'drums play in every bar from bar 3 to the end (bars 1-2 are piano alone)')
check(set(range(3, 43)) <= bb and min(sb) == 43, f'brushes from bar 3 to bar 42, sticks enter at bar {min(sb)}')


def energy(a, b):
    n = [x for nm in ('Grand Piano', 'Drums (Brushes)', 'Drums (Sticks)', 'Bass', 'Organ')
         for x in data[nm] if a <= x[0] // BAR + 1 <= b]
    return len(n) / (b - a + 1), sum(x[3] for x in n) / len(n)


c1, c2, fin = energy(25, 32), energy(47, 54), energy(65, 72)
check(c1[0] < c2[0] and c1[1] < c2[1] < fin[1] + 0.01,
      f'arc: chorus 1 {c1[0]:.0f} notes/bar @ vel {c1[1]:.0f} < chorus 2 {c2[0]:.0f} @ {c2[1]:.0f} '
      f'<= final chorus {fin[0]:.0f} @ {fin[1]:.0f}')

print('\n== single-instrument files ==')
for fn, nms in [('piano_only.mid', ['Grand Piano']), ('drums_only.mid', ['Drums (Brushes)', 'Drums (Sticks)']),
                ('bass_only.mid', ['Bass']), ('organ_only.mid', ['Organ']),
                ('aux_percussion_only.mid', ['Shaker & Tambourine'])]:
    f = MidiFile(os.path.join(HERE, fn))
    same = all([m for m in f.tracks[k + 1]] == [m for m in full.tracks[names.index(nm)]] for k, nm in enumerate(nms))
    same_cond = [m for m in f.tracks[0]] == [m for m in full.tracks[0]]
    check(f.type == 1 and len(f.tracks) == 1 + len(nms) and same and same_cond and abs(f.length - full.length) < 0.01,
          f'{fn:<24} type 1, conductor + {nms}, matches the multitrack, {f.length:.2f} s')

sys.exit(0 if ok else 1)
