#!/usr/bin/env python3
"""Build the full band arrangement around the original piano MIDI.

Reads (never writes):
  ../original_piano_song.mid    the piano part, tempo map, meter, key and markers
  ../generate_piano_song.py     the chord chart and section list (read as data)

Writes, next to this script:
  full_song_multitrack.mid      Type 1: Tempo & Meter, Grand Piano, Drums,
                                Bass, Organ, Shaker & Tambourine
  piano_only.mid, drums_only.mid, bass_only.mid, organ_only.mid,
  aux_percussion_only.mid       the same tracks one at a time, same tempo map
  drum_map.md                   every drum note used, with velocity conventions

Requires: pip install mido.  Run: python3 generate_arrangement.py
The random seed is fixed, so every run produces identical files.
"""
import ast
import itertools
import os
import random
import shutil
from collections import Counter

from mido import Message, MetaMessage, MidiFile, MidiTrack

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(HERE)
SRC_MID = os.path.join(SRC_DIR, 'original_piano_song.mid')
SRC_PY = os.path.join(SRC_DIR, 'generate_piano_song.py')
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
END = sum(m.time for m in orig.tracks[1])           # end of the piano track = end of bar 80

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

parts = {k: [] for k in ('drums', 'bass', 'organ', 'aux')}   # (tick, note, dur, vel)
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


def drums_for(sec, i, bar):
    st, n = sec['style'], len(sec['chords'])
    two = len(chords_of(bar)) == 2
    last = i == n - 1
    name = sec['name']

    if st == 'intro':
        if i == 2:
            kicks(bar, [0], 52)
            hats(bar, 44)
        elif i == 3:
            hats(bar, 46, until=12)
            hit('drums', bar, 12, SNARE, 38)
            hit('drums', bar, 14, SNARE, 48)
            hit('drums', bar, 15, SNARE, 56)

    elif st == 'verse':                               # restrained: cross-stick, kick locks to piano LH
        lv = 60 + i
        kicks(bar, [0, 6, 8] if two else ([0, 6, 10] if i % 2 else [0, 6]), lv + 16)
        backbeat(bar, lv + 10, SIDESTICK)
        if last:
            hats(bar, lv, skip=(14,))
            hit('drums', bar, 14, HH_OPEN, lv - 4, dur16=2)
        else:
            hats(bar, lv)

    elif st == 'turn':
        kicks(bar, [0] if i == 0 else [0, 10], 66)
        backbeat(bar, 56, SIDESTICK, (12,) if i == 0 else (4, 12))
        hats(bar, 48)

    elif st == 'verse2':                              # same family, more motion: 16th hats, ghosts, pickups
        lv = 62 + i
        if two:
            kicks(bar, [0, 6, 8, 14], lv + 14)
        else:
            kicks(bar, [0, 6, 10, 14] if i % 2 else [0, 6, 10], lv + 14)
        backbeat(bar, lv + 10, SIDESTICK)
        hit('drums', bar, 7 if i % 2 else 15, SNARE, 28)
        if last:
            hats(bar, lv - 4, step=1, until=13)
            hit('drums', bar, 14, HH_OPEN, lv - 2, dur16=2)
            hit('drums', bar, 15, SNARE, 46)
        else:
            hats(bar, lv - 4, step=1)

    elif st == 'pre':                                 # real snare arrives, hats tighten, crescendo
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

    elif st == 'lift':                                # bars 65-68: pulled back under the vocal
        kicks(bar, [0], 56)
        hit('drums', bar, 8, SIDESTICK, 52)
        for p in (0, 4, 8, 12):
            hit('drums', bar, p, HH_PEDAL, 38)
        if i == 3:
            for pos, note, v in [(8, SNARE, 62), (10, SNARE, 72), (12, TOM_HIGH, 82),
                                 (13, TOM_HIGH, 86), (14, TOM_LOW, 92), (15, TOM_FLOOR, 102)]:
                hit('drums', bar, pos, note, v, jitter=3)
            kicks(bar, [12], 80)

    elif st == 'outro':
        lv = 58 - 3 * i
        if i < 4:
            kicks(bar, [0], lv + 6)
            backbeat(bar, lv, SIDESTICK)
            hats(bar, lv - 10)
        elif i < 6:
            kicks(bar, [0], lv)
            for p in (0, 4, 8, 12):
                hit('drums', bar, p, RIDE, lv - 8)
        elif i == 6:
            kicks(bar, [0], lv)
            hit('drums', bar, 0, RIDE, lv - 6)
            hit('drums', bar, 8, RIDE, lv - 12)
        else:                                         # last downbeat: everyone lands together
            hit('drums', bar, 0, KICK, 64)
            hit('drums', bar, 0, CRASH, 62, dur16=16)


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


