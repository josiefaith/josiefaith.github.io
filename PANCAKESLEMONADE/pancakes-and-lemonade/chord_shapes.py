"""Chord diagrams for the lead sheet: piano voicings from the arrangement, easiest guitar shapes.

piano_voicings()  the voicing the track's piano plays most often for each chord
guitar_shapes()   searches every fingering in the first frets (with a capo) and keeps the easiest
piano_svg(), guitar_svg()  small inline SVG diagrams, coloured by the page's CSS tokens
"""
import os
import re
from collections import Counter, OrderedDict
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# semitones above the root; the same spelling the chord guide uses
QUALITY = {
    '': (0, 4, 7), 'maj7': (0, 4, 7, 11), 'maj9': (0, 4, 7, 11, 14),
    'maj7#11': (0, 4, 7, 11, 18), 'm7': (0, 3, 7, 10), 'm9': (0, 3, 7, 10, 14),
    'm11': (0, 3, 7, 10, 14, 17), 'm6': (0, 3, 7, 9), 'm7b5': (0, 3, 6, 10),
    'dim7': (0, 3, 6, 9), '9': (0, 4, 7, 10, 14), '7b9': (0, 4, 7, 10, 13),
    '9sus4': (0, 5, 7, 10, 14), '13': (0, 4, 7, 10, 14, 21),
}
# the tones that make each chord sound like itself (besides the root)
CORE = {'': {4}, 'maj7': {4, 11}, 'maj9': {4, 11}, 'maj7#11': {4, 11}, 'm7': {3, 10},
        'm9': {3, 10}, 'm11': {3, 10}, 'm6': {3, 9}, 'm7b5': {3, 6, 10}, 'dim7': {3, 6, 9},
        '9': {4, 10}, '7b9': {4, 10}, '9sus4': {5, 10}, '13': {4, 10}}
COLOUR = {'maj9': {14}, 'm9': {14}, '9': {14}, '9sus4': {14}, 'm11': {17}, '13': {21},
          '7b9': {13}, 'maj7#11': {18}}
EASY_NAME = {'maj9': 'maj7', 'm9': 'm7', 'm11': 'm7', '9': '7', '13': '7', '7b9': '7',
             '9sus4': '7sus4', 'maj7#11': 'maj7'}


def parse(name):
    root, qual, slash = re.fullmatch(r'([A-G]b?)([^/]*)(?:/([A-G]b?))?', name).groups()
    pc = lambda s: (PC[s[0]] - s[1:].count('b')) % 12
    r = pc(root)
    return r, qual, (pc(slash) if slash else r), slash


# ---------- note names ----------
FLATS = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B']


def note_name(pc, chord):
    """Spell a pitch class the way it reads in this chord (C♭ and F♭ in the G♭ bridge, F♯ in D7)."""
    root = re.match(r'[A-G]b?m?', chord).group()
    if pc == 11 and (root in ('Gb', 'Cb', 'Db', 'Abm', 'Ebm', 'Bbm') or 'Cb' in chord):
        return 'C♭'
    if pc == 4 and root == 'Gb':
        return 'F♭'
    if pc == 6 and root == 'D':
        return 'F♯'
    return FLATS[pc]


def with_octave(midi, chord):
    return f'{note_name(midi % 12, chord)}{midi // 12 - 1}'


# ---------- piano ----------
def piano_voicings():
    """Most common (left hand, right hand) voicing per chord, in order of first appearance."""
    src = open(os.path.join(HERE, 'generate_piano.py')).read()
    ns = {'__file__': os.path.join(HERE, 'generate_piano.py'), '__name__': 'chord_shapes'}
    exec(compile(src[:src.index('# ---------- pass 2')], 'generate_piano.py', 'exec'), ns)
    seen = OrderedDict()
    for bar in ns['bars']:
        for c in bar['chords']:
            lh = (c['bass'], c['bass'] + c['lh'])
            seen.setdefault(c['name'], Counter())[(lh, tuple(c['rh']))] += 1
    out = OrderedDict()
    for name, cnt in seen.items():
        (lh, rh), _ = cnt.most_common(1)[0]
        lh = [p for p in lh if p not in rh]          # don't show a key twice
        out[name] = (lh, list(rh))
    return out


WHITE = {0, 2, 4, 5, 7, 9, 11}


def piano_svg(lh, rh, chord):
    notes = lh + rh
    lo, hi = min(33, min(notes)), max(72, max(notes))  # same A1-C5 keyboard for every chord
    while lo % 12 not in WHITE:
        lo -= 1
    while hi % 12 not in WHITE:
        hi += 1
    whites = [p for p in range(lo, hi + 1) if p % 12 in WHITE]
    w, h, bw, bh = 9, 46, 6, 28
    x_of = {p: i * w for i, p in enumerate(whites)}
    parts = [f'<svg class="kb" viewBox="0 0 {len(whites) * w + 1} {h + 12}" role="img" '
             f'aria-label="{chord} on piano">']
    for p in whites:
        cls = 'k-lh' if p in lh else 'k-rh' if p in rh else 'k-w'
        parts.append(f'<rect class="{cls}" x="{x_of[p] + .5}" y=".5" width="{w}" height="{h}" rx="1.5"/>')
    for p in range(lo + 1, hi):
        if p % 12 not in WHITE:
            x = x_of[p - 1] + w - bw / 2 + .5
            cls = 'k-lh' if p in lh else 'k-rh' if p in rh else 'k-b'
            parts.append(f'<rect class="{cls} blk" x="{x}" y=".5" width="{bw}" height="{bh}" rx="1"/>')
    if 60 in x_of:                                   # mark middle C
        parts.append(f'<circle class="k-mid" cx="{x_of[60] + w / 2 + .5}" cy="{h + 6}" r="1.8"/>')
    parts.append('</svg>')
    return ''.join(parts)


