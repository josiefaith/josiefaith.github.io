#!/usr/bin/env python3
"""Reopen every It's Rainin' Honey file and check structure, alignment, musical sanity, playability,
the loudness arc and originality against Pancakes and Lemonade. Exit code 1 on any failure."""
import ast
import math
import os
import re
import sys

from mido import MidiFile, tempo2bpm

import chord_shapes as cs
import generate_piano as gp
from song import (BAR, BPM, CH, CHORUS_CELL, END, FORM, HOOK_RHYTHM, KEY, PPQ, QUALITY, S16, TOTAL_BARS,
                  VERSE_STABS, chord_tones, parse, sections, timeline)

HERE = os.path.dirname(os.path.abspath(__file__))
PANCAKES = os.path.join(HERE, '..', 'PANCAKESLEMONADE', 'pancakes-and-lemonade')
ok = True


def check(cond, msg):
    global ok
    print(('PASS ' if cond else 'FAIL ') + msg)
    ok &= bool(cond)


def notes_of(track):
    t, on, out, chans, cc = 0, {}, [], set(), []
    for m in track:
        t += m.time
        if m.type == 'note_on' and m.velocity > 0:
            on[(m.channel, m.note)] = (t, m.velocity)
            chans.add(m.channel)
        elif m.type in ('note_on', 'note_off') and (m.channel, m.note) in on:
            s, v = on.pop((m.channel, m.note))
            out.append((s, t, m.note, v))
        elif m.type == 'control_change':
            cc.append(m.control)
    return out, chans, on, t, cc


SECS = sections()
TL = timeline()
full = MidiFile(os.path.join(HERE, 'full_song_multitrack.mid'))

print('== full_song_multitrack.mid ==')
check(full.type == 1 and full.ticks_per_beat == PPQ == 480, f'Standard MIDI File type {full.type}, {full.ticks_per_beat} PPQ')
names = [t.name for t in full.tracks]
TRACKS = ['Grand Piano', 'Drums', 'Bass', 'Rhodes', 'Shaker & Tambourine', 'Wurli']
check(names == ['Tempo & Meter'] + TRACKS, f'{len(names)} tracks: {names}')

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
        marks.append((t, m.text))
check(sigs == [(0, '4/4')] and keys == [(0, KEY)], f'meter {sigs}, key {keys}')
check(tempos[0] == (1, float(BPM)) and all(b >= TOTAL_BARS - 1 for b, _ in tempos[1:]),
      f'tempo map (bar, BPM): {tempos}  (ritardando only in the last two bars)')
want_marks = [((a - 1) * BAR, f'{n} (bars {a}-{b})') for n, _, a, b, _ in SECS]
check(marks == want_marks, f'{len(marks)} section markers on the section boundaries: ' +
      ', '.join(f'{x[1]}' for x in marks))
check(180 <= full.length <= 240, f'duration {full.length:.2f} s ({int(full.length // 60)}:{full.length % 60:05.2f}), '
      f'{TOTAL_BARS} bars (3:00-4:00 required)')

EXPECT = {'Grand Piano': ({0}, 0), 'Drums': ({9}, 0), 'Bass': ({1}, 33), 'Rhodes': ({2}, 4),
          'Shaker & Tambourine': ({9}, 0), 'Wurli': ({3}, 4)}
ALLOWED_CC = {'Grand Piano': {64}, 'Drums': set(), 'Bass': set(), 'Rhodes': {11}, 'Shaker & Tambourine': set(), 'Wurli': set()}
data = {}
for tr in full.tracks[1:]:
    ns, chans, hanging, end, cc = notes_of(tr)
    progs = [m.program for m in tr if m.type == 'program_change']
    data[tr.name] = ns
    exp_ch, exp_prog = EXPECT[tr.name]
    check(chans == exp_ch and progs == [exp_prog],
          f'{tr.name:<20} channel {sorted(c + 1 for c in chans)}, program {[p + 1 for p in progs]} (1-based GM), '
          f'{len(ns)} notes')
    check(set(cc) <= ALLOWED_CC[tr.name], f'{tr.name:<20} controllers used: {sorted(set(cc))} (no CC7 volume, no CC10 pan)')
    check(not hanging and end == END, f'{tr.name:<20} no hanging notes; track ends exactly at bar {TOTAL_BARS}\'s barline')
    check(all(0 <= s < e <= END for s, e, _, _ in ns) and min(e - s for s, e, _, _ in ns) >= 25,
          f'{tr.name:<20} every note inside bars 1-{TOTAL_BARS}, none shorter than 25 ticks')
