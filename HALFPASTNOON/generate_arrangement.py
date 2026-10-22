#!/usr/bin/env python3
"""Build the band arrangement for "Half Past Noon" around piano_only.mid.

Reads (never writes):
  piano_only.mid   the piano part, tempo map, meter, key and markers
  song.py          the chord chart, form and grooves

Writes, next to this script:
  full_song_multitrack.mid   Type 1: Tempo & Meter, Grand Piano, Drums, Bass, Rhodes,
                             Shaker & Tambourine
  drums_only.mid, bass_only.mid, rhodes_only.mid, aux_percussion_only.mid
  drum_map.md                every drum note used, with velocity conventions

Every instrument has its own random stream (fixed seeds), so editing one part never shifts another
and every run produces identical files.
Requires: pip install mido.  Run: python3 generate_piano.py && python3 generate_arrangement.py
"""
import os
import random
from collections import Counter

from mido import Message, MetaMessage, MidiFile, MidiTrack

from song import BAR, CH, END, PPQ, S16, TOTAL_BARS, VERSE_KICK, sections, timeline
from generate_piano import voice

HERE = os.path.dirname(os.path.abspath(__file__))
orig = MidiFile(os.path.join(HERE, 'piano_only.mid'))
assert orig.type == 1 and len(orig.tracks) == 2 and orig.ticks_per_beat == PPQ
assert sum(m.time for m in orig.tracks[1]) == END, 'piano track does not end on the last barline'
markers = [m.text for m in orig.tracks[0] if m.type == 'marker']
SECTIONS = [{'name': nm, 'style': st, 'start': a, 'chords': ch} for nm, st, a, b, ch in sections()]
assert len(markers) == len(SECTIONS), 'form and markers disagree'
TIMELINE = timeline()

RNG = {k: random.Random(seed) for k, seed in
       (('drums', 7701), ('bass', 3402), ('rhodes', 505), ('aux', 8203))}

# ---------- helpers ----------
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

parts = {k: [] for k in RNG}          # (tick, note, dur, vel)
ccs = {k: [] for k in RNG}            # (tick, controller, value)


def tick(bar, pos):
    return int((bar - 1) * BAR + pos * S16)


def clampv(v):
    return max(1, min(127, int(round(v))))


def hit(part, bar, pos, note, vel, dur16=1.0, jitter=4):
    """One note. pos is in sixteenths. Small human timing drift from the part's own stream."""
    r = RNG[part]
    t0 = tick(bar, pos)
    if jitter:
        t0 += r.randint(0 if pos == 0 else -jitter, jitter)   # downbeats never early
    t0 = max(0, min(t0, END - 30))
    dur = max(30, min(int(dur16 * S16), END - t0))
    parts[part].append((t0, note, dur, clampv(vel + r.randint(-4, 4))))


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


# ---------- drums (GM channel 10) ----------
def d(bar, pos, note, v, dur16=1.0, jitter=4):
    hit('drums', bar, pos, note, v, dur16, jitter)


def hats(bar, base, step=2, note=HH_CLOSED, skip=(), until=16, extra=()):
    for pos in sorted(set(range(0, until, step)) | set(extra)):
        if pos in skip or pos >= until:
            continue
        v = base if pos % 4 == 0 else base - (10 if pos % 2 == 0 else 20)
        d(bar, pos, note, v)


def ride(bar, base, bell=False, skip=()):
    for pos in range(0, 16, 2):
        if pos in skip:
            continue
        if bell and pos % 4 == 0:
            d(bar, pos, RIDE_BELL, base - 4)
        else:
            d(bar, pos, RIDE, base if pos % 4 == 0 else base - 10)


def kicks(bar, positions, v):
    for p in positions:
        d(bar, p, KICK, v if p in (0, 8) else v - 8)


def fill(bar, hits):
    for pos, note, v in hits:
        d(bar, pos, note, v, jitter=3)


