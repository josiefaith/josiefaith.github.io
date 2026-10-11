#!/usr/bin/env python3
"""Build the band arrangement for "Pancakes and Lemonade" around piano_only.mid.

Reads (never writes):
  piano_only.mid        the piano part, tempo map, meter, key and markers
  generate_piano.py     the chord chart and section list (read as data)

Writes, next to this script:
  full_song_multitrack.mid   Type 1: Tempo & Meter, Grand Piano, Drums (Brushes),
                             Drums (Sticks), Bass, Organ, Shaker & Tambourine
  drums_only.mid             both drum tracks
  bass_only.mid, organ_only.mid, aux_percussion_only.mid
  drum_map.md                every drum note used, with velocity conventions

Requires: pip install mido.  Run: python3 generate_piano.py && python3 generate_arrangement.py
The random seed is fixed, so every run produces identical files.
"""
import ast
import itertools
import os
import random
from collections import Counter

from mido import Message, MetaMessage, MidiFile, MidiTrack

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_MID = os.path.join(HERE, 'piano_only.mid')
SRC_PY = os.path.join(HERE, 'generate_piano.py')
random.seed(19960)

# ---------- 1. read the existing song ----------
orig = MidiFile(SRC_MID)
assert orig.type == 1 and len(orig.tracks) == 2, 'unexpected layout in original MIDI'
PPQ = orig.ticks_per_beat
S16 = PPQ // 4
BAR = S16 * 16

# chord chart + form, taken from the original generator without running it
tree = ast.parse(open(SRC_PY).read())
WANT = {'PC', 'CH', 'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'}
ns = {'itertools': itertools}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in WANT for t in node.targets):
        exec(compile(ast.Module([node], []), SRC_PY, 'exec'), ns)
    if isinstance(node, ast.FunctionDef) and node.name == 'voice':
        exec(compile(ast.Module([node], []), SRC_PY, 'exec'), ns)
CH, FORM, voice = ns['CH'], ns['FORM'], ns['voice']

