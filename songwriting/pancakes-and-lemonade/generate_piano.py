#!/usr/bin/env python3
"""Generate piano_only.mid for "Pancakes and Lemonade" (version 2 of the piano song).

Changes from ../original-piano-song/generate_piano_song.py:
  - a second 8-bar verse after verse 1, to fit the lyrics (88 bars, about 3:40)
  - chorus 1 is a lighter, held-chord version; the big pattern waits for chorus 2
  - the piano's melodic fills under sung lines are removed (verses, chorus endings,
    the pull-back chorus and the outro) to leave room for the vocal

Key E-flat major, 4/4, 96 BPM (short ritardando in the last two bars). Type 1 MIDI: track 0 = tempo/meter/key/markers,
track 1 = "Grand Piano" (GM program 1, Acoustic Grand Piano).

Requires: pip install mido
Run:      python3 generate_piano.py   (writes next to this script)
Change the seed, chords, melody fragments or velocity curves below and re-run.
"""
import itertools
import os
import random

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

PPQ = 480
S16 = PPQ // 4          # one sixteenth note
BAR = S16 * 16          # one 4/4 bar
BPM = 96
random.seed(20261010)   # fixed seed = identical file every run

PC = {'C': 0, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'Gb': 6, 'G': 7,
      'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}


def n(name):
    """'Bb4' -> 70 (C4 = 60)."""
    return 12 * (int(name[-1]) + 1) + PC[name[:-1]]


# name: (bass pitch class, right-hand pitch classes, left-hand second-note interval)
CH = {
    'Ebmaj9':    (3,  [7, 10, 2, 5], 7),
    'Bb/D':      (2,  [10, 2, 5, 0], 12),
    'Cm9':       (0,  [3, 7, 10, 2], 7),
    'Cm7/Bb':    (10, [0, 3, 7, 2], 12),
    'Abmaj9':    (8,  [0, 3, 7, 10], 7),
    'Gm11':      (7,  [10, 2, 5, 0], 7),
    'C7b9':      (0,  [4, 10, 1, 7], 7),
    'Fm9':       (5,  [8, 0, 3, 7], 7),
    'Fm7':       (5,  [5, 8, 0, 3], 7),
    'Bb9sus4':   (10, [8, 0, 3, 5], 7),
    'Bb9':       (10, [8, 2, 5, 0], 7),
    'Bb7b9':     (10, [8, 2, 5, 11], 7),
    'Bb13':      (10, [8, 2, 7, 0], 7),
    'Ab/Bb':     (10, [8, 0, 3], 12),
    'Am7b5':     (9,  [0, 3, 7], 6),
    'D7b9':      (2,  [6, 0, 3, 9], 7),
    'Gb9':       (6,  [10, 4, 1, 8], 7),
    'Bb/Ab':     (8,  [10, 2, 5, 0], 12),
    'Eb/G':      (7,  [3, 7, 10, 2], 12),
    'Gbdim7':    (6,  [9, 0, 3, 6], 6),
    'Cm7':       (0,  [3, 7, 10, 2], 7),
    'Abm6':      (8,  [11, 3, 5, 10], 7),
    'Cbmaj9':    (11, [3, 6, 10, 1], 7),
    'Db/Cb':     (11, [1, 5, 8, 3], 12),
    'Bbm9':      (10, [1, 5, 8, 0], 7),
    'Ebm9':      (3,  [6, 10, 1, 5], 7),
    'Abm9':      (8,  [11, 3, 6, 10], 7),
    'Db13':      (1,  [11, 5, 10, 3], 7),
    'Gbmaj9':    (6,  [10, 1, 5, 8], 7),
    'Gbmaj7#11': (6,  [10, 0, 5, 1], 7),
    'Abmaj7/C':  (0,  [8, 3, 7, 10], 12),
    'Abm6/Cb':   (11, [8, 3, 5], 12),
    'Ebmaj9/Bb': (10, [3, 7, 2, 5], 12),
}

VERSE = [['Ebmaj9'], ['Bb/D'], ['Cm9'], ['Cm7/Bb'],
         ['Abmaj9'], ['Gm11', 'C7b9'], ['Fm9'], ['Bb9sus4', 'Bb9']]
PRE_1 = [['Abmaj9'], ['Am7b5', 'D7b9'], ['Gm11', 'Gb9'], ['Fm7', 'Bb9sus4']]
PRE_2 = [['Abmaj9'], ['Am7b5', 'D7b9'], ['Gm11', 'Gb9'], ['Fm9', 'Bb13']]
CHORUS_A = [['Abmaj9'], ['Bb/Ab'], ['Gm11'], ['C7b9'],
            ['Fm9'], ['Bb13'], ['Gm11', 'Cm7'], ['Fm7', 'Bb9sus4']]
CHORUS_B = [['Abmaj9'], ['Bb/Ab'], ['Gm11'], ['C7b9'],
            ['Fm9'], ['Abm6'], ['Eb/G', 'Gbdim7'], ['Fm7', 'Bb9sus4']]
BRIDGE = [['Cbmaj9'], ['Db/Cb'], ['Bbm9'], ['Ebm9'],
          ['Abm9'], ['Db13'], ['Gbmaj9'], ['Gbmaj7#11']]
OUTRO = [['Ebmaj9'], ['Bb/D'], ['Abmaj7/C'], ['Abm6/Cb'],
         ['Ebmaj9/Bb'], ['Ab/Bb'], ['Ebmaj9'], ['Ebmaj9']]

# (section name, style, bars, velocity at first bar, velocity at last bar)
FORM = [
    ('Intro',                'intro',     [['Ebmaj9'], ['Bb/D'], ['Abmaj7/C'], ['Bb9sus4']], 56, 60),
    ('Verse 1',              'verse',     VERSE,    54, 58),
    ('Verse 2',              'verse',     VERSE,    58, 62),
    ('Pre-Chorus 1',         'pre',       PRE_1,    58, 68),
    ('Chorus 1',             'chorus_light', CHORUS_A, 68, 72),
    ('Turnaround',           'turn',      [['Ebmaj9'], ['Ab/Bb']], 62, 58),
    ('Verse 3',              'verse2',    VERSE,    58, 66),
    ('Pre-Chorus 2',         'pre',       PRE_2,    66, 84),
    ('Chorus 2',             'chorus',    CHORUS_B, 86, 90),
    ('Bridge',               'bridge',    BRIDGE,   50, 92),
    ('Breakdown',            'breakdown', [['Abm6'], ['Bb9sus4', 'Bb7b9']], 52, 56),
    ('Final Chorus',         'final',     CHORUS_A, 92, 98),
    ('Final Chorus (pull-back + lift)', 'lift', CHORUS_B, 64, 100),
    ('Outro',                'outro',     OUTRO,    58, 40),
]

# Right-hand register per style: (lowest, highest, centre the voicing gravitates to)
REG = {'chorus_light': (55, 70, 63), 'intro': (53, 67, 60), 'verse': (53, 67, 60), 'verse2': (53, 67, 61),
       'turn': (53, 67, 60), 'pre': (55, 70, 63), 'chorus': (56, 72, 65),
       'bridge': (55, 72, 62), 'breakdown': (53, 68, 61), 'final': (58, 75, 67),
       'lift': (58, 75, 67), 'outro': (53, 67, 60)}


def hook(names, rhythm=((2, 2), (4, 2), (6, 4), (10, 2), (12, 4))):
    """The signature cell: two pushed sixteenths, a held note, a falling answer."""
    return [(p, nm, d) for (p, d), nm in zip(rhythm, names)]


ANSWER = [(8, 'C6', 2), (10, 'Bb5', 2), (12, 'Ab5', 2), (14, 'F5', 2)]

# Right-hand melodic lines by absolute bar: (sixteenth position, note, length in sixteenths)
MEL = {
    # intro hook (no vocal yet)
    1: hook(['Bb4', 'C5', 'Eb5', 'D5', 'Bb4']),
    2: [(2, 'C5', 2), (4, 'D5', 2), (6, 'F5', 6), (12, 'Eb5', 2), (14, 'D5', 2)],
    3: hook(['C5', 'Eb5', 'G5', 'F5', 'Eb5']),
    4: [(2, 'F5', 2), (4, 'Eb5', 2), (6, 'C5', 6), (14, 'Bb4', 2)],
    # turnaround (instrumental)
    33: hook(['Bb4', 'C5', 'Eb5', 'D5', 'Bb4']),
    34: [(2, 'C5', 2), (4, 'Eb5', 2), (6, 'F5', 4), (10, 'Eb5', 2), (12, 'C5', 2), (14, 'Bb4', 2)],
    # bridge counter-line under the wordless "today"
    55: [(6, 'Bb5', 4), (10, 'Gb5', 2), (12, 'Eb5', 4)],
    56: [(6, 'Ab5', 4), (10, 'F5', 2), (12, 'Db5', 4)],
    57: [(6, 'F5', 4), (10, 'Db5', 2), (12, 'C5', 4)],
    58: [(6, 'Gb5', 6), (12, 'F5', 2), (14, 'Db5', 2)],
    # breakdown: the vocal rests here
    63: hook(['Eb5', 'F5', 'Ab5', 'Gb5', 'Eb5']),
}


def voice(pcs, prev, lo, hi, center):
    """Pick the voicing of pcs in [lo, hi] that moves least from prev."""
    lo = min(lo, hi - 14)
    opts = [[p for p in range(lo, hi + 1) if p % 12 == pc] for pc in pcs]
    best, best_cost = None, None
    for combo in itertools.product(*opts):
        c = sorted(combo)
        if c[-1] - c[0] > 14:
            continue
        cost = 0.0
        for a, b in zip(c, c[1:]):
            if b - a <= 2 and a < 58:      # no low clusters (mud)
                cost += 6
        if c[-1] - c[-2] == 1:             # no minor 2nd on top
            cost += 5
        if prev:
            cost += sum(min(abs(x - y) for y in prev) for x in c)
            cost += sum(min(abs(x - y) for x in c) for y in prev)
            cost += 0.5 * abs(c[-1] - prev[-1])
        cost += 0.4 * abs(sum(c) / len(c) - center)
        if best_cost is None or cost < best_cost:
            best, best_cost = c, cost
    return best


def pick_bass(pc, prev):
    cands = [p for p in range(33, 51) if p % 12 == pc]
    return min(cands, key=lambda p: (abs(p - prev), p))


# ---------- pass 1: lay out bars, voicings and bass notes ----------
bars, sections = [], []
prev_rh, prev_bass, bar_no = None, 39, 1
for name, style, chords, v0, v1 in FORM:
    sections.append((name, bar_no, bar_no + len(chords) - 1, style, chords))
    for i, bar_chords in enumerate(chords):
        lo, hi, center = REG[style]
        if style == 'bridge' and i >= 4:
            center += 2 * (i - 3)          # the bridge climbs
            hi += i - 3
        mel = MEL.get(bar_no, [])
        if mel:
            hi = max(62, min(hi, min(n(m[1]) for m in mel) - 1))
        vel = v0 + (v1 - v0) * (i / max(1, len(chords) - 1))
        half = 16 // len(bar_chords)
        cs = []
        for k, cname in enumerate(bar_chords):
            bpc, rpcs, lhi = CH[cname]
            prev_rh = voice(rpcs, prev_rh, lo, hi, center)
            prev_bass = pick_bass(bpc, prev_bass)
            cs.append({'name': cname, 'start': k * half, 'len': half,
                       'rh': prev_rh, 'bass': prev_bass, 'lh': lhi})
        bars.append({'no': bar_no, 'tick': (bar_no - 1) * BAR, 'style': style,
                     'section': name, 'i': i, 'n': len(chords), 'chords': cs,
                     'vel': vel, 'mel': mel})
        bar_no += 1
TOTAL_BARS = bar_no - 1

# ---------- pass 2: render notes and pedal ----------
notes, pedal = [], []


def add(t, p, d16, v, gap=0.92):
    notes.append([t, p, max(40, int(d16 * S16 * gap)), v])


def chord_at(bar, pos):
    return bar['chords'][pos * len(bar['chords']) // 16]


def stab(bar, pos, d16, v, double_top=False, roll=8, gap=0.92):
    c = chord_at(bar, pos)
    t = bar['tick'] + pos * S16
    for k, p in enumerate(c['rh']):
        top = k == len(c['rh']) - 1
        add(t + k * random.randint(0, roll), p, d16, v + (5 if top else -3), gap)
    if double_top and c['rh'][-1] + 12 <= 88:
        add(t + len(c['rh']) * 4, c['rh'][-1] + 12, d16, v + 2, gap)


def lh(bar, pos, pitch, d16, v, gap=0.95):
    add(bar['tick'] + pos * S16, pitch, d16, v, gap)


def approach(bar):
    """Chromatic neighbour leading into the next bar's bass note."""
    if bar['no'] >= TOTAL_BARS:
        return None
    nxt = bars[bar['no']]['chords'][0]['bass']
    cur = bar['chords'][-1]['bass']
    cand = [nxt - 1, nxt + 1]
    random.shuffle(cand)
    for p in cand:
        if p != cur:
            return p
    return None


def low_octave(b):
    return [b - 12, b] if b - 12 >= 28 else [b, b + 12]


def render(bar):
    s, v, cs = bar['style'], bar['vel'], bar['chords']
    t0 = bar['tick']
    mel_start = min((m[0] for m in bar['mel']), default=99)

    if s in ('intro', 'outro'):
        final = bar['no'] == TOTAL_BARS
        for c in cs:
            b = c['bass']
            if final:                              # last chord: wide, rolled, full bar
                for k, p in enumerate([b - 12, b, b + 7] + c['rh'] + [c['rh'][-1] + 12]):
                    add(t0 + k * 28, p, 16, v + 4, gap=1.0)
                continue
            lh(bar, c['start'], b, c['len'], v)
            lh(bar, c['start'] + 6, b + 12 if c['lh'] == 12 else b + c['lh'], 10, v - 12)
            for k, p in enumerate(c['rh']):
                add(t0 + c['start'] * S16 + 18 * k, p, 14, v - 12)

    elif s in ('verse', 'verse2', 'turn'):
        for c in cs:
            b, st = c['bass'], c['start']
            if len(cs) == 1:
                lh(bar, 0, b, 6, v + 8)
                lh(bar, 6, b + c['lh'], 2 if s == 'verse2' else 4, v - 6)
                if s == 'verse2':
                    lh(bar, 8, b + 12, 3, v - 4)
                    lh(bar, 11, b + c['lh'], 3, v - 8)
                else:
                    lh(bar, 10, b + 12, 2, v - 10)
            else:
                lh(bar, st, b, 6, v + 8)
                lh(bar, st + 6, b + c['lh'], 2, v - 8)
        if s == 'verse2':
            a = approach(bar)
            if a and len(cs) == 1:
                lh(bar, 14, a, 2, v - 10)
        if s == 'turn':                            # soft pad under the hook
            for k, p in enumerate(cs[0]['rh']):
                add(t0 + 16 * k, p, 14, v - 16)
        else:
            hits = [(2, 3, 0), (7, 2, -6), (12, 3, -2)] if len(cs) == 1 else \
                   [(2, 3, 0), (6, 2, -6), (10, 2, -2), (13, 3, -4)]
            if s == 'verse2':
                hits.append((15, 1, -12))          # ghosted pickup
            for pos, d, acc in hits:
                if pos < mel_start - 1:
                    stab(bar, pos, d, v + acc)

    elif s == 'pre':
        last = bar['i'] == bar['n'] - 1
        for c in cs:
            b = c['bass']
            for off in range(0, c['len'], 8):
                st = c['start'] + off
                lh(bar, st, b, 4, v + 6)
                lh(bar, st + 4, b + c['lh'], 2, v - 6)
                lh(bar, st + 6, b + 12, 2, v - 8)
        for pos in range(0, 16, 2):
            if last and pos == 14:
                continue                           # a breath before the chorus
            acc = {0: 6, 6: 4, 10: 3}.get(pos, -6) + pos * 0.4
            stab(bar, pos, 2, int(v + acc), gap=0.8)

    elif s == 'chorus_light':                      # chorus 1: held chords, two soft pushes
        for c in cs:
            b, st = c['bass'], c['start']
            lh(bar, st, b, c['len'] if len(cs) == 2 else 8, v)
            if len(cs) == 1:
                lh(bar, 8, b + c['lh'], 6, v - 10)
        for pos, d, acc in [(0, 6, 4), (6, 2, -6), (11, 4, -2)]:
            stab(bar, pos, d, int(v + acc), roll=14)

    elif s in ('chorus', 'final') or (s == 'lift' and bar['i'] >= 4):
        big = s in ('final', 'lift')
        for c in cs:
            b, st = c['bass'], c['start']
            for p in (low_octave(b) if (st == 0 or big) else [b]):
                lh(bar, st, p, 6, v + 4)
            if len(cs) == 1:
                lh(bar, 6, b, 2, v - 4)
                lh(bar, 8, b + c['lh'], 4, v - 4)
                lh(bar, 12, b + 12, 2, v - 8)
            else:
                lh(bar, st + 6, b, 2, v - 6)
        a = approach(bar)
        if a and len(cs) == 1:
            lh(bar, 14, a, 2, v - 6)
        for pos, d, acc in [(0, 3, 8), (3, 3, 2), (6, 2, -4), (8, 3, 6), (11, 3, 2), (14, 2, -4)]:
            if pos < mel_start - 1:
                stab(bar, pos, d, int(v + acc), double_top=big or pos in (0, 8))

    elif s == 'lift':                              # bars 1-4: the room goes quiet
        c = cs[0]
        lh(bar, 0, c['bass'], 16, v)
        lh(bar, 8, c['bass'] + c['lh'], 8, v - 10)
        for k, p in enumerate(c['rh']):
            add(t0 + 20 * k, p, 9, v - 10)
        stab(bar, 10, 5, v - 16)

    elif s == 'bridge':
        if bar['i'] < 4:                           # half-time, open, rolled
            c = cs[0]
            lh(bar, 0, c['bass'], 16, v)
            lh(bar, 0, c['bass'] + c['lh'], 16, v - 10)
            lh(bar, 10, c['bass'] + 12, 6, v - 14)
            for k, p in enumerate(c['rh']):
                add(t0 + 30 * k, p, 6, v - 6)
        else:                                      # the climb
            c = cs[0]
            for pos, p in zip((0, 4, 8, 12), (c['bass'], c['bass'] + c['lh'], c['bass'] + 12, c['bass'] + c['lh'])):
                lh(bar, pos, p, 4, v + (6 if pos == 0 else -2))
            step = 1 if bar['i'] == 7 else 2
            for pos in range(0, 16, step):
                if step == 1 and pos < 8 and pos % 2:
                    continue
                stab(bar, pos, step, int(v - 4 + pos * 0.8), gap=0.8)

    elif s == 'breakdown':
        if bar['i'] == 0:
            c = cs[0]
            lh(bar, 0, c['bass'], 16, v)
            lh(bar, 0, c['bass'] + c['lh'], 16, v - 10)
            for k, p in enumerate(c['rh']):
                add(t0 + 24 * k, p, 14, v - 8)
        else:
            c1, c2 = cs
            lh(bar, 0, c1['bass'], 8, v)
            for k, p in enumerate(c1['rh']):
                add(t0 + 20 * k, p, 8, v - 4)
            for pos in range(8, 16):               # 16th crescendo into the final chorus
                stab(bar, pos, 1, int(v + (pos - 8) * 6.5), roll=3, gap=0.75)
            for pos in (8, 12):
                for p in low_octave(c2['bass']):
                    lh(bar, pos, p, 4, int(v + (pos - 8) * 6))

    # melody line on top
    for pos, nm, d in bar['mel']:
        acc = 4 if s in ('chorus', 'final', 'lift') else 8
        add(t0 + pos * S16, n(nm), d, int(v + acc), gap=0.97)

    # sustain pedal
    for c in cs:
        t = t0 + c['start'] * S16
        if s in ('verse', 'verse2'):
            pedal.append((t + 20, 127))
            pedal.append((t + 5 * S16 - 10, 0))
        else:
            pedal.append((t + 4, 0))
            pedal.append((t + 30, 127))
            if c['len'] == 16 and s not in ('intro', 'outro', 'bridge', 'breakdown', 'turn') \
                    and not (s == 'lift' and bar['i'] < 4):
                pedal.append((t + 8 * S16 + 4, 0))
                pedal.append((t + 8 * S16 + 30, 127))


for bar in bars:
    render(bar)

END = TOTAL_BARS * BAR
pedal.append((END - 1, 0))

# humanise: small timing drift and velocity variation (never before bar 1 / after the end)
for nt in notes:
    if nt[0] % BAR != 0:
        nt[0] = max(0, nt[0] + random.randint(-5, 5))
    nt[3] = max(24, min(118, int(nt[3] + random.randint(-4, 4))))
    nt[2] = min(nt[2], END - nt[0])

# no overlapping notes on the same key: shorten the earlier one
notes.sort(key=lambda x: (x[1], x[0]))
clean = []
for k, nt in enumerate(notes):
    if k + 1 < len(notes) and notes[k + 1][1] == nt[1]:
        nxt = notes[k + 1][0]
        if nxt <= nt[0]:
            continue                              # exact duplicate
        nt[2] = min(nt[2], nxt - nt[0] - 10)
    if nt[2] >= 30:
        clean.append(nt)
notes = clean

# ---------- write the file ----------
mid = MidiFile(type=1, ticks_per_beat=PPQ)

conductor = MidiTrack()
mid.tracks.append(conductor)
cev = [(0, MetaMessage('track_name', name='Tempo & Meter')),
       (0, MetaMessage('time_signature', numerator=4, denominator=4,
                       clocks_per_click=24, notated_32nd_notes_per_beat=8)),
       (0, MetaMessage('key_signature', key='Eb')),
       (0, MetaMessage('set_tempo', tempo=bpm2tempo(BPM)))]
for name, start, end, *_ in sections:
    cev.append(((start - 1) * BAR, MetaMessage('marker', text=f'{name} (bars {start}-{end})')))
R0 = (TOTAL_BARS - 2) * BAR
RIT = [(R0, 92), (R0 + 8 * S16, 90), (R0 + BAR, 86), (R0 + BAR + 8 * S16, 80)]
for t, bpm in RIT:
    cev.append((t, MetaMessage('set_tempo', tempo=bpm2tempo(bpm))))
cev.sort(key=lambda e: e[0])

piano = MidiTrack()
mid.tracks.append(piano)
pev = [(0, MetaMessage('track_name', name='Grand Piano')),
       (0, MetaMessage('instrument_name', name='Acoustic Grand Piano')),
       (0, Message('program_change', channel=0, program=0))]
# no CC7/CC10: Logic would lock the track's volume and pan faders to them
# order key: note-offs (0) before pedal (1) before note-ons (2) at the same tick
for t, p, d, v in notes:
    pev.append((t, 2, Message('note_on', channel=0, note=p, velocity=v)))
    pev.append((t + d, 0, Message('note_off', channel=0, note=p, velocity=64)))
last = None
for t, val in sorted(pedal):
    if val != last:
        pev.append((t, 1, Message('control_change', channel=0, control=64, value=val)))
        last = val
head, body = pev[:3], sorted(pev[3:], key=lambda e: (e[0], e[1]))


def write(track, events, end):
    now = 0
    for t, msg in events:
        track.append(msg.copy(time=t - now))
        now = t
    track.append(MetaMessage('end_of_track', time=end - now))


write(conductor, cev, END)
write(piano, [(0, m) for _, m in head] + [(t, m) for t, _, m in body], END)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'piano_only.mid')
mid.save(out)
print(f'wrote {out}: {TOTAL_BARS} bars, {len(notes)} notes, {mid.length:.2f} s')
for name, start, end, style, chords in sections:
    print(f'  bars {start:>2}-{end:>2}  {name}: ' + ' | '.join(' '.join(b) for b in chords))