def drums_for(sec, i, bar):
    st, name, n = sec['style'], sec['name'], len(sec['chords'])
    two = len(chords_of(bar)) == 2
    last = i == n - 1

    if st == 'intro':                                   # bars 1-2 piano alone
        if i == 2:
            kicks(bar, [0], 54)
            hats(bar, 46)
        elif i == 3:
            kicks(bar, [0, 10], 58)
            hats(bar, 48, until=12)
            fill(bar, [(12, SIDESTICK, 50), (14, SNARE, 40), (15, SNARE, 52)])

    elif st in ('verse', 'verse2') or (st == 'outro' and i < 2):
        busy = st == 'verse2'
        lv = (58 if not busy else 62) + i // 2 - (4 if st == 'outro' else 0)
        kicks(bar, [0, 8] if two else VERSE_KICK, lv + 14)
        for p in (4, 12):
            d(bar, p, SIDESTICK, lv + 8)
        if busy:                                       # verse 2/3: ghost notes and a 16th skip in the hats
            d(bar, 6, SNARE, 24)
            if i % 2:
                d(bar, 15, SNARE, 28)
            hats(bar, lv - 2, extra=(11,) if i % 2 == 0 else (3, 11))
        elif last:
            hats(bar, lv - 2, skip=(14,))
            d(bar, 14, HH_OPEN, lv - 6, dur16=2)
        else:
            hats(bar, lv - 2)
        if last and st != 'outro':
            d(bar, 15, SNARE, 44)

    elif st == 'turn':
        kicks(bar, [0] if i == 0 else [0, 8], 66)
        d(bar, 12, SIDESTICK, 56)
        hats(bar, 50)
        if i == 1:
            d(bar, 14, HH_OPEN, 50, dur16=2)

    elif st == 'pre':                                   # the real snare arrives
        second = name.endswith('2')
        lv = 66 + 5 * i + (6 if second else 0)
        if not last:
            kicks(bar, [0, 6, 8, 14], lv + 10)
            for p in (4, 12):
                d(bar, p, SNARE, lv + 6)
            hats(bar, lv - 6, step=1 if i == 2 and second else 2)
        elif not second:                               # pre 1: short snare pickup
            kicks(bar, [0, 6, 8], lv + 10)
            d(bar, 4, SNARE, lv + 6)
            hats(bar, lv - 6, until=12)
            fill(bar, [(12, SNARE, 70), (13, SNARE, 56), (14, SNARE, 78), (15, SNARE, 88)])
        else:                                          # pre 2: tom fill, high to low
            kicks(bar, [0, 6, 8, 12], lv + 8)
            d(bar, 4, SNARE, lv + 6)
            hats(bar, lv - 6, until=8)
            fill(bar, [(8, TOM_HIGH, 80), (9, TOM_HIGH, 70), (10, TOM_LOW, 84), (11, TOM_LOW, 74),
                       (12, TOM_FLOOR, 90), (13, TOM_FLOOR, 82), (14, SNARE, 96), (15, SNARE, 104)])

    elif st == 'chorus_light':                          # chorus 1: half the kit, softer
        lv = 72 + (2 if i >= 4 else 0)
        if i == 0:
            d(bar, 0, CRASH, 84, dur16=8)
        kicks(bar, [0, 6, 8] if two else [0, 6, 10], lv + 8)
        for p in (4, 12):
            d(bar, p, SNARE, lv)
        hats(bar, lv - 12, skip=(0,) if i == 0 else ())
        if last:
            d(bar, 15, SNARE, 40)

    elif st in ('chorus', 'final'):
        big = st == 'final'
        lv = (92 if big else 82) + (4 if i % 4 == 0 else 0)
        crash = i in (0, 4) and not (name == 'Last Lift' and i == 4)
        if crash:
            d(bar, 0, CRASH, lv + 16, dur16=8)
        if last and name == 'Chorus 2':                # fill that drops into the half-time bridge
            kicks(bar, [0, 6, 8], lv + 6)
            d(bar, 4, SNARE, lv + 6)
            hats(bar, lv - 10, until=8)
            fill(bar, [(8, SNARE, 78), (10, SNARE, 84), (11, TOM_HIGH, 80), (12, TOM_LOW, 84),
                       (13, TOM_LOW, 78), (14, TOM_FLOOR, 90), (15, TOM_FLOOR, 82)])
            return
        if last and name == 'Final Chorus':            # stop on beat 3: the room empties for the pull-back
            kicks(bar, [0, 6, 8], lv + 6)
            d(bar, 4, SNARE, lv + 6)
            d(bar, 8, CRASH, lv, dur16=8)
            ride(bar, lv - 14, skip=range(8, 16))
            return
        if last:                                       # last lift -> outro
            kicks(bar, [0, 6, 8], lv + 6)
            d(bar, 4, SNARE, lv + 6)
            ride(bar, lv - 14, bell=True, skip=range(8, 16))
            fill(bar, [(8, SNARE, 84), (9, SNARE, 66), (10, TOM_HIGH, 86), (12, TOM_LOW, 90),
                       (14, TOM_FLOOR, 96), (15, SNARE, 70)])
            return
        kp = [0, 2, 6, 10] if big else [0, 6, 10]
        if two:
            kp = [0, 2, 6, 8] if big else [0, 6, 8]
        kicks(bar, kp, lv + 8)
        for p in (4, 12):
            d(bar, p, SNARE, lv + 8)
        d(bar, 7, SNARE, 30)                           # ghosts
        d(bar, 15, SNARE, 26 if i % 2 == 0 else 34)
        skip = (0,) if crash else ()
        if big:
            ride(bar, lv - 10, bell=True, skip=skip)
        else:
            hats(bar, lv - 8, skip=skip + ((14,) if i % 2 else ()))
            if i % 2:
                d(bar, 14, HH_OPEN, lv - 12, dur16=2)

    elif st == 'pullback':                              # kick, hat foot, one cross-stick: like verse 1
        kicks(bar, [0, 10], 66)
        d(bar, 12, SIDESTICK, 58)
        for p in (4, 12):
            d(bar, p, HH_PEDAL, 46)
        hats(bar, 40, step=4, skip=(0,))
        if i == 3:                                     # build into the last lift
            kicks(bar, [8, 12], 74)
            fill(bar, [(8, SNARE, 46), (10, SNARE, 56), (12, SNARE, 66), (13, SNARE, 72),
                       (14, SNARE, 82), (15, SNARE, 92)])

    elif st == 'bridge':
        if i < 4:                                      # half-time: snare on beat 3 only, soft 8th hats
            if i == 0:
                d(bar, 0, CRASH, 74, dur16=12)
            kicks(bar, [0, 8] if two else [0, 10], 70)
            d(bar, 8, SIDESTICK if i < 2 else SNARE, 64 if i < 2 else 68)
            hats(bar, 50, skip=(0,) if i == 0 else ())
            if i == 3:
                d(bar, 14, TOM_FLOOR, 62)
                d(bar, 15, TOM_FLOOR, 70)
        else:                                          # the climb back into time
            lv = 72 + (i - 4) * 7
            if i == 4:
                d(bar, 0, CRASH, 86, dur16=8)
            kp = {4: [0, 8], 5: [0, 6, 8], 6: [0, 6, 8, 14], 7: [0, 4, 8, 12]}[i]
            kicks(bar, kp, lv + 8)
            if i < 7:
                for p in (4, 12):
                    d(bar, p, SNARE, lv + 4)
                hats(bar, lv - 6, step=1 if i == 6 else 2, skip=(0,) if i == 4 else ())
            else:                                      # snare 8ths, growing, into the breakdown
                for pos in range(0, 16, 2):
                    d(bar, pos, SNARE, 60 + pos * 3, jitter=2)
                hats(bar, lv - 8, until=8)

    elif st == 'breakdown':
        if i == 0:                                     # drums drop out: hat foot only under the hook
            for p in (4, 12):
                d(bar, p, HH_PEDAL, 40)
        else:                                          # four on the floor, then a snare pickup
            for k, p in enumerate((0, 4, 8, 12)):
                d(bar, p, KICK, 66 + 8 * k)
            d(bar, 14, KICK, 86)
            fill(bar, [(8, SNARE, 64), (12, SNARE, 80), (14, SNARE, 90), (15, SNARE, 100)])
            hats(bar, 54, until=8)

    elif st == 'outro':                                 # bars 81-82 handled with the verses above
        if i < 4:
            lv = 60 - 3 * (i - 2)
            kicks(bar, [0, 8] if two else [0, 10], lv + 6)
            for p in (0, 4, 8, 12):
                d(bar, p, RIDE, lv - 6)
            d(bar, 12, SIDESTICK, lv - 6)
        elif i == 4:
            kicks(bar, [0], 54)
            d(bar, 0, RIDE, 50)
            d(bar, 8, RIDE, 42)
            fill(bar, [(12, SNARE, 36), (14, SNARE, 44), (15, SNARE, 52)])
        else:                                          # last downbeat: everyone lands together
            d(bar, 0, KICK, 70, jitter=0)
            d(bar, 0, CRASH, 66, dur16=16, jitter=0)