# time signature, key, tempo and markers from the original conductor track
t, markers, meta = 0, [], {}
for m in orig.tracks[0]:
    t += m.time
    if m.type == 'marker':
        markers.append((t // BAR + 1, m.text))
    elif m.type in ('time_signature', 'key_signature') and t == 0:
        meta[m.type] = m
assert meta['time_signature'].numerator == 4 and meta['time_signature'].denominator == 4
END = sum(m.time for m in orig.tracks[1])           # end of the piano track = end of the last bar

# section list, cross-checked against the markers in the MIDI
SECTIONS, bar_no = [], 1
for name, style, chords, v0, v1 in FORM:
    SECTIONS.append({'name': name, 'style': style, 'start': bar_no, 'chords': chords})
    bar_no += len(chords)
TOTAL_BARS = bar_no - 1
assert [s['start'] for s in SECTIONS] == [b for b, _ in markers], 'form and markers disagree'
assert END == TOTAL_BARS * BAR, 'piano track does not end on the last barline'

# per-bar chord timeline: bar -> [(start16, len16, chord name)]
TIMELINE = {}
for s in SECTIONS:
    for i, bc in enumerate(s['chords']):
        half = 16 // len(bc)
        TIMELINE[s['start'] + i] = [(k * half, half, c) for k, c in enumerate(bc)]

# ---------- 2. helpers ----------
KICK, SIDESTICK, SNARE = 36, 37, 38
HH_CLOSED, HH_PEDAL, HH_OPEN = 42, 44, 46
TOM_FLOOR, TOM_LOW, TOM_HIGH = 43, 45, 48
CRASH, RIDE, RIDE_BELL = 49, 51, 53
TAMBOURINE, SHAKER = 54, 82
DRUM_NAMES = {KICK: 'Acoustic Bass Drum / Kick', SIDESTICK: 'Side Stick (cross-stick)',
              SNARE: 'Acoustic Snare', HH_CLOSED: 'Closed Hi-Hat', HH_PEDAL: 'Pedal Hi-Hat',
              HH_OPEN: 'Open Hi-Hat', TOM_FLOOR: 'High Floor Tom', TOM_LOW: 'Low Tom',
              TOM_HIGH: 'Hi-Mid Tom', CRASH: 'Crash Cymbal 1', RIDE: 'Ride Cymbal 1',
              RIDE_BELL: 'Ride Bell', TAMBOURINE: 'Tambourine', SHAKER: 'Shaker'}

parts = {k: [] for k in ('brushes', 'drums', 'bass', 'organ', 'aux')}   # (tick, note, dur, vel)
ccs = {k: [] for k in parts}                                 # (tick, controller, value)


def tick(bar, pos):
    return int((bar - 1) * BAR + pos * S16)


def clampv(v):
    return max(1, min(127, int(round(v))))


def hit(part, bar, pos, note, vel, dur16=1.0, jitter=4):
    """One note. pos is in sixteenths (may be fractional). Small human timing drift."""
    t0 = tick(bar, pos)
    if jitter:
        lo = 0 if pos == 0 else -jitter               # downbeats never early
        t0 += random.randint(lo, jitter)
    t0 = max(0, min(t0, END - 30))
    dur = max(30, min(int(dur16 * S16), END - t0))
    parts[part].append((t0, note, dur, clampv(vel + random.randint(-4, 4))))


def ramp(part, bar0, pos0, bar1, pos1, ctrl, v0, v1, step=S16):
    a, b = tick(bar0, pos0), min(tick(bar1, pos1), END)
    for x in range(a, b + 1, step):
        f = (x - a) / max(1, b - a)
        ccs[part].append((x, ctrl, clampv(v0 + (v1 - v0) * f)))


def chords_of(bar):
    return TIMELINE[bar]


def chord_at(bar, pos):
    for st, ln, c in TIMELINE[bar]:
        if st <= pos < st + ln:
            return c
    return TIMELINE[bar][-1][2]


# ---------- 3. drums (GM channel 10) ----------
def hats(bar, base, step=2, note=HH_CLOSED, skip=(), until=16):
    for pos in range(0, until, step):
        if pos in skip:
            continue
        v = base if pos % 4 == 0 else base - (12 if pos % 2 == 0 else 22)
        hit('drums', bar, pos, note, v)


def ride(bar, base, step=2, skip=(), bell_quarters=False):
    for pos in range(0, 16, step):
        if pos in skip:
            continue
        if bell_quarters and pos % 4 == 0:
            hit('drums', bar, pos, RIDE_BELL, base - 6)
        else:
            hit('drums', bar, pos, RIDE, base if pos % 4 == 0 else base - 10)


def kicks(bar, positions, v):
    for p in positions:
        hit('drums', bar, p, KICK, v if p in (0, 8) else v - 10)


def backbeat(bar, v, note=SNARE, positions=(4, 12)):
    for p in positions:
        hit('drums', bar, p, note, v)


# Bars on brushes: everything up to the end of verse 3, the pulled-back chorus, the outro.
BRUSH_SECTIONS = {'Intro', 'Verse 1', 'Verse 2', 'Pre-Chorus 1', 'Chorus 1', 'Turnaround', 'Verse 3', 'Outro'}
BRUSH_BARS = set()
for _s in SECTIONS:
    for _i in range(len(_s['chords'])):
        if _s['name'] in BRUSH_SECTIONS or (_s['style'] == 'lift' and _i < 4):
            BRUSH_BARS.add(_s['start'] + _i)


def sweep(bar, lv, step=2, until=16, skip=()):
    """Soft brush strokes on the snare between the backbeats (the 'swish' of a brush groove)."""
    for pos in range(0, until, step):
        if pos in (4, 12) or pos in skip:
            continue
        v = lv - 28 if pos % 4 == 0 else (lv - 32 if pos % 2 == 0 else lv - 40)
        hit('brushes', bar, pos, SNARE, max(20, v), jitter=5)


def bkick(bar, positions, lv):
    for p in positions:
        hit('brushes', bar, p, KICK, lv if p in (0, 8) else lv - 10)


def btap(bar, lv, positions=(4, 12)):
    for p in positions:
        hit('brushes', bar, p, SNARE, lv)


def foot(bar, lv, positions=(4, 12)):
    for p in positions:
        hit('brushes', bar, p, HH_PEDAL, lv)


def brushes_for(sec, i, bar):
    st, name, n = sec['style'], sec['name'], len(sec['chords'])
    two = len(chords_of(bar)) == 2
    last = i == n - 1

    if st == 'intro':                                  # piano alone for two bars, then a whisper
        if i == 2:
            bkick(bar, [0], 46)
            sweep(bar, 52)
        elif i == 3:
            sweep(bar, 54, until=12)
            for pos, v in ((12, 36), (14, 46), (15, 54)):
                hit('brushes', bar, pos, SNARE, v)

    elif name == 'Verse 1':                            # the lightest groove in the song
        lv = 56
        bkick(bar, [0, 6, 8] if two else [0, 6], lv + 6)
        btap(bar, lv)
        foot(bar, lv - 18)
        if last:
            sweep(bar, lv, until=14)
            hit('brushes', bar, 14, SNARE, lv - 14)
            hit('brushes', bar, 15, SNARE, lv - 8)
        else:
            sweep(bar, lv)

    elif name == 'Verse 2':                            # same feel, 16th strokes, kick pickups
        lv = 60
        bkick(bar, [0, 6, 8, 14] if two else ([0, 6, 10] if i % 2 else [0, 6]), lv + 6)
        btap(bar, lv)
        foot(bar, lv - 18)
        if last:
            sweep(bar, lv, step=1, until=12)
            for pos, v in ((13, 44), (14, 52), (15, 60)):
                hit('brushes', bar, pos, SNARE, v)
        else:
            sweep(bar, lv, step=1)

    elif st == 'pre':                                  # pre-chorus 1, still brushes, building
        lv = 62 + 4 * i
        if not last:
            bkick(bar, [0, 6, 8], lv + 6)
            btap(bar, lv + 2)
            sweep(bar, lv, step=1 if i else 2)
            if i >= 1:
                for pos in range(0, 16, 2):
                    hit('brushes', bar, pos, HH_CLOSED, lv - (20 if pos % 4 == 0 else 30))
        else:                                          # stop on beat 4 with the piano's breath
            bkick(bar, [0, 6, 8, 12], lv + 6)
            btap(bar, lv + 2, (4,))
            sweep(bar, lv, step=1, until=11)
            hit('brushes', bar, 12, SNARE, lv + 10)
            hit('brushes', bar, 15, SNARE, 46)

    elif st == 'chorus_light':                         # chorus 1: a lift, not a wall
        lv = 68 + (3 if i % 4 == 0 else 0)
        if i == 0:
            hit('brushes', bar, 0, CRASH, 54, dur16=8)
        if last:
            bkick(bar, [0, 6], lv + 4)
            btap(bar, lv, (4,))
            hit('brushes', bar, 12, SNARE, 48)
            sweep(bar, lv - 4, until=10)
            return
        kp = [0, 6, 8, 14] if two else [0, 6, 8] + ([11] if i % 2 else [])
        bkick(bar, kp, lv + 6)
        btap(bar, lv)
        sweep(bar, lv, step=1)
        foot(bar, lv - 20)
        for p in (0, 4, 8, 12):
            if not (i == 0 and p == 0):
                hit('brushes', bar, p, RIDE, lv - 22)

    elif st == 'turn':
        bkick(bar, [0] if i == 0 else [0, 10], 56)
        btap(bar, 52, (12,) if i == 0 else (4, 12))
        sweep(bar, 52)

    elif st == 'verse2':                               # verse 3: busiest brush groove, shaker joins
        lv = 60 + i
        if two:
            bkick(bar, [0, 6, 8, 14], lv + 6)
        else:
            bkick(bar, [0, 6, 10, 14] if i % 2 else [0, 6, 10], lv + 6)
        btap(bar, lv + 2)
        foot(bar, lv - 18)
        if last:                                       # swell into the sticks at pre-chorus 2
            sweep(bar, lv, step=1, until=8)
            for pos in range(8, 16):
                hit('brushes', bar, pos, SNARE, 40 + (pos - 8) * 6, jitter=2)
        else:
            sweep(bar, lv, step=1)

    elif st == 'lift':                                 # the stripped-down chorus: half-time brushes
        bkick(bar, [0], 50)
        hit('brushes', bar, 8, SNARE, 52)
        foot(bar, 34, (0, 4, 8, 12))
        if i == 3:                                     # sticks come back with the fill
            sweep(bar, 50, until=8, skip=(8,))
            for pos, note, v in [(8, SNARE, 62), (10, SNARE, 72), (12, TOM_HIGH, 82),
                                 (13, TOM_HIGH, 86), (14, TOM_LOW, 92), (15, TOM_FLOOR, 102)]:
                hit('drums', bar, pos, note, v, jitter=3)
            hit('drums', bar, 12, KICK, 80)
        else:
            sweep(bar, 50, skip=(8,))

    elif st == 'outro':
        lv = 56 - 3 * i
        if i < 4:
            bkick(bar, [0], lv + 4)
            btap(bar, lv)
            foot(bar, lv - 16)
            sweep(bar, lv)
        elif i < 6:
            bkick(bar, [0], lv)
            sweep(bar, lv + 4)
        elif i == 6:
            bkick(bar, [0], lv)
            sweep(bar, lv + 4, until=10)
        else:                                          # last downbeat: everyone lands together
            hit('brushes', bar, 0, KICK, 58, jitter=0)
            hit('brushes', bar, 0, RIDE, 50, dur16=16, jitter=0)


def drums_for(sec, i, bar):
    if bar in BRUSH_BARS:
        brushes_for(sec, i, bar)
        return
    st, n = sec['style'], len(sec['chords'])
    two = len(chords_of(bar)) == 2
    last = i == n - 1
    name = sec['name']

    if st == 'pre':                                 # real snare arrives, hats tighten, crescendo
        lv = 66 + 6 * i + (6 if name.endswith('2') else 0)
        if not last:
            kicks(bar, [0, 6, 8], lv + 10)
            backbeat(bar, lv + 6)
            hats(bar, lv - 4, step=1 if i == 2 else 2)
        elif name.endswith('1'):                      # pre 1: the band stops on beat 4 with the piano breath
            kicks(bar, [0, 6, 8, 12], lv + 10)
            backbeat(bar, lv + 6, positions=(4,))
            hit('drums', bar, 12, SNARE, lv + 14)
            hats(bar, lv - 4, until=11)
            hit('drums', bar, 15, SNARE, 50)
        else:                                         # pre 2: a proper tom fill
            kicks(bar, [0, 6, 8, 12], lv + 8)
            backbeat(bar, lv + 6, positions=(4,))
            hats(bar, lv - 4, until=8)
            for pos, note, v in [(8, SNARE, 78), (9, SNARE, 58), (10, SNARE, 84), (11, TOM_HIGH, 80),
                                 (12, TOM_HIGH, 84), (13, TOM_LOW, 86), (14, TOM_FLOOR, 92), (15, TOM_FLOOR, 98)]:
                hit('drums', bar, pos, note, v, jitter=3)

    elif st in ('chorus', 'final') or (st == 'lift' and i >= 4):
        big = st != 'chorus'
        second = name == 'Chorus 2'
        lv = (96 if big else 84) + (6 if second else 0) + (i % 4 == 0) * 4
        crash = (i in (0, 4)) if st != 'lift' else i == 4
        if crash:
            hit('drums', bar, 0, CRASH, lv + 14, dur16=8)
        if last and st != 'chorus' or (last and second):
            pass                                      # handled below
        elif last:                                    # chorus 1 -> turnaround: thin out under the piano's answer
            kicks(bar, [0, 6], lv + 6)
            backbeat(bar, lv + 4, positions=(4,))
            hit('drums', bar, 12, SNARE, 58)
            hats(bar, lv - 14, until=13)
            return
        if last and second:                           # chorus 2 -> bridge: fill that falls away
            kicks(bar, [0, 6, 8], lv + 8)
            backbeat(bar, lv + 6, positions=(4,))
            ride(bar, lv - 14, skip=range(10, 16))
            for pos, note, v in [(10, SNARE, 82), (11, SNARE, 66), (12, TOM_HIGH, 84),
                                 (13, TOM_LOW, 80), (14, TOM_FLOOR, 76), (15, TOM_FLOOR, 68)]:
                hit('drums', bar, pos, note, v, jitter=3)
            return
        if last:                                      # final choruses end on the piano's answer phrase
            kicks(bar, [0, 6], lv + 6)
            backbeat(bar, lv + 4, positions=(4,))
            ride(bar, lv - 16, skip=range(8, 16))
            hit('drums', bar, 12, RIDE_BELL, 58)
            return
        kp = [0, 6, 8] + ([11] if i % 2 else []) + ([14] if big and i % 2 else [])
        if two:
            kp = [0, 6, 8, 14]
        kicks(bar, kp, lv + 8)
        backbeat(bar, lv + 8)
        if i % 2 or big:
            hit('drums', bar, 7, SNARE, 30)
            hit('drums', bar, 15, SNARE, 26)
        skip = (0,) if crash else ()
        if second or big:
            ride(bar, lv - 12, skip=skip, bell_quarters=big)
        else:
            hats(bar, lv - 10, skip=skip)
            if i in (3, 7):
                hit('drums', bar, 14, HH_OPEN, lv - 12, dur16=2)

    elif st == 'bridge':
        if i < 4:                                     # half-time: snare only on beat 3, ride quarters
            if i == 0:
                hit('drums', bar, 0, CRASH, 68, dur16=12)
            kicks(bar, [0, 10], 70)
            hit('drums', bar, 8, SNARE, 72)
            for p in (0, 4, 8, 12):
                if not (i == 0 and p == 0):
                    hit('drums', bar, p, RIDE, 50)
            hit('drums', bar, 4, HH_PEDAL, 42)
            hit('drums', bar, 12, HH_PEDAL, 42)
        else:                                         # the climb back
            lv = 74 + (i - 4) * 9
            if i == 4:
                kicks(bar, [0, 8], lv + 8)
                backbeat(bar, lv)
                hats(bar, lv - 6)
            elif i == 5:
                kicks(bar, [0, 6, 8], lv + 8)
                backbeat(bar, lv)
                hats(bar, lv - 6)
            elif i == 6:
                kicks(bar, [0, 6, 8, 14], lv + 8)
                backbeat(bar, lv)
                hats(bar, lv - 6, step=1)
            else:
                kicks(bar, [0, 2, 4, 6, 8, 12], lv + 6)
                backbeat(bar, lv, positions=(4,))
                hats(bar, lv - 6, until=8)
                for pos in range(8, 16):              # snare roll into the breakdown hit
                    hit('drums', bar, pos, SNARE, 64 + (pos - 8) * 6, jitter=2)

    elif st == 'breakdown':
        if i == 0:                                    # one big hit, then the room empties
            hit('drums', bar, 0, CRASH, 104, dur16=16)
            hit('drums', bar, 0, KICK, 100)
        else:
            hit('drums', bar, 0, HH_PEDAL, 36)
            hit('drums', bar, 4, HH_PEDAL, 36)
            for pos in range(8, 16):                  # build into the final chorus
                hit('drums', bar, pos, SNARE, 46 + (pos - 8) * 9, jitter=2)
            kicks(bar, [8, 12], 92)



# ---------- 4. shaker & tambourine (also channel 10, own track) ----------
def aux_for(sec, i, bar):
    st, name, last = sec['style'], sec['name'], i == len(sec['chords']) - 1
    if st == 'verse2' and i >= 2:
        for pos in range(16):
            hit('aux', bar, pos, SHAKER, 46 if pos % 4 == 0 else (36 if pos % 2 == 0 else 26), jitter=3)
    elif st == 'pre' and name.endswith('2'):
        for pos in range(16 if not last else 8):
            hit('aux', bar, pos, SHAKER, 44 + i * 4 + (8 if pos % 2 == 0 else 0), jitter=3)
    elif name == 'Chorus 2' and not last:
        for pos in range(16):
            hit('aux', bar, pos, SHAKER, 50 if pos % 4 == 0 else (40 if pos % 2 == 0 else 30), jitter=3)
    elif (st == 'final' or (st == 'lift' and i >= 4)) and not last:
        for p in (4, 12):
            hit('aux', bar, p, TAMBOURINE, 74)
        for pos in range(0, 16, 2):
            if pos not in (4, 12):
                hit('aux', bar, pos, TAMBOURINE, 38, jitter=3)


# ---------- 5. bass (GM 34 Electric Bass (finger), channel 2) ----------
EB_SCALE = {3, 5, 7, 8, 10, 0, 2}
bass_prev = 39


def bass_pitch(chord):
    global bass_prev
    pc = CH[chord][0]
    cands = [p for p in range(28, 48) if p % 12 == pc]
    bass_prev = min(cands, key=lambda p: (abs(p - bass_prev), p))
    return bass_prev


def second(chord, root):
    """Safe second note above the bass: the original's LH interval (5th, or octave on slash chords)."""
    iv = CH[chord][2]
    return root + iv if root + iv <= 52 else root + iv - 12


def approach(bar, root):
    """Step into the next bar's bass from a scale tone below (or chromatic if needed)."""
    if bar >= TOTAL_BARS:
        return None
    nxt_pc = CH[TIMELINE[bar + 1][0][2]][0]
    target = min((p for p in range(28, 48) if p % 12 == nxt_pc), key=lambda p: abs(p - root))
    for cand in (target - 2, target - 1, target + 2, target + 1):
        if cand % 12 in EB_SCALE and cand != root and 28 <= cand <= 50:
            return cand
    return target - 1


def b(bar, pos, pitch, dur16, vel, gap=0.9):
    hit('bass', bar, pos, pitch, vel, dur16=dur16 * gap, jitter=3)


def bass_for(sec, i, bar, lv):
    st, n = sec['style'], len(sec['chords'])
    if sec['name'] == 'Verse 2':
        st = 'verse2'                                 # second pass: the bass steps up
    cs = chords_of(bar)
    last = i == n - 1
    roots = [(s, l, c, bass_pitch(c)) for s, l, c in cs]
    r0 = roots[0][3]

    if st == 'intro':
        if i == 2:
            b(bar, 0, r0, 16, lv - 6, gap=0.97)
        elif i == 3:
            b(bar, 0, r0, 12, lv - 4)
            a = approach(bar, r0)
            b(bar, 14, a, 2, lv - 10)

    elif st in ('verse', 'verse2'):
        if len(roots) == 2:
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 5, lv + 6)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 5 if st == 'verse2' else 6, lv + 2)
            if st == 'verse2' or last:
                b(bar, 14, approach(bar, r2), 2, lv - 8)
        else:
            c = roots[0][2]
            b(bar, 0, r0, 5, lv + 6)
            b(bar, 6, r0, 2, lv - 6)
            if st == 'verse':
                b(bar, 10, second(c, r0), 2, lv - 10)
                if i in (3, 7):
                    b(bar, 14, approach(bar, r0), 2, lv - 10)
            elif i % 2:
                b(bar, 8, second(c, r0), 3, lv - 4)
                b(bar, 11, r0, 2, lv - 8)
                b(bar, 14, approach(bar, r0), 2, lv - 8)
            else:
                b(bar, 10, second(c, r0), 2, lv - 8)
                b(bar, 12, r0, 3, lv - 6)

    elif st == 'chorus_light':                        # chorus 1: long notes, room to breathe
        if last:
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 5, lv + 4)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 8, lv)
        elif len(roots) == 2:
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 6, lv + 4)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 6, lv)
        else:
            b(bar, 0, r0, 6, lv + 4)
            b(bar, 6, r0, 2, lv - 6)
            b(bar, 8, r0, 6, lv - 2)
            if i in (3, 5):
                b(bar, 14, approach(bar, r0), 2, lv - 8)

    elif st == 'turn':
        b(bar, 0, r0, 14 if i == 0 else 12, lv - 6)
        if i == 1:
            b(bar, 14, approach(bar, r0), 2, lv - 10)

    elif st == 'pre':
        for s, l, c, r in roots:
            for off in range(0, l, 2):
                pos = s + off
                if last and pos == 14:
                    continue                          # breath with the piano
                p = r + 12 if off == 6 and r + 12 <= 52 else r
                b(bar, pos, p, 2, lv + (6 if off == 0 else -4), gap=0.8)

    elif st in ('chorus', 'final') or (st == 'lift' and i >= 4):
        if last:                                      # sustain under the piano's answer
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 5, lv + 6)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 6 if sec['name'] == 'Chorus 2' else 8, lv)
            if sec['name'] == 'Chorus 2':
                b(bar, 14, approach(bar, r2), 2, lv - 4)
        elif len(roots) == 2:
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 5, lv + 6)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 5, lv + 2)
            b(bar, 14, approach(bar, r2), 2, lv - 6)
        else:
            c = roots[0][2]
            b(bar, 0, r0, 5, lv + 6)
            b(bar, 6, r0, 2, lv - 4)
            b(bar, 8, r0, 3, lv + 2)
            b(bar, 11, second(c, r0), 2, lv - 6)
            if sec['name'] != 'Chorus 1' and r0 + 12 <= 52:
                b(bar, 12.5, r0 + 12, 1, lv - 14)     # ghosted octave pop
            b(bar, 14, approach(bar, r0), 2, lv - 6)

    elif st == 'bridge':
        c = roots[0][2]
        if i < 4:
            b(bar, 0, r0, 16, lv - 2, gap=0.96)
        elif i == 4:
            for k, pos in enumerate((0, 4, 8, 12)):
                b(bar, pos, r0 if k % 2 == 0 else second(c, r0), 4, lv)
        elif i == 5:
            for pos in (0, 4, 6, 8, 12):
                b(bar, pos, r0, 2 if pos == 4 else 4, lv)
        else:
            for pos in range(0, 16, 2):
                p = r0
                if i == 7 and pos == 14:
                    p = approach(bar, r0)
                b(bar, pos, p, 2, lv + (4 if pos % 4 == 0 else -4), gap=0.85)

    elif st == 'breakdown':
        if i == 0:
            b(bar, 0, r0, 16, lv, gap=0.96)
        else:
            (s1, l1, c1, r1), (s2, l2, c2, r2) = roots
            b(bar, 0, r1, 7, lv)
            for k, pos in enumerate((8, 10, 12, 14)):
                b(bar, pos, r2, 2, lv + 8 * k, gap=0.8)

    elif st == 'lift':                                # bars 65-68: whole notes, then the climb
        if i < 3:
            b(bar, 0, r0, 16, lv, gap=0.96)
        else:
            b(bar, 0, r0, 8, lv)
            b(bar, 8, r0, 4, lv + 8)
            b(bar, 12, r0, 2, lv + 14)
            b(bar, 14, approach(bar, r0), 2, lv + 20)

    elif st == 'outro':
        if bar == TOTAL_BARS:
            hit('bass', bar, 0, r0, lv, dur16=16, jitter=0)
        elif i == 6:
            b(bar, 0, r0, 16, lv, gap=0.98)
        else:
            b(bar, 0, r0, 10, lv)
            if i < 4:
                b(bar, 12, second(roots[0][2], r0), 4, lv - 10)