check(max(e for nm in data for _, e, _, _ in data[nm]) == END, 'final notes end exactly on the last barline (no trailing silence)')
LAST = (TOTAL_BARS - 1) * BAR
landed = [nm for nm in data if any(s == LAST for s, *_ in data[nm])]
check(landed == TRACKS, f'every instrument plays the last downbeat together: {landed}')

# ---- other files: same conductor track, matching parts ----
print('\n== single-instrument files and chord guide ==')
for fn, nm in [('piano_only.mid', 'Grand Piano'), ('drums_only.mid', 'Drums'), ('bass_only.mid', 'Bass'),
               ('rhodes_only.mid', 'Rhodes'), ('aux_percussion_only.mid', 'Shaker & Tambourine'), ('wurli_only.mid', 'Wurli'),
               ('chord_guide.mid', None)]:
    f = MidiFile(os.path.join(HERE, fn))
    same_cond = list(f.tracks[0]) == list(full.tracks[0])
    same = nm is None or list(f.tracks[1]) == list(full.tracks[names.index(nm)])
    check(f.type == 1 and f.ticks_per_beat == PPQ and len(f.tracks) == 2 and same and same_cond
          and abs(f.length - full.length) < 0.01,
          f'{fn:<24} type 1, same tempo/meter/key/markers, {"matches the multitrack" if nm else "chord track"}, {f.length:.2f} s')
guide, _, gh, gend, gcc = notes_of(MidiFile(os.path.join(HERE, 'chord_guide.mid')).tracks[1])
check(not gh and gend == END and not gcc, 'chord_guide.mid: no hanging notes, ends on the last barline, no controllers')


def chord_at(tk):
    b, pos = tk // BAR + 1, (tk % BAR) / S16
    for st, ln, c in TL[b]:
        if st <= pos < st + ln:
            return c, pos - st
    return TL[b][-1][2], 0


bad_guide = [(s, p) for s, _, p, _ in guide if p % 12 not in chord_tones(chord_at(s + 8)[0])]
groups = {}
for s, _, p, _ in guide:
    groups.setdefault(s, []).append(p)
bass_ok = all(min(ps) % 12 == CH[chord_at(s + 8)[0]][0] and sorted(ps)[1] - min(ps) >= 5 for s, ps in groups.items())
check(not bad_guide and bass_ok, f'chord guide: {len(groups)} block chords, all chord tones, bass note alone underneath')

# ---- percussion ----
print('\n== drums, bass, Rhodes ==')
doc = set(int(x) for x in re.findall(r'^\| (\d+) \|', open(os.path.join(HERE, 'drum_map.md')).read(), re.M))
used = {p for nm in ('Drums', 'Shaker & Tambourine') for *_, p, _ in data[nm]}
GM = {35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 69, 70, 82}
check(used == doc and used <= GM, f'drum notes used {sorted(used)} = drum_map.md, all General MIDI percussion')
dv = [v for *_, v in data['Drums']]
check(min(dv) >= 15 and max(dv) <= 122, f'drum velocities {min(dv)}-{max(dv)} ({len(set(dv))} distinct)')
bp = [p for *_, p, _ in data['Bass']]
check(28 <= min(bp) and max(bp) <= 55, f'bass range MIDI {min(bp)}-{max(bp)} (E1-G3 = 28-55)')

changes = [(b, st) for b, cells in TL.items() for st, _, _ in cells]
missed = []
for b, st in changes:
    t0 = (b - 1) * BAR + st * S16
    chord = chord_at(t0)[0]
    plays = [p for s, e, p, _ in data['Bass'] if s <= t0 + 12 and e > t0 + 12]
    if not plays or plays[0] % 12 != CH[chord][0]:
        if b > 2 or plays:                           # the bass waits for bar 3 (intro: piano alone)
            missed.append((b, st, chord, plays))
check(not missed, f'bass sounds the chord\'s bass note on every chord change from bar 3 '
      f'({len([c for c in changes if c[0] >= 3])} changes){": " + str(missed[:5]) if missed else ""}')