# ---------- shaker & tambourine (channel 10, own track) ----------
def a(bar, pos, note, v):
    hit('aux', bar, pos, note, v, jitter=3)


def shaker(bar, base, until=16):
    for pos in range(until):
        a(bar, pos, SHAKER, base if pos % 4 == 0 else (base - 8 if pos % 2 == 0 else base - 16))


def aux_for(sec, i, bar):
    st, name, last = sec['style'], sec['name'], i == len(sec['chords']) - 1
    if name == 'Verse 3':
        shaker(bar, 40 + i)
    elif name == 'Pre-Chorus 2':
        shaker(bar, 48 + 3 * i, until=16 if not last else 8)
    elif name == 'Chorus 2' and not last:
        shaker(bar, 54)
    elif st == 'bridge' and i >= 4 and i < 7:
        shaker(bar, 46 + 3 * i)
    elif st == 'final' and not last:
        for p in (4, 12):
            a(bar, p, TAMBOURINE, 76)
        for pos in (2, 6, 10, 14):
            a(bar, pos, TAMBOURINE, 40)
    elif st == 'outro' and i < 4:
        shaker(bar, 40 - 3 * i, until=16)
    elif bar == TOTAL_BARS:                            # one soft tambourine with the final chord
        hit('aux', bar, 0, TAMBOURINE, 48, jitter=0)


