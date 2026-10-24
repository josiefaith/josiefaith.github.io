#!/usr/bin/env python3
"""Generate piano_only.mid for "It's Rainin' Honey".

A major, 4/4, 104 BPM (short ritardando over the last two bars). Type 1 MIDI: track 0 = tempo, meter,
key and section markers; track 1 = "Grand Piano" (GM program 1, Acoustic Grand Piano).
The chord chart and form live in song.py.

The piano plays a melodic hook only where the vocal rests: intro, turnaround, breakdown and the
outro tag. Under sung lines it only comps.

Requires: pip install mido
Run:      python3 generate_piano.py   (writes next to this script)
"""
import itertools
import os
import random

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

from song import BAR, BPM, CH, END, FORM, KEY, PPQ, RIT, S16, TOTAL_BARS, sections, \
    CHORUS_CELL, HOOK_RHYTHM, VERSE_STABS

rng = random.Random(1040)          # the piano's own random stream: fixed seed, identical file every run

PCN = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def n(name):
    """'C#5' -> 73 (C4 = 60)."""
    return 12 * (int(name[-1]) + 1) + PCN[name[:-1]]


def hook(names, rhythm=HOOK_RHYTHM, lens=(2, 1, 3, 2, 2, 4)):
    """The signature cell: a quick skip up, a held top note, a falling answer."""
    return [(p, nm, d) for p, nm, d in zip(rhythm, names, lens)]


# Right-hand melodic lines by absolute bar (sixteenth position, note, length in sixteenths).
# Only in bars where the vocal rests.
MEL = {
    # intro
    1: hook(['C#5', 'E5', 'F#5', 'E5', 'C#5', 'B4']),
    2: [(2, 'D5', 2), (4, 'C#5', 2), (6, 'B4', 2), (8, 'A4', 6)],
    3: hook(['C#5', 'E5', 'F#5', 'A5', 'F#5', 'E5']),
    4: [(2, 'D5', 2), (4, 'E5', 2), (6, 'F#5', 2), (8, 'E5', 4)],
    # turnaround
    33: hook(['C#5', 'E5', 'F#5', 'E5', 'C#5', 'B4']),
    34: [(0, 'C#5', 2), (2, 'B4', 2), (4, 'A4', 4), (8, 'B4', 2), (10, 'D5', 2), (12, 'E5', 4)],
    # breakdown (first bar only; the second bar is the build)
    63: hook(['C#5', 'E5', 'G#5', 'E5', 'C#5', 'A4']),
    # outro tag
    81: hook(['C#5', 'E5', 'F#5', 'E5', 'C#5', 'B4']),
    83: hook(['C#5', 'E5', 'F#5', 'A5', 'F#5', 'E5']),
    85: [(0, 'C#5', 2), (2, 'E5', 1), (3, 'F#5', 3), (8, 'E5', 8)],
}
HOOK_BARS = set(MEL)

# Right-hand register per style: (lowest, highest, centre the voicing gravitates to). G3 = 55, G4 = 67.
REG = {'intro': (55, 67, 61), 'verse': (55, 67, 61), 'verse2': (55, 67, 62), 'turn': (55, 67, 61),
       'pre': (55, 69, 63), 'chorus_light': (55, 69, 63), 'chorus': (56, 70, 64), 'final': (57, 71, 65),
       'pullback': (55, 67, 61), 'bridge': (55, 69, 62), 'breakdown': (55, 67, 61), 'outro': (55, 67, 61)}


def voice(pcs, prev, lo, hi, center):
    """Pick the voicing of pcs in [lo, hi] that moves least from prev (span at most a ninth)."""
    lo = min(lo, hi - 14)
    opts = [[p for p in range(lo, hi + 1) if p % 12 == pc] for pc in pcs]
    best, best_cost = None, None
    for combo in itertools.product(*opts):
        c = sorted(combo)
        if c[-1] - c[0] > 14 or len(set(c)) < len(c):
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
    cands = [p for p in range(36, 51) if p % 12 == pc]   # C2-D3: left hand stays clear of mud
    return min(cands, key=lambda p: (abs(p - prev), p))