odd = [(s // BAR + 1, (s % BAR) // S16, p) for s, _, p, _ in data['Bass']
       if p % 12 not in chord_tones(chord_at(s + 8)[0]) and round((s % BAR) / S16) != 14]
check(not odd, f'bass non-chord tones only as approach notes on the last 8th of a bar{": " + str(odd[:5]) if odd else ""}')
rh_bad = [(s // BAR + 1, p) for s, _, p, _ in data['Rhodes'] if p % 12 not in chord_tones(chord_at(s + 8)[0])]
check(not rh_bad, f'Rhodes plays only chord tones ({len(data["Rhodes"])} notes){": " + str(rh_bad[:5]) if rh_bad else ""}')
sec_of = {}
for n, st, a, b, _ in SECS:
    for x in range(a, b + 1):
        sec_of[x] = n
rh_secs = sorted({sec_of[s // BAR + 1] for s, *_ in data['Rhodes']}, key=lambda n: [x[0] for x in SECS].index(n))
check(not {'Chorus 1', 'Verse 1', 'Verse 2', 'Pre-Chorus 1'} & set(rh_secs), f'Rhodes sits out verses 1-2, pre 1 and chorus 1; plays in: {rh_secs}')
import generate_arrangement as ga  # noqa: E402  (rebuilds the files identically; reads the Wurli hook data)
hook_ticks = {(b - 1) * BAR + pos * S16: p for b, k in ga.WURLI_HOOK_BARS.items() for pos, p, _ in ga.WURLI_HOOK[k]}
wu = data['Wurli']
hook_ok = all(any(abs(s - t) <= 4 and p == hp for s, _, p, _ in wu) for t, hp in hook_ticks.items())
check(hook_ok, f'Wurli plays josie\'s hook note for note in bars 5-8 and 35-38 ({len(hook_ticks)} notes)')
wu_bad = [(s // BAR + 1, p) for s, _, p, _ in wu if s // BAR + 1 not in ga.WURLI_HOOK_BARS
          and p % 12 not in chord_tones(chord_at(s + 8)[0])]
check(not wu_bad, f'Wurli comping uses only chord tones outside the hook bars{": " + str(wu_bad[:5]) if wu_bad else ""}')
wu_rng = [p for *_, p, _ in wu]
check(min(wu_rng) >= 55 and max(wu_rng) <= 69 and not any(s // BAR + 1 <= 4 for s, *_ in wu),
      f'Wurli stays in MIDI {min(wu_rng)}-{max(wu_rng)} (G2-A3 in Logic) and enters at the verse (bar 5)')
kick = [s for s, _, p, _ in data['Drums'] if p == 36]
locked = sum(1 for k in kick if any(abs(k - s) <= 12 for s, *_ in data['Bass']))
check(locked / len(kick) >= 0.8, f'kick/bass lock: {locked}/{len(kick)} kicks land with a bass note')
lh_ticks = [s for s, _, p, _ in data['Grand Piano'] if p < 52]
v1 = [s for s in kick if 5 <= s // BAR + 1 <= 42 and sec_of[s // BAR + 1].startswith('Verse')]
locked_lh = sum(1 for k in v1 if any(abs(k - s) <= 12 for s in lh_ticks + [x[0] for x in data['Bass']]))
check(locked_lh == len(v1), f'verse kicks all land with the bass or the piano left hand ({locked_lh}/{len(v1)})')

# ---- arrangement arc ----
print('\n== loudness arc ==')
print('  Level = 10*log10(sum of (velocity/127)^2 over every note per bar), all five instrument tracks.')
print('  Same idea as Pancakes\' validate_arrangement.py (notes per bar x velocity), expressed in dB.')


def level(a, b):
    ns = [x for nm in TRACKS for x in data[nm] if a <= x[0] // BAR + 1 <= b]
    e = sum((x[3] / 127) ** 2 for x in ns) / (b - a + 1)
    return 10 * math.log10(e), len(ns) / (b - a + 1), sum(x[3] for x in ns) / len(ns)


LV = {}
for n, _, a, b, _ in SECS:
    LV[n] = level(a, b)
    print(f'  {n:<18} bars {a:>2}-{b:<2}  {LV[n][0]:6.1f} dB   {LV[n][1]:5.1f} notes/bar   mean vel {LV[n][2]:4.0f}')
d_v1 = LV['Final Chorus'][0] - LV['Verse 1'][0]
check(d_v1 >= 3, f'verse 1 is {d_v1:.1f} dB quieter than the final chorus (need at least 3)')
d_pb = LV['Pull-back Chorus'][0] - LV['Verse 1'][0]
check(abs(d_pb) <= 2, f'pull-back chorus is within 2 dB of verse 1 ({d_pb:+.1f} dB)')
c1, c2, fc = LV['Chorus 1'], LV['Chorus 2'], LV['Final Chorus']
check(c1[0] < c2[0] < fc[0] and c1[1] < c2[1] and c1[2] < c2[2],
      f'chorus 1 ({c1[0]:.1f} dB, {c1[1]:.0f} notes/bar) < chorus 2 ({c2[0]:.1f} dB, {c2[1]:.0f}) '
      f'< final chorus ({fc[0]:.1f} dB, {fc[1]:.0f})')
check(LV['Last Lift'][0] >= fc[0] - 0.5, f'last lift ({LV["Last Lift"][0]:.1f} dB) is as big as the final chorus')

# ---- piano: room for the vocal, playability ----
print('\n== piano ==')
style_of = {n: st for n, st, *_ in FORM}
hook_secs = {sec_of[b] for b in gp.MEL}
check(all(style_of[s] in ('intro', 'turn', 'breakdown', 'outro') for s in hook_secs),
      f'piano melody only where the vocal rests: bars {sorted(gp.MEL)} in {sorted(hook_secs)}')
bars = gp.layout()
rh_all = [p for b in bars for c in b['chords'] for p in c['rh']]
rh_span = max(c['rh'][-1] - c['rh'][0] for b in bars for c in b['chords'])
lh_span = max(c['lh'] for b in bars for c in b['chords'])
in_zone = sum(1 for p in rh_all if 55 <= p <= 67) / len(rh_all)
check(rh_span <= 14 and lh_span <= 12, f'hand spans: right hand at most {rh_span} semitones (a ninth = 14), '
      f'left hand bass + 5th/octave (at most {lh_span})')
check(in_zone >= 0.75 and min(rh_all) >= 53 and max(rh_all) <= 72,
      f'right-hand chord notes {in_zone:.0%} inside G3-G4 (MIDI 55-67), all within F3-C5')
voiced_ok = all(set(p % 12 for p in c['rh']) <= chord_tones(c['name']) for b in bars for c in b['chords'])
check(voiced_ok, 'every piano voicing uses only tones of its chord')

# ---- guitar ----
print('\n== guitar ==')
V = cs.piano_voicings()
capo, shapes, totals = cs.guitar_shapes(list(V))
bad = [n for n, ((_, combo), _) in shapes.items()
       if not cs.is_barre_free(combo) or max(f or 0 for f in combo) > cs.MAX_FRET]
check(len(shapes) == len(V) == len(CH) and not bad,
      f'capo {capo}: all {len(shapes)} chords have a shape with no barre, at most 4 fretted notes, within 4 frets of the capo')
for n, ((_, combo), easy) in shapes.items():
    miss = cs.missing_colour(n, combo, capo)
    print(f'  {n:<10} {cs.shape_name(n, capo, combo, easy):<10} '
          + ''.join('x' if f is None else str(f) for f in combo)
          + (f'   easier version: leaves out {", ".join(miss)}' if easy and miss else ''))

# ---- originality vs Pancakes and Lemonade ----
print('\n== originality vs Pancakes and Lemonade ==')
src = open(os.path.join(PANCAKES, 'generate_piano.py')).read()
pk = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in
            {'CH', 'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'} for t in node.targets):
        exec(compile(ast.Module([node], []), 'pancakes', 'exec'), pk)
pk_key = re.search(r"key_signature', key='(\w+)'", src).group(1)
check(pk_key != KEY and KEY != 'Gb', f'different key: Pancakes {pk_key} major, this song {KEY} major')
PK_TONIC, TONIC = 3, 9                                # E-flat, A

PK_QUAL = {'Ebmaj9': 'maj9', 'Bb/D': '', 'Cm9': 'm9', 'Cm7/Bb': 'm7', 'Abmaj9': 'maj9', 'Gm11': 'm11',
           'C7b9': '7b9', 'Fm9': 'm9', 'Fm7': 'm7', 'Bb9sus4': '9sus4', 'Bb9': '9', 'Bb7b9': '7b9',
           'Bb13': '13', 'Ab/Bb': '', 'Am7b5': 'm7b5', 'D7b9': '7b9', 'Gb9': '9', 'Bb/Ab': '', 'Eb/G': '',
           'Gbdim7': 'dim7', 'Cm7': 'm7', 'Abm6': 'm6', 'Cbmaj9': 'maj9', 'Db/Cb': '', 'Bbm9': 'm9',
           'Ebm9': 'm9', 'Abm9': 'm9', 'Db13': '13', 'Gbmaj9': 'maj9', 'Gbmaj7#11': 'maj7#11',
           'Abmaj7/C': 'maj7', 'Abm6/Cb': 'm6', 'Ebmaj9/Bb': 'maj9'}
FLATPC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def family(q):
    """Broad chord family, so 'maj9' vs 'maj7' or 'm9' vs 'm11' still count as the same chord."""
    if q.startswith('m') and not q.startswith('maj'):
        return 'min'
    if 'sus' in q:
        return 'sus'
    if q in ('7', '9', '13', '7b9'):
        return 'dom'
    if q in ('dim7', 'm7b5'):
        return 'dim'
    return 'maj'


def pk_degree(name):
    root = re.match(r'[A-G]b?', name).group()
    r = (FLATPC[root[0]] - root[1:].count('b')) % 12
    return ((r - PK_TONIC) % 12, family(PK_QUAL[name]), (CH_PK[name][0] - PK_TONIC) % 12)


def my_degree(name):
    r, q, bass, _ = parse(name)
    return ((r - TONIC) % 12, family(q), (bass - TONIC) % 12)


CH_PK = pk['CH']
pk_seq = [c for _, _, chords, _, _ in pk['FORM'] for bc in chords for c in bc]
my_seq = [c for _, _, chords, _, _ in FORM for bc in chords for c in bc]


def windows(seq, fn):
    deg = [fn(c) for c in seq]
    deg = [d for k, d in enumerate(deg) if k == 0 or d != deg[k - 1]]   # a held chord is one chord
    return {tuple(deg[k:k + 4]) for k in range(len(deg) - 3)}


shared = windows(my_seq, my_degree) & windows(pk_seq, pk_degree)
check(not shared, f'no four-chord sequence (as scale degrees, any key) in the same order as Pancakes '
      f'({len(windows(my_seq, my_degree))} of ours vs {len(windows(pk_seq, pk_degree))} of theirs){": " + str(shared) if shared else ""}')
abs_shared = {tuple(my_seq[k:k + 4]) for k in range(len(my_seq) - 3)} & {tuple(pk_seq[k:k + 4]) for k in range(len(pk_seq) - 3)}
check(not abs_shared, 'no four-chord sequence by name either')

pk_hook = ast.literal_eval(re.search(r'def hook\(names, rhythm=(\(\([^)]*\)(?:, \([^)]*\))*\))', src).group(1))
pk_hook_on = tuple(p for p, _ in pk_hook)
pk_chorus = (0, 3, 6, 8, 11, 14)
pk_verse = (2, 7, 12)
check('[(0, 3, 8), (3, 3, 2), (6, 2, -4), (8, 3, 6), (11, 3, 2), (14, 2, -4)]' in src and
      '[(2, 3, 0), (7, 2, -6), (12, 3, -2)]' in src, 'Pancakes chorus cell (0 3 6 8 11 14) and verse stabs (2 7 12) read from its source')
check(HOOK_RHYTHM != pk_hook_on and len(HOOK_RHYTHM) != len(pk_hook_on),
      f'hook rhythm {HOOK_RHYTHM} (6 notes) differs from Pancakes {pk_hook_on} (5 notes)')
gaps = lambda cell: tuple(b - a for a, b in zip(cell, cell[1:] + (cell[0] + 16,)))
check(CHORUS_CELL != pk_chorus and gaps(CHORUS_CELL) != gaps(pk_chorus) and (3, 3, 2) not in
      {gaps(CHORUS_CELL)[k:k + 3] for k in range(len(CHORUS_CELL))},
      f'chorus cell {CHORUS_CELL} = {"+".join(map(str, gaps(CHORUS_CELL)))}, not Pancakes\' 3+3+2 {pk_chorus}')
check(set(VERSE_STABS) != set(pk_verse), f'verse stabs on {VERSE_STABS} (backbeat), Pancakes used {pk_verse}')

# the rendered piano really uses those cells
pn = data['Grand Piano']
hook_on = tuple(sorted({round((s % BAR) / S16) for s, _, p, _ in pn if s // BAR + 1 == 1 and p >= 69}))
check(hook_on == HOOK_RHYTHM, f'piano hook in bar 1 plays on 16ths {hook_on}')
c2 = [b for n, _, a, b2, ch in SECS if n == 'Chorus 2' for b in range(a, b2 + 1) if len(TL[b]) == 1]
rh_on = {round((s % BAR) / S16) % 16 for s, _, p, _ in pn if s // BAR + 1 in c2 and p >= 55}
check(rh_on == set(CHORUS_CELL), f'chorus 2 right hand hits on 16ths {sorted(rh_on)}')
rh_of = {b['no']: {p for c in b['chords'] for p in c['rh']} - {c['bass'] + c['lh'] for c in b['chords']} for b in bars}
v1b = [b for n, _, a, b2, ch in SECS if n == 'Verse 1' for b in range(a, b2 + 1)]
rh_on = {round((s % BAR) / S16) % 16 for s, _, p, _ in pn if s // BAR + 1 in v1b and p in rh_of[s // BAR + 1]}
check(rh_on == set(VERSE_STABS), f'verse 1 right hand hits on 16ths {sorted(rh_on)}')

print('\nALL CHECKS PASSED' if ok else '\nSOME CHECKS FAILED')
sys.exit(0 if ok else 1)