# ---------- bass (GM 34 Electric Bass (finger), channel 2) ----------
A_SCALE = {9, 11, 1, 2, 4, 6, 8}
LO, HI = 28, 50                                       # E1 .. D3 for the main notes (octave pops may reach 55)
bass_prev = [45]


def bass_pitch(chord):
    pc = CH[chord][0]
    cands = [p for p in range(LO, HI + 1) if p % 12 == pc]
    bass_prev[0] = min(cands, key=lambda p: (abs(p - bass_prev[0]), p))
    return bass_prev[0]


def fifth(chord, root):
    iv = CH[chord][2]
    return root + iv if root + iv <= 52 else root + iv - 12


def approach(bar, root):
    """A scale step into the next bar's bass note (chromatic only if nothing else fits)."""
    if bar >= TOTAL_BARS:
        return None
    nxt_pc = CH[TIMELINE[bar + 1][0][2]][0]
    target = min((p for p in range(LO, HI + 1) if p % 12 == nxt_pc), key=lambda p: abs(p - root))
    for cand in (target - 2, target + 2, target - 1, target + 1):
        if cand % 12 in A_SCALE and cand != root and LO <= cand <= 52:
            return cand
    return target - 1


def b(bar, pos, pitch, dur16, vel, gap=0.9):
    hit('bass', bar, pos, pitch, vel, dur16=dur16 * gap, jitter=3)