BASS_LEVEL = {'Intro': (60, 62), 'Verse 1': (64, 68), 'Verse 2': (68, 72), 'Pre-Chorus 1': (70, 80),
              'Chorus 1': (78, 82), 'Turnaround': (70, 66), 'Verse 3': (70, 74), 'Pre-Chorus 2': (76, 88),
              'Chorus 2': (90, 92), 'Bridge': (62, 96), 'Breakdown': (62, 66), 'Final Chorus': (96, 100),
              'Final Chorus (pull-back + lift)': (66, 102), 'Outro': (64, 46)}

# ---------- 6. organ (GM 17 Drawbar Organ, channel 3) ----------
organ_prev = None


def organ_voicing(chord):
    global organ_prev
    pcs = CH[chord][1][:3]
    organ_prev = voice(pcs, organ_prev, 52, 67, 60)
    return organ_prev


def pad(bar, chord_list, vel, dur_scale=1.0):
    for s, l, c in chord_list:
        for p in organ_voicing(c):
            hit('organ', bar, s, p, vel, dur16=l * dur_scale - 0.15, jitter=2)


def organ_for(sec, i, bar):
    st, name, n = sec['style'], sec['name'], len(sec['chords'])
    cs = chords_of(bar)
    last = i == n - 1
    if name == 'Verse 3' and i >= 4:
        if i == 4:
            ccs['organ'].append((tick(bar, 0) - 10, 11, 60))
        pad(bar, cs, 48)
    elif name == 'Pre-Chorus 2':
        if i == 0:
            ramp('organ', bar, 0, bar + 3, 12, 11, 60, 112)
        pad(bar, cs, 56)
    elif name == 'Chorus 2':
        if i == 0:
            ccs['organ'].append((tick(bar, 0) + 30, 11, 92))
        pad(bar, cs, 64)
    elif st == 'bridge':
        if i < 4:                                     # slow two-bar swells under the half-time feel
            if i % 2 == 0:
                ramp('organ', bar, 0, bar + 1, 8, 11, 40, 100)
                ramp('organ', bar + 1, 8, bar + 1, 15, 11, 100, 60)
            pad(bar, cs, 58)
        else:
            if i == 4:
                ramp('organ', bar, 0, bar + 3, 15, 11, 70, 120)
            pad(bar, cs, 62)
    elif st == 'breakdown' and i == 1:
        ramp('organ', bar, 8, bar, 15.5, 11, 30, 120)
        pad(bar, cs[1:], 66)
    elif st == 'final':
        if i == 0:
            ccs['organ'].append((tick(bar, 0) + 30, 11, 100))
        pad(bar, cs, 66)
    elif st == 'lift':
        if i == 0:
            ccs['organ'].append((tick(bar, 0) + 30, 11, 74))
        if i == 3:
            ramp('organ', bar, 0, bar, 15, 11, 74, 110)
        pad(bar, cs, 60 if i < 4 else 68)
        if i >= 4 and not last:                       # small off-beat lift, organ-only
            for p in organ_voicing(chord_at(bar, 14)):
                hit('organ', bar, 14, p, 56, dur16=1.2, jitter=2)
    elif st == 'outro' and i >= 4:
        if i == 4:
            ccs['organ'].append((tick(bar, 0) - 10, 11, 70))
        if i == 6:
            ramp('organ', bar, 0, bar + 1, 15, 11, 70, 20)
        if bar == TOTAL_BARS:
            for p in organ_voicing(cs[0][2]):
                hit('organ', bar, 0, p, 50, dur16=16, jitter=0)
        else:
            pad(bar, cs, 50)