def layout():
    """Pass 1: bars, voicings and bass notes (no notes rendered). Used by chord_shapes.py too."""
    bars, prev_rh, prev_bass, bar_no = [], None, 45, 1
    for name, style, chords, v0, v1 in FORM:
        for i, bar_chords in enumerate(chords):
            lo, hi, center = REG[style]
            if style == 'bridge' and i >= 4:
                center += i - 3                # the bridge climbs
                hi += 1
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
    return bars


# ---------- pass 2: render notes and pedal ----------
notes, pedal = [], []


def add(t, p, d16, v, gap=0.92):
    notes.append([t, p, max(40, int(d16 * S16 * gap)), int(v)])


def chord_at(bar, pos):
    for c in bar['chords']:
        if c['start'] <= pos < c['start'] + c['len']:
            return c
    return bar['chords'][-1]


def stab(bar, pos, d16, v, double_top=False, roll=8, gap=0.92):
    c = chord_at(bar, pos)
    t = bar['tick'] + pos * S16
    for k, p in enumerate(c['rh']):
        top = k == len(c['rh']) - 1
        add(t + k * rng.randint(0, roll), p, d16, v + (5 if top else -3), gap)
    if double_top and c['rh'][-1] + 12 <= 84:
        add(t + len(c['rh']) * 4, c['rh'][-1] + 12, d16, v + 2, gap)


def lh(bar, pos, pitch, d16, v, gap=0.95):
    add(bar['tick'] + pos * S16, pitch, d16, v, gap)


def second(c):
    """Left hand's second note: the 5th above the bass, or the octave on slash chords."""
    return c['bass'] + c['lh']