BASS_LEVEL = {'Intro': (60, 62), 'Verse 1': (66, 70), 'Pre-Chorus 1': (70, 82), 'Chorus 1': (86, 88),
              'Turnaround': (70, 66), 'Verse 2': (70, 74), 'Pre-Chorus 2': (74, 88), 'Chorus 2': (90, 92),
              'Bridge': (62, 96), 'Breakdown': (62, 66), 'Final Chorus': (96, 100),
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
    if name == 'Chorus 1':
        if i == 0:
            ccs['organ'].append((tick(bar, 0) - 10, 11, 84))
        pad(bar, cs, 60)
    elif name == 'Verse 2' and i >= 4:
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
    'drums': ('Drums', 9, 0, 100, 64),
    'bass': ('Bass', 1, 33, 100, 64),
    'organ': ('Organ', 2, 16, 84, 76),
    'aux': ('Shaker & Tambourine', 9, 0, 80, 50),
}
INSTR = {'drums': 'Standard Drum Kit (GM channel 10)', 'bass': 'Electric Bass (finger)',
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
            [band[k] for k in ('drums', 'bass', 'organ', 'aux')])
shutil.copyfile(SRC_MID, os.path.join(HERE, 'piano_only.mid'))   # byte-for-byte original
save('drums_only.mid', [band['drums']])
save('bass_only.mid', [band['bass']])
save('organ_only.mid', [band['organ']])
save('aux_percussion_only.mid', [band['aux']])

# ---------- 9. drum map documentation (generated so it always matches the file) ----------
used = Counter(p for _, p, _, _ in parts['drums'])
used_aux = Counter(p for _, p, _, _ in parts['aux'])
lines = ['# Drum map — full_song_multitrack.mid / drums_only.mid', '',
         'Both drum tracks ("Drums" and "Shaker & Tambourine") use **MIDI channel 10** and the',
         '**General MIDI percussion map**. Logic\'s acoustic Drum Kit Designer kits follow the same',
         'note numbers for the kit pieces below. Logic labels middle C (note 60) as **C3**, so note',
         '36 appears as **C1** in Logic\'s Piano Roll / Drum Editor.', '',
         '| MIDI note | Logic name | Instrument | Hits (Drums) | Hits (Shaker & Tamb.) |',
         '|---:|:---:|---|---:|---:|']
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for note in sorted(DRUM_NAMES):
    if used[note] or used_aux[note]:
        lines.append(f'| {note} | {NAMES[note % 12]}{note // 12 - 2} | {DRUM_NAMES[note]} | '
                     f'{used[note]} | {used_aux[note]} |')
lines += ['', '## Velocity conventions', '',
          '| Range | Meaning | Where it appears |', '|---|---|---|',
          '| 20–40 | Ghost notes | quiet snare taps between backbeats, soft 16th hats, shaker off-beats |',
          '| 40–65 | Soft / restrained | intro hats, verse cross-stick, half-time bridge ride, outro |',
          '| 65–95 | Normal playing | verse kick, pre-chorus and chorus snare, hats and ride |',
          '| 95–120 | Accents | chorus downbeat crashes, final-chorus backbeats, fill peaks |', '',
          'Hi-hat and ride patterns accent the quarter notes; the off-beat 8ths are about 12',
          'lower and 16ths about 22 lower. Timing drifts by at most ±4 ticks (under 1/100 of',
          'a beat at 480 ticks per quarter). Downbeats are never early.', '',
          '## Where things happen', '',
          '- **Intro (1-4):** no drums for two bars; soft hats from bar 3; a three-note snare pickup into the verse.',
          '- **Verse 1 (5-12):** kick on beat 1 and the "and" of 2 (it locks with the piano\'s left hand), cross-stick on 2 and 4, 8th-note hats. An open hat on the last "and" leads into the pre-chorus.',
          '- **Pre-Chorus 1 (13-16):** full snare on 2 and 4, 16th hats in bar 15. The band stops on beat 4 of bar 16 with the piano\'s breath.',
          '- **Chorus 1 (17-24):** crash and fuller kick (adds the "a" of 3), hats with ghost snares. Thins out in bar 24 under the piano\'s answer phrase.',
          '- **Turnaround (25-26):** just kick, cross-stick and hats.',
          '- **Verse 2 (27-34):** 16th-note hats, ghost snare notes, kick pickups; the shaker joins at bar 29.',
          '- **Pre-Chorus 2 (35-38):** like pre-chorus 1, but ends with a tom fill.',
          '- **Chorus 2 (39-46):** ride cymbal instead of hats, plus the shaker. The fill in bar 46 drops away into the bridge.',
          '- **Bridge (47-54):** half-time (snare on beat 3 only, ride quarters, hi-hat foot). From bar 51 it climbs back, ending in a snare roll.',
          '- **Breakdown (55-56):** one crash, then nearly silent; a snare crescendo in bar 56 launches the final chorus.',
          '- **Final Chorus (57-64):** strongest groove: ride with bell, crashes, tambourine on 2 and 4.',
          '- **Pull-back (65-68):** kick, cross-stick on beat 3 and hi-hat foot only, then a tom fill.',
          '- **Lift (69-72):** full band again.',
          '- **Outro (73-80):** cross-stick, then ride only, then one soft kick + crash on the last downbeat.']
open(os.path.join(HERE, 'drum_map.md'), 'w').write('\n'.join(lines) + '\n')

print(f'wrote {len(TRACKS) + 1} instrument tracks, {full.length:.2f} s, {TOTAL_BARS} bars')
for k in parts:
    print(f'  {TRACKS[k][0]:<20} ch {TRACKS[k][1] + 1:>2}  {len(parts[k])} notes')