# ---------- 7. render every bar ----------
for sec in SECTIONS:
    lv0, lv1 = BASS_LEVEL[sec['name']]
    n = len(sec['chords'])
    for i in range(n):
        bar = sec['start'] + i
        drums_for(sec, i, bar)
        aux_for(sec, i, bar)
        bass_for(sec, i, bar, lv0 + (lv1 - lv0) * i / max(1, n - 1))
        organ_for(sec, i, bar)


def tidy(notes):
    """Remove same-key overlaps (shorten the earlier note) and exact duplicates."""
    notes = sorted(notes, key=lambda x: (x[1], x[0]))
    out = []
    for k, (t0, p, d, v) in enumerate(notes):
        if k + 1 < len(notes) and notes[k + 1][1] == p:
            nt = notes[k + 1][0]
            if nt - t0 < 30:
                continue
            d = min(d, nt - t0 - 5)
        out.append((t0, p, max(25, min(d, END - t0)), v))
    return out


for k in parts:
    parts[k] = tidy(parts[k])

# ---------- 8. write MIDI ----------
TRACKS = {  # key: (track name, channel 0-based, GM program 0-based, volume, pan)
    'brushes': ('Drums (Brushes)', 9, 40, 100, 64),
    'drums': ('Drums (Sticks)', 9, 0, 100, 64),
    'bass': ('Bass', 1, 33, 100, 64),
    'organ': ('Organ', 2, 16, 84, 76),
    'aux': ('Shaker & Tambourine', 9, 0, 80, 50),
}
INSTR = {'brushes': 'Brush Kit (GM channel 10)', 'drums': 'Standard Drum Kit (GM channel 10)', 'bass': 'Electric Bass (finger)',
         'organ': 'Drawbar Organ', 'aux': 'Percussion (GM channel 10)'}