def render(bar, total):
    s, v, cs = bar['style'], bar['vel'], bar['chords']
    t0 = bar['tick']
    two = len(cs) == 2
    final = bar['no'] == total

    if s in ('intro', 'outro', 'turn'):
        for c in cs:
            b, st = c['bass'], c['start']
            if final:                              # last chord: wide, rolled, the whole bar
                for k, p in enumerate([b - 12, b, b + 7] + c['rh']):
                    add(t0 + k * 26, p, 16, v + 6, gap=1.0)
                continue
            lh(bar, st, b, 8 if not two else 6, v)
            lh(bar, st + (8 if not two else 4), second(c), 6 if not two else 4, v - 12)
            for k, p in enumerate(c['rh']):        # soft rolled pad under the hook
                add(t0 + st * S16 + 16 * k, p, c['len'] - 1, v - 14)

    elif s in ('verse', 'verse2'):
        # left hand locks with kick and bass on 1 and the "and" of 3
        if two:
            c1, c2 = cs
            lh(bar, 0, c1['bass'], 6, v + 8)
            lh(bar, 8, c2['bass'], 4, v + 6)
            lh(bar, 12, second(c2), 3, v - 8)
        else:
            c = cs[0]
            lh(bar, 0, c['bass'], 7, v + 8)
            if s == 'verse2':
                lh(bar, 7, c['bass'], 2, v - 6)    # the "a" of 2, with the kick
            lh(bar, 10, second(c), 4, v - 4)
        for pos in VERSE_STABS:                    # backbeat chords, with the cross-stick
            stab(bar, pos, 2, v - 2, gap=0.85)
        if s == 'verse2' and bar['i'] % 2:
            stab(bar, 15, 1, v - 14, roll=3, gap=0.8)   # ghosted pickup

    elif s == 'pre':
        last = bar['i'] == bar['n'] - 1
        for c in cs:
            b, st = c['bass'], c['start']
            lh(bar, st, b, 3, v + 6)
            lh(bar, st + 6, b + 12 if b + 12 <= 55 else b, 2, v - 6)
        for pos in (0, 4, 8, 12):                  # steady quarters that grow
            stab(bar, pos, 2, int(v + pos * 0.5 + (4 if pos == 0 else 0)), gap=0.8)
        for pos in ((6, 10, 14) if last else (14,)):
            stab(bar, pos, 1, int(v - 6 + pos * 0.8), roll=4, gap=0.8)

    elif s == 'chorus_light':                      # chorus 1: held chords and one push
        for c in cs:
            lh(bar, c['start'], c['bass'], 8 if not two else 7, v)
            if not two:
                lh(bar, 8, second(c), 6, v - 10)
        stab(bar, 0, 2, v + 4, roll=6)             # the chorus skip (1, "and" of 1), then held
        stab(bar, 2, 6, v - 2, roll=10)
        stab(bar, 10, 5, v - 2, roll=10)

    elif s in ('chorus', 'final'):
        big = s == 'final'
        if two:
            c1, c2 = cs
            for p in (c1['bass'] - 12, c1['bass']) if big else (c1['bass'],):
                lh(bar, 0, p, 5, v + 4)
            lh(bar, 6, c1['bass'], 2, v - 6)
            for p in (c2['bass'] - 12, c2['bass']) if big else (c2['bass'],):
                lh(bar, 8, p, 2, v + 2)
            lh(bar, 10, second(c2), 4, v - 6)
        else:
            c = cs[0]
            for p in (c['bass'] - 12, c['bass']):
                lh(bar, 0, p, 5, v + 4)
            lh(bar, 6, c['bass'], 2, v - 6)
            lh(bar, 10, second(c), 4, v - 4)
        for pos, d, acc in zip(CHORUS_CELL, (2, 3, 2, 2, 3), (8, -2, 2, 6, -4)):
            stab(bar, pos, d, int(v + acc), double_top=big and pos in (0, 10))
        if big and bar['i'] % 2 and bar['i'] < bar['n'] - 1:
            stab(bar, 15, 1, v - 12, roll=3, gap=0.8)

    elif s == 'pullback':                          # the room goes quiet: whole notes, soft
        c = cs[0]
        lh(bar, 0, c['bass'], 16, v)
        lh(bar, 8, second(c), 8, v - 10)
        for k, p in enumerate(c['rh']):
            add(t0 + 22 * k, p, 15, v - 8)

    elif s == 'bridge':
        if bar['i'] < 4:                           # half-time, open, rolled
            for c in cs:
                lh(bar, c['start'], c['bass'], c['len'], v)
                lh(bar, c['start'], second(c), c['len'], v - 10)
                for k, p in enumerate(c['rh']):
                    add(t0 + c['start'] * S16 + 30 * k, p, min(c['len'], 8) - 1, v - 6)
                if not two:
                    stab(bar, 10, 5, v - 14, roll=12)
        else:                                      # the climb
            c = cs[0]
            for pos, p in zip((0, 4, 8, 12), (c['bass'], second(c), c['bass'] + 12, second(c))):
                lh(bar, pos, p, 4, v + (6 if pos == 0 else -2))
            step = 4 if bar['i'] < 6 else 2
            for pos in range(0, 16, step):
                stab(bar, pos, step, int(v - 4 + pos * 0.8), gap=0.8)

    elif s == 'breakdown':
        if bar['i'] == 0:
            c = cs[0]
            lh(bar, 0, c['bass'], 16, v)
            lh(bar, 0, second(c), 16, v - 10)
            for k, p in enumerate(c['rh']):
                add(t0 + 24 * k, p, 14, v - 10)
        else:
            c1, c2 = cs
            for pos in range(0, 16, 2):            # 8th-note build into the final chorus
                stab(bar, pos, 2, int(v - 6 + pos * 3.5), roll=3, gap=0.75)
            lh(bar, 0, c1['bass'], 8, v)
            for pos in (8, 12):
                for p in (c2['bass'] - 12, c2['bass']):
                    lh(bar, pos, p, 4, int(v + (pos - 8) * 4))

    # hook melody on top
    for pos, nm, d in bar['mel']:
        add(t0 + pos * S16, n(nm), d, v + 10, gap=0.97)

    # sustain pedal: change with every chord (up just after the attack, down again)
    for c in cs:
        t = t0 + c['start'] * S16
        if s in ('verse', 'verse2', 'pre'):
            pedal.append((t + 20, 127))
            pedal.append((t + 3 * S16, 0))         # short, dry: the bounce stays crisp
        else:
            pedal.append((t + 4, 0))
            pedal.append((t + 30, 127))