def bass_for(sec, i, bar, lv):
    st, name, n = sec['style'], sec['name'], len(sec['chords'])
    cs = chords_of(bar)
    last = i == n - 1
    roots = [(s, l, c, bass_pitch(c)) for s, l, c in cs]
    r0, c0 = roots[0][3], roots[0][2]
    two = len(roots) == 2
    if st == 'outro' and i < 2:
        st = 'verse'

    if st == 'intro':
        if i == 2:
            b(bar, 0, r0, 16, lv - 6, gap=0.97)
        elif i == 3:
            b(bar, 0, r0, 10, lv - 4)
            b(bar, 10, r0, 4, lv - 8)
            b(bar, 14, approach(bar, r0), 2, lv - 10)

    elif st in ('verse', 'verse2'):                   # 1, the "a" of 2, the "and" of 3: with the kick
        if two:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 6, lv + 6)
            b(bar, 8, r2, 5, lv + 2)
            if st == 'verse2' or last:
                b(bar, 14, approach(bar, r2), 2, lv - 8)
        else:
            b(bar, 0, r0, 6, lv + 6)
            b(bar, 7, r0, 2, lv - 6)
            b(bar, 10, r0 if st == 'verse' else fifth(c0, r0), 3, lv - 2)
            if st == 'verse2' and i % 2:
                b(bar, 14, approach(bar, r0), 2, lv - 8)
            elif i in (3, 7):
                b(bar, 14, approach(bar, r0), 2, lv - 10)

    elif st == 'turn':
        if two:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 7, lv)
            b(bar, 8, r2, 5, lv)
            b(bar, 14, approach(bar, r2), 2, lv - 8)
        else:
            b(bar, 0, r0, 12, lv - 4)

    elif st == 'pre':                                 # with the kick: 1, "and" of 2, 3, "and" of 4
        for s, l, c, r in roots:
            b(bar, s, r, 3, lv + 6)
            b(bar, s + 6, r + 12 if r + 12 <= 52 else r, 2, lv - 4)
        if not two:
            b(bar, 8, r0, 3, lv + 2)
            if not last:
                b(bar, 14, approach(bar, r0) if i % 2 else r0, 2, lv - 6)

    elif st == 'chorus_light':                        # chorus 1: long notes, room to breathe
        if two:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 5, lv + 4)
            b(bar, 6, r1, 2, lv - 6)
            b(bar, 8, r2, 7 if last else 6, lv)
        else:
            b(bar, 0, r0, 5, lv + 4)
            b(bar, 6, r0, 2, lv - 6)
            b(bar, 10, r0, 4, lv - 2)
            if i in (3, 5):
                b(bar, 14, approach(bar, r0), 2, lv - 8)

    elif st in ('chorus', 'final'):
        big = st == 'final'
        if two:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 2, lv + 6)
            if big:
                b(bar, 2, r1, 3, lv - 4)
            b(bar, 6, r1, 2, lv - 2)
            b(bar, 8, r2, 3, lv + 4)
            b(bar, 12, fifth(c2, r2), 2, lv - 6)
            if not (last and name == 'Final Chorus'):
                b(bar, 14, approach(bar, r2), 2, lv - 6)
        else:
            b(bar, 0, r0, 2, lv + 6)
            if big:
                b(bar, 2, r0, 3, lv - 4)
            b(bar, 6, r0, 2, lv - 2)
            b(bar, 10, r0, 2, lv + 2)
            b(bar, 12, fifth(c0, r0), 2, lv - 6)
            b(bar, 14, approach(bar, r0) if i % 2 else r0, 2, lv - 6)

    elif st == 'pullback':
        b(bar, 0, r0, 10, lv, gap=0.96)
        b(bar, 10, r0, 6 if i < 3 else 2, lv - 6)
        if i == 3:
            for k, pos in enumerate((12, 14)):
                b(bar, pos, r0 if k == 0 else approach(bar, r0), 2, lv + 6 * k)

    elif st == 'bridge':
        if i < 4:
            if two:
                (_, _, c1, r1), (_, _, c2, r2) = roots
                b(bar, 0, r1, 8, lv, gap=0.96)
                b(bar, 8, r2, 8, lv, gap=0.96)
            else:
                b(bar, 0, r0, 10, lv, gap=0.96)
                b(bar, 10, fifth(c0, r0), 6, lv - 6, gap=0.96)
        else:
            if i == 4:
                for k, pos in enumerate((0, 4, 8, 12)):
                    b(bar, pos, r0 if k % 2 == 0 else fifth(c0, r0), 4, lv)
            elif i == 5:
                for pos in (0, 4, 6, 8, 12):
                    b(bar, pos, r0, 2, lv)
            else:
                for pos in range(0, 16, 2):
                    p = approach(bar, r0) if (i == 7 and pos == 14) else r0
                    b(bar, pos, p, 2, lv + (4 if pos % 4 == 0 else -4), gap=0.85)

    elif st == 'breakdown':
        if i == 0:
            b(bar, 0, r0, 16, lv - 6, gap=0.96)
        else:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 7, lv)
            for k, pos in enumerate((8, 10, 12, 14)):
                b(bar, pos, r2, 2, lv + 6 * k, gap=0.8)

    elif st == 'outro':
        if bar == TOTAL_BARS:
            hit('bass', bar, 0, r0, lv, dur16=16, jitter=0)
        elif two:
            (_, _, c1, r1), (_, _, c2, r2) = roots
            b(bar, 0, r1, 7, lv)
            b(bar, 8, r2, 7, lv)
        elif i == 4:
            b(bar, 0, r0, 16, lv, gap=0.98)
        else:
            b(bar, 0, r0, 9, lv)
            b(bar, 10, fifth(c0, r0), 4, lv - 8)