def build_track(key):
    name, ch, prog, vol, pan = TRACKS[key]
    tr = MidiTrack()
    head = [MetaMessage('track_name', name=name),
            MetaMessage('instrument_name', name=INSTR[key]),
            Message('program_change', channel=ch, program=prog),
            Message('control_change', channel=ch, control=7, value=vol),
            Message('control_change', channel=ch, control=10, value=pan),
            Message('control_change', channel=ch, control=11, value=100 if key != 'organ' else 70)]
    ev = []
    for t0, p, d, v in parts[key]:
        ev.append((t0, 2, Message('note_on', channel=ch, note=p, velocity=v)))
        ev.append((t0 + d, 0, Message('note_off', channel=ch, note=p, velocity=64)))
    last = None
    for t0, c, val in sorted(ccs[key]):
        if (c, val) != last:
            ev.append((max(0, min(t0, END)), 1, Message('control_change', channel=ch, control=c, value=val)))
            last = (c, val)
    ev.sort(key=lambda e: (e[0], e[1]))
    for m in head:
        tr.append(m.copy(time=0))
    now = 0
    for t0, _, m in ev:
        tr.append(m.copy(time=t0 - now))
        now = t0
    tr.append(MetaMessage('end_of_track', time=END - now))
    return tr


def copy_track(src):
    tr = MidiTrack()
    for m in src:
        tr.append(m.copy())
    return tr