def tempo_events():
    ev = [(0, MetaMessage('set_tempo', tempo=bpm2tempo(BPM)))]
    for bar_off, pos, bpm in RIT:
        ev.append(((TOTAL_BARS + bar_off) * BAR + pos * S16, MetaMessage('set_tempo', tempo=bpm2tempo(bpm))))
    return ev


def conductor_track():
    tr = MidiTrack()
    ev = [(0, MetaMessage('track_name', name='Tempo & Meter')),
          (0, MetaMessage('time_signature', numerator=4, denominator=4,
                          clocks_per_click=24, notated_32nd_notes_per_beat=8)),
          (0, MetaMessage('key_signature', key=KEY))] + tempo_events()
    for name, _, start, end, _ in sections():
        ev.append(((start - 1) * BAR, MetaMessage('marker', text=f'{name} (bars {start}-{end})')))
    ev.sort(key=lambda e: e[0])
    now = 0
    for t, m in ev:
        tr.append(m.copy(time=t - now))
        now = t
    tr.append(MetaMessage('end_of_track', time=END - now))
    return tr


def main():
    bars = layout()
    assert len(bars) == TOTAL_BARS
    for bar in bars:
        render(bar, TOTAL_BARS)
    pedal.append((END - 1, 0))

    # humanise: small timing drift and velocity variation (never before bar 1 / after the end)
    for nt in notes:
        if nt[0] % BAR != 0:
            nt[0] = max(0, nt[0] + rng.randint(-5, 5))
        nt[3] = max(24, min(118, int(nt[3] + rng.randint(-4, 4))))
        nt[2] = min(nt[2], END - nt[0])

    # no overlapping notes on the same key: shorten the earlier one
    notes.sort(key=lambda x: (x[1], x[0]))
    clean = []
    for k, nt in enumerate(notes):
        if k + 1 < len(notes) and notes[k + 1][1] == nt[1]:
            nxt = notes[k + 1][0]
            if nxt <= nt[0]:
                continue
            nt[2] = min(nt[2], nxt - nt[0] - 10)
        if nt[2] >= 30:
            clean.append(nt)

    mid = MidiFile(type=1, ticks_per_beat=PPQ)
    mid.tracks.append(conductor_track())
    piano = MidiTrack()
    mid.tracks.append(piano)
    head = [MetaMessage('track_name', name='Grand Piano'),
            MetaMessage('instrument_name', name='Acoustic Grand Piano'),
            Message('program_change', channel=0, program=0)]
    # no CC7/CC10: Logic would lock the track's volume and pan faders to them
    # order key: note-offs (0) before pedal (1) before note-ons (2) at the same tick
    ev = []
    for t, p, d, v in clean:
        ev.append((t, 2, Message('note_on', channel=0, note=p, velocity=v)))
        ev.append((t + d, 0, Message('note_off', channel=0, note=p, velocity=64)))
    last = None
    for t, val in sorted(pedal):
        if val != last:
            ev.append((t, 1, Message('control_change', channel=0, control=64, value=val)))
            last = val
    ev.sort(key=lambda e: (e[0], e[1]))
    for m in head:
        piano.append(m.copy(time=0))
    now = 0
    for t, _, m in ev:
        piano.append(m.copy(time=t - now))
        now = t
    piano.append(MetaMessage('end_of_track', time=END - now))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'piano_only.mid')
    mid.save(out)
    print(f'wrote {out}: {TOTAL_BARS} bars, {len(clean)} notes, {mid.length:.2f} s')
    for name, _, start, end, chords in sections():
        print(f'  bars {start:>2}-{end:>2}  {name}: ' + ' | '.join(' '.join(b) for b in chords))


if __name__ == '__main__':
    main()