BASS_LEVEL = {'Intro': (58, 60), 'Verse 1': (60, 64), 'Verse 2': (64, 68), 'Pre-Chorus 1': (68, 78),
              'Chorus 1': (74, 78), 'Turnaround': (68, 66), 'Verse 3': (68, 72), 'Pre-Chorus 2': (74, 86),
              'Chorus 2': (88, 92), 'Bridge': (62, 94), 'Breakdown': (62, 70), 'Final Chorus': (96, 100),
              'Pull-back Chorus': (60, 62), 'Last Lift': (98, 102), 'Outro': (66, 48)}

# ---------- Rhodes (GM 5 Electric Piano 1, channel 3): pads and small answers ----------
rhodes_prev = [None]


def rhodes_voicing(chord):
    rhodes_prev[0] = voice(CH[chord][1][:3], rhodes_prev[0], 52, 66, 59)
    return rhodes_prev[0]


def pad(bar, chord_list, vel, dur_scale=1.0):
    for s, l, c in chord_list:
        for p in rhodes_voicing(c):
            hit('rhodes', bar, s, p, vel, dur16=l * dur_scale - 0.15, jitter=2)


def answer(bar, pos0, vel):
    """Three rising chord tones in a gap where the vocal rests."""
    c = chord_at(bar, pos0)
    for k, p in enumerate(rhodes_voicing(c)):
        hit('rhodes', bar, pos0 + 2 * k, p, vel - 2 * k, dur16=2, jitter=2)


def rhodes_for(sec, i, bar):
    st, name, n = sec['style'], sec['name'], len(sec['chords'])
    cs = chords_of(bar)
    last = i == n - 1
    if name == 'Verse 3' and i >= 4:
        if i == 4:
            ccs['rhodes'].append((tick(bar, 0) - 10, 11, 70))
        pad(bar, cs, 42)
    elif name == 'Pre-Chorus 2':
        if i == 0:
            ramp('rhodes', bar, 0, bar + 3, 12, 11, 70, 110)
        pad(bar, cs, 50)
    elif name == 'Chorus 2':
        if i == 0:
            ccs['rhodes'].append((tick(bar, 0) + 30, 11, 96))
        pad(bar, cs, 50)
    elif st == 'bridge':
        if i < 4:                                     # two-bar swells under the half-time feel
            if i % 2 == 0:
                ramp('rhodes', bar, 0, bar + 1, 8, 11, 50, 108)
                ramp('rhodes', bar + 1, 8, bar + 1, 15, 11, 108, 70)
            pad(bar, cs, 56)
        else:
            if i == 4:
                ramp('rhodes', bar, 0, bar + 3, 15, 11, 76, 118)
            pad(bar, cs, 58)
    elif st == 'breakdown':
        if i == 0:
            ccs['rhodes'].append((tick(bar, 0) + 30, 11, 80))
            pad(bar, cs, 46)
        else:
            ramp('rhodes', bar, 8, bar, 15.5, 11, 50, 118)
            pad(bar, cs, 56)
    elif st == 'final':
        if i == 0:
            ccs['rhodes'].append((tick(bar, 0) + 30, 11, 104))
        pad(bar, cs, 58)
    elif st == 'outro':
        if i == 0:
            ccs['rhodes'].append((tick(bar, 0) - 10, 11, 84))
        if i in (1, 3):                               # answers the piano hook in bars 81 and 83
            answer(bar, 10, 54)
        elif i == 4:
            ramp('rhodes', bar, 0, bar + 1, 15, 11, 84, 40)
            pad(bar, cs, 46)
        elif bar == TOTAL_BARS:
            for p in rhodes_voicing(cs[0][2]):
                hit('rhodes', bar, 0, p, 44, dur16=16, jitter=0)