# ---------- guitar ----------
TUNING = [40, 45, 50, 55, 59, 64]                    # E A D G B E
MAX_FRET = 4                                         # stay in the first four frets above the capo


def _chord_sets(name, easy):
    r, qual, bass, slash = parse(name)
    ivs = QUALITY[qual]
    allowed = {(r + i) % 12 for i in ivs} | {bass}
    need = {r} | {(r + i) % 12 for i in CORE[qual]} | {bass}
    if not easy:
        need |= {(r + i) % 12 for i in COLOUR.get(qual, ())}
    return allowed, need, bass


def _best(name, capo, easy):
    allowed, need, bass = _chord_sets(name, easy)
    opts = []
    for open_p in TUNING:
        o = [None] + [f for f in range(MAX_FRET + 1) if (open_p + capo + f) % 12 in allowed]
        opts.append(o)
    best = None
    for combo in product(*opts):
        snd = [(s, f) for s, f in enumerate(combo) if f is not None]
        if len(snd) < 3:
            continue
        s0, f0 = snd[0]
        if (TUNING[s0] + capo + f0) % 12 != bass:
            continue
        pcs = {(TUNING[s] + capo + f) % 12 for s, f in snd}
        if not need <= pcs:
            continue
        first, last = snd[0][0], snd[-1][0]
        inner = sum(1 for s in range(first, last + 1) if combo[s] is None)
        if inner > 1:
            continue
        fretted = [(s, f) for s, f in snd if f > 0]
        frets = [f for _, f in fretted]
        span = max(frets) - min(frets) if frets else 0
        if span > 3:
            continue
        barre = None
        fingers = len(frets)
        if fingers > 4:                              # needs a barre at the lowest fret
            mn = min(frets)
            at = [s for s, f in fretted if f == mn]
            lo_s, hi_s = min(at), max(at)
            if len(at) < 2 or any(combo[s] is not None and combo[s] < mn for s in range(lo_s, hi_s + 1)):
                continue
            fingers = 1 + sum(1 for f in frets if f != mn)
            if fingers > 4:
                continue
            barre = (mn, lo_s, hi_s)
        opens = sum(1 for _, f in snd if f == 0)
        score = (span * 1.5 + fingers + (3 if barre else 0) + (max(frets) if frets else 0) * .4
                 + inner * 2.5 + (6 - len(snd)) * .5 - opens * .3 + len(allowed - pcs) * .3)
        if best is None or score < best[0]:
            best = (score, combo, barre)
    return best


def guitar_shapes(names):
    """Pick one capo for the whole song that makes the shapes easiest, then the best shape per chord."""
    results = {}
    for capo in range(0, 8):
        total, shapes = 0, {}
        for n in names:
            full, easy = _best(n, capo, False), _best(n, capo, True)
            if full is None and easy is None:
                total += 50
                continue
            if full is not None and (easy is None or full[0] <= easy[0] + 2.5):
                shapes[n] = (full, False)
            else:                                    # simplified, unless it happens to hold every tone
                allowed, need_full, _ = _chord_sets(n, False)
                got = {(TUNING[s] + capo + f) % 12 for s, f in enumerate(easy[1]) if f is not None}
                shapes[n] = (easy, not need_full <= got)
            total += shapes[n][0][0]
        results[capo] = (total, shapes)
    capo = min(results, key=lambda c: results[c][0])
    return capo, results[capo][1], {c: round(results[c][0], 1) for c in results}


SHARP_SHAPE = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']


def shape_name(name, capo, easy):
    r, qual, bass, slash = parse(name)
    q = EASY_NAME.get(qual, qual) if easy else qual
    nm = SHARP_SHAPE[(r - capo) % 12] + q
    if slash:
        nm += '/' + SHARP_SHAPE[(bass - capo) % 12]
    return nm.replace('b', '♭').replace('#', '♯')


def guitar_svg(combo, barre, chord):
    sx, fy, top = 12, 13, 14
    W, H = 5 * sx + 16, top + MAX_FRET * fy + 6
    x = lambda s: 8 + s * sx
    parts = [f'<svg class="gb" viewBox="0 0 {W} {H}" role="img" aria-label="{chord} on guitar">']
    parts.append(f'<rect class="g-nut" x="{x(0)}" y="{top - 2.5}" width="{5 * sx}" height="2.5"/>')
    for i in range(1, MAX_FRET + 1):
        parts.append(f'<line class="g-line" x1="{x(0)}" x2="{x(5)}" y1="{top + i * fy}" y2="{top + i * fy}"/>')
    for s in range(6):
        parts.append(f'<line class="g-line" x1="{x(s)}" x2="{x(s)}" y1="{top}" y2="{top + MAX_FRET * fy}"/>')
    if barre:
        f, a, b = barre
        cy = top + (f - .5) * fy
        parts.append(f'<rect class="g-dot" x="{x(a) - 4}" y="{cy - 4}" width="{x(b) - x(a) + 8}" height="8" rx="4"/>')
    for s, f in enumerate(combo):
        if f is None:
            parts.append(f'<text class="g-mark" x="{x(s)}" y="{top - 5}">×</text>')
        elif f == 0:
            parts.append(f'<circle class="g-open" cx="{x(s)}" cy="{top - 7.5}" r="2.6"/>')
        elif not (barre and f == barre[0] and barre[1] <= s <= barre[2]):
            parts.append(f'<circle class="g-dot" cx="{x(s)}" cy="{top + (f - .5) * fy}" r="4"/>')
    parts.append('</svg>')
    return ''.join(parts)


def sounding_notes(combo, capo, chord):
    return ' '.join(note_name((TUNING[s] + capo + f) % 12, chord) for s, f in enumerate(combo) if f is not None)