band = {k: build_track(k) for k in TRACKS}


def save(path, tracks):
    mf = MidiFile(type=1, ticks_per_beat=PPQ)
    mf.tracks.append(copy_track(orig.tracks[0]))      # identical tempo map, meter, key, markers
    for tr in tracks:
        mf.tracks.append(tr)
    mf.save(os.path.join(HERE, path))
    return mf


full = save('full_song_multitrack.mid', [copy_track(orig.tracks[1])] +
            [band[k] for k in ('brushes', 'drums', 'bass', 'organ', 'aux')])
save('drums_only.mid', [band['brushes'], band['drums']])
save('bass_only.mid', [band['bass']])
save('organ_only.mid', [band['organ']])
save('aux_percussion_only.mid', [band['aux']])

# ---------- 9. drum map documentation (generated so it always matches the file) ----------
cnt = {k: Counter(p for _, p, _, _ in parts[k]) for k in ('brushes', 'drums', 'aux')}
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
lines = ['# Drum map: Pancakes and Lemonade', '',
         'All three percussion tracks use **MIDI channel 10** and the **General MIDI percussion map**.',
         'Logic calls middle C (note 60) **C3**, so note 36 shows up as **C1** in the Piano Roll.', '',
         '- **Drums (Brushes)**: bars ' + ', '.join(f'{a}-{b}' for a, b in (
             (min(g), max(g)) for g in [[x for x in sorted(BRUSH_BARS) if x <= 42],
                                        [x for x in sorted(BRUSH_BARS) if 43 <= x <= 80],
                                        [x for x in sorted(BRUSH_BARS) if x > 80]] if g)) +
         '. Load a brush kit on this track.',
         '- **Drums (Sticks)**: everything else (pre-chorus 2 to the end of the final chorus, except the pulled-back bars). Load a normal acoustic kit.',
         '- **Shaker & Tambourine**: optional, verse 3 onward.', '',
         'The brush part uses the same note numbers as a stick kit (snare = 38, kick = 36, hi-hat foot = 44).',
         'With a brush kit loaded, those notes play brush sounds. The soft, constant snare notes are the "swish"',
         'between backbeats. With a stick kit they just sound like very light playing.', '',
         '| MIDI note | Logic name | Instrument | Brushes | Sticks | Shaker & Tamb. |',
         '|---:|:---:|---|---:|---:|---:|']