# ---------- render every bar ----------
for sec in SECTIONS:
    lv0, lv1 = BASS_LEVEL[sec['name']]
    n = len(sec['chords'])
    for i in range(n):
        bar = sec['start'] + i
        drums_for(sec, i, bar)
        aux_for(sec, i, bar)
        bass_for(sec, i, bar, lv0 + (lv1 - lv0) * i / max(1, n - 1))
        rhodes_for(sec, i, bar)


def tidy(notes):
    """Remove same-key overlaps (shorten the earlier note) and exact duplicates."""
    notes = sorted(notes, key=lambda x: (x[1], x[0]))
    out = []
    for k, (t0, p, dur, v) in enumerate(notes):
        if k + 1 < len(notes) and notes[k + 1][1] == p:
            nt = notes[k + 1][0]
            if nt - t0 < 30:
                continue
            dur = min(dur, nt - t0 - 5)
        out.append((t0, p, max(25, min(dur, END - t0)), v))
    return out


for k in parts:
    parts[k] = tidy(parts[k])

# ---------- write MIDI ----------
TRACKS = {  # key: (track name, channel 0-based, GM program 0-based)
    'drums': ('Drums', 9, 0),
    'bass': ('Bass', 1, 33),
    'rhodes': ('Rhodes', 2, 4),
    'aux': ('Shaker & Tambourine', 9, 0),
}
INSTR = {'drums': 'Standard Drum Kit (GM channel 10)', 'bass': 'Electric Bass (finger)',
         'rhodes': 'Electric Piano 1', 'aux': 'Percussion (GM channel 10)'}


def build_track(key):
    name, ch, prog = TRACKS[key]
    tr = MidiTrack()
    head = [MetaMessage('track_name', name=name),
            MetaMessage('instrument_name', name=INSTR[key]),
            Message('program_change', channel=ch, program=prog)]
    # No volume (CC7) or pan (CC10) messages: Logic would lock its faders to them.
    # The Rhodes keeps CC11 (expression) for its swells; that doesn't touch the fader.
    if key == 'rhodes':
        head.append(Message('control_change', channel=ch, control=11, value=80))
    ev = []
    for t0, p, dur, v in parts[key]:
        ev.append((t0, 2, Message('note_on', channel=ch, note=p, velocity=v)))
        ev.append((t0 + dur, 0, Message('note_off', channel=ch, note=p, velocity=64)))
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
            [band[k] for k in ('drums', 'bass', 'rhodes', 'aux')])
save('drums_only.mid', [band['drums']])
save('bass_only.mid', [band['bass']])
save('rhodes_only.mid', [band['rhodes']])
save('aux_percussion_only.mid', [band['aux']])

# ---------- drum map documentation (generated so it always matches the file) ----------
cnt = {k: Counter(p for _, p, _, _ in parts[k]) for k in ('drums', 'aux')}
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
sec_bars = {s['name']: f"{s['start']}-{s['start'] + len(s['chords']) - 1}" for s in SECTIONS}
lines = ['# Drum map: Half Past Noon', '',
         'Both percussion tracks ("Drums" and "Shaker & Tambourine") use **MIDI channel 10** and the',
         '**General MIDI percussion map**. Logic calls middle C (note 60) **C3**, so note 36 shows up as',
         '**C1** in the Piano Roll.', '',
         '| MIDI note | Logic name | Instrument | Drums | Shaker & Tamb. |', '|---:|:---:|---|---:|---:|']
for note in sorted(DRUM_NAMES):
    if cnt['drums'][note] or cnt['aux'][note]:
        lines.append(f'| {note} | {NAMES[note % 12]}{note // 12 - 2} | {DRUM_NAMES[note]} | '
                     f'{cnt["drums"][note]} | {cnt["aux"][note]} |')
lines += ['', '## Velocity conventions', '',
          '| Range | Meaning | Where it appears |', '|---|---|---|',
          '| 20–40 | Ghost notes | quiet snare taps, hi-hat foot, soft shaker 16ths |',
          '| 40–65 | Soft / restrained | verse hats and cross-stick, half-time bridge, pull-back, outro |',
          '| 65–95 | Normal playing | verse kick, chorus snare, hats and ride, fills |',
          '| 95–120 | Accents | crashes, final-chorus backbeats, fill peaks |', '',
          'Timing drifts by at most ±4 ticks. Downbeats are never early.', '',
          '## The groove', '',
          'The kick, the bass and the piano left hand share one rhythm in each section, so they lock:',
          '',
          '- **Verses:** 1, the "a" of 2, the "and" of 3 (16ths 0, 7, 10). Cross-stick on 2 and 4 with the piano\'s',
          '  backbeat chords. That syncopated kick is what makes it bounce.',
          '- **Pre-choruses:** 1, the "and" of 2, 3, the "and" of 4. Real snare on 2 and 4.',
          '- **Choruses:** 1, the "and" of 2, the "and" of 3 (the final chorus adds the "and" of 1).', '',
          '## What the drums do in each section', '',
          f'- **Intro ({sec_bars["Intro"]}):** piano alone for two bars, then soft hats and a kick, cross-stick pickup.',
          f'- **Verse 1 ({sec_bars["Verse 1"]}):** syncopated kick, cross-stick on 2 and 4, 8th hats. Open hat at the end.',
          f'- **Verse 2 ({sec_bars["Verse 2"]}):** same groove plus ghost snares and a 16th "skip" in the hats.',
          f'- **Pre-Chorus 1 ({sec_bars["Pre-Chorus 1"]}):** real snare, kick on the "ands"; snare pickup into the chorus.',
          f'- **Chorus 1 ({sec_bars["Chorus 1"]}):** half the kit: kick on 1 and the "and" of 3, soft snare, soft hats. One crash.',
          f'- **Turnaround ({sec_bars["Turnaround"]}):** kick, cross-stick on 4, open hat.',
          f'- **Verse 3 ({sec_bars["Verse 3"]}):** the verse 2 groove; shaker joins.',
          f'- **Pre-Chorus 2 ({sec_bars["Pre-Chorus 2"]}):** builds to a tom fill, high to low, landing on two snares.',
          f'- **Chorus 2 ({sec_bars["Chorus 2"]}):** first full-band chorus: crashes, ghost notes, hats with open-hat lifts, shaker.',
          f'- **Bridge ({sec_bars["Bridge"]}):** half-time (cross-stick, then snare, on beat 3), then climbs back into time',
          '  and ends with growing snare 8ths.',
          f'- **Breakdown ({sec_bars["Breakdown"]}):** hat foot only under the piano hook, then four on the floor and a snare pickup.',
          f'- **Final Chorus ({sec_bars["Final Chorus"]}):** biggest: ride with bell on the beats, extra kick, tambourine on 2 and 4.',
          '  Stops on beat 3 of the last bar.',
          f'- **Pull-back Chorus ({sec_bars["Pull-back Chorus"]}):** kick, cross-stick on 4, hat foot; snare build in the last bar.',
          f'- **Last Lift ({sec_bars["Last Lift"]}):** full band again; tom fill into the outro.',
          f'- **Outro ({sec_bars["Outro"]}):** verse groove, then ride quarters, then one soft kick + crash on the last downbeat.']
open(os.path.join(HERE, 'drum_map.md'), 'w').write('\n'.join(lines) + '\n')

print(f'wrote {len(TRACKS) + 1} instrument tracks, {full.length:.2f} s, {TOTAL_BARS} bars')
for k in parts:
    print(f'  {TRACKS[k][0]:<20} ch {TRACKS[k][1] + 1:>2}  {len(parts[k])} notes')