for note in sorted(DRUM_NAMES):
    if any(cnt[k][note] for k in cnt):
        lines.append(f'| {note} | {NAMES[note % 12]}{note // 12 - 2} | {DRUM_NAMES[note]} | '
                     f'{cnt["brushes"][note]} | {cnt["drums"][note]} | {cnt["aux"][note]} |')
lines += ['', '## Velocity conventions', '',
          '| Range | Meaning | Where it appears |', '|---|---|---|',
          '| 14–40 | Ghost notes / brush strokes | the soft snare swish under the brushes, 16th hats, shaker off-beats |',
          '| 40–65 | Soft | brush backbeats in the verses, intro, outro, the pulled-back chorus |',
          '| 65–95 | Normal | chorus 1 brushes, stick grooves in pre-chorus 2 and chorus 2 |',
          '| 95–120 | Accents | crashes, final-chorus backbeats, fill peaks |', '',
          'Timing drifts by at most ±5 ticks (about 1/100 of a beat). Downbeats are never early.', '',
          '## Where things happen', '',
          '- **Intro (1-4):** piano alone for two bars, then a soft brush swish and a pickup.',
          '- **Verse 1 (5-12):** lightest groove: brush taps on 2 and 4, kick on 1 and the "and" of 2, hi-hat foot.',
          '- **Verse 2 (13-20):** same feel with 16th-note brush strokes and a few kick pickups.',
          '- **Pre-Chorus 1 (21-24):** builds, brushed hi-hat joins, stops on beat 4 of bar 24 with the piano.',
          '- **Chorus 1 (25-32):** still brushes: brushed ride, fuller kick. A lift, not a wall.',
          '- **Turnaround (33-34):** very light.',
          '- **Verse 3 (35-42):** busiest brush groove, shaker joins; swells into the sticks.',
          '- **Pre-Chorus 2 (43-46):** sticks come in, ending with a tom fill.',
          '- **Chorus 2 (47-54):** first full-band chorus: ride cymbal, crash, shaker.',
          '- **Bridge (55-62):** half-time, then climbs to a snare roll.',
          '- **Breakdown (63-64):** one crash, near silence, snare crescendo.',
          '- **Final Chorus (65-72):** the biggest groove, tambourine on 2 and 4.',
          '- **Pull-back (73-76):** back to brushes, half-time; sticks return with a tom fill in bar 76.',
          '- **Lift (77-80):** full band.',
          '- **Outro (81-88):** brushes fade out; last kick and brushed ride on the final downbeat.']
open(os.path.join(HERE, 'drum_map.md'), 'w').write('\n'.join(lines) + '\n')

print(f'wrote {len(TRACKS) + 1} instrument tracks, {full.length:.2f} s, {TOTAL_BARS} bars')
for k in parts:
    print(f'  {TRACKS[k][0]:<20} ch {TRACKS[k][1] + 1:>2}  {len(parts[k])} notes')
