"""Chord diagrams for the lead sheet: piano voicings from the arrangement, easiest barre-free guitar shapes.

piano_voicings()  the voicing the track's piano plays most often for each chord
guitar_shapes()   searches every fingering within four frets above a capo, never a barre, and keeps
                  the easiest; picks the one capo that makes the whole song easiest
piano_svg(), guitar_svg()  small inline SVG diagrams, coloured by the page's CSS tokens
"""
from collections import Counter, OrderedDict
from itertools import combinations, product

from song import QUALITY, parse

# the tones that make each chord sound like itself (besides the root and the bass)
CORE = {'': {4}, 'add9': {4}, '6/9': {4}, 'maj9': {4, 11}, 'maj7#11': {4, 11}, 'm7': {3, 10},
        'm9': {3, 10}, '7': {4, 10}, '9': {4, 10}, '9sus4': {5, 10}}
COLOUR = {'add9': {14}, '6/9': {9, 14}, 'maj9': {14}, 'm9': {14}, '9': {14}, '9sus4': {14},
          'maj7#11': {18}}
COLOUR_NAME = {14: 'the 9th', 9: 'the 6th', 18: 'the ♯11'}

# ---------- note names (sharp key) ----------
SHARPS = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']


def note_name(pc, chord):
    """Spell a pitch class the way it reads in this chord (E♯ in C♯7)."""
    if pc == 5 and chord.startswith('C#'):
        return 'E♯'
    return SHARPS[pc]


def with_octave(midi, chord):
    return f'{note_name(midi % 12, chord)}{midi // 12 - 1}'


# ---------- piano ----------
def piano_voicings():
    """Most common (left hand, right hand) voicing per chord, in order of first appearance."""
    import generate_piano
    seen = OrderedDict()
    for bar in generate_piano.layout():
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


def hand_fingers(notes, hand):
    """Suggested piano fingering for one hand (1 = thumb, 5 = pinky).

    Tries every set of fingers in order and keeps the one whose finger spacing best matches the
    distance between the keys (about two semitones per finger, a little more next to the thumb).
    Right hand: lowest note gets the lowest finger. Left hand: lowest note gets the highest finger.
    """
    notes = sorted(notes)
    if len(notes) == 1:
        return {notes[0]: 5 if hand == 'L' else 1}
    best = None
    for fs in combinations(range(1, 6), len(notes)):
        seq = fs if hand == 'R' else tuple(reversed(fs))
        if (hand == 'L' and seq[0] != 5) or (hand == 'R' and seq[0] != 1):
            continue                                 # bass note on the pinky; right hand starts on the thumb
        if hand == 'R' and len(notes) >= 3 and seq[-1] != 5:
            continue
        cost = 0
        for (a, b), (fa, fb) in zip(zip(notes, notes[1:]), zip(seq, seq[1:])):
            step = abs(fb - fa)
            expect = 2 * step + (1 if 1 in (fa, fb) else 0)
            cost += (b - a - expect) ** 2
        if best is None or cost < best[0]:
            best = (cost, seq)
    return dict(zip(notes, best[1]))


def piano_svg(lh, rh, chord, fingers=True):
    notes = lh + rh
    lo, hi = min(36, min(notes)), max(72, max(notes))  # the same C2-C5 keyboard for every chord
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
    if fingers:
        fmap = {**hand_fingers(lh, 'L'), **hand_fingers(rh, 'R')}
        for p, f in fmap.items():
            cls = 'fn-lh' if p in lh else 'fn-rh'
            if p % 12 in WHITE:
                parts.append(f'<text class="kfn {cls}" x="{x_of[p] + w / 2 + .5}" y="{h - 4}">{f}</text>')
            else:
                parts.append(f'<text class="kfn {cls} kfb" x="{x_of[p - 1] + w + .5}" y="{bh - 4}">{f}</text>')
    if 60 in x_of:                                   # mark middle C
        parts.append(f'<circle class="k-mid" cx="{x_of[60] + w / 2 + .5}" cy="{h + 6}" r="1.8"/>')
    parts.append('</svg>')
    return ''.join(parts)


# ---------- guitar ----------
TUNING = [40, 45, 50, 55, 59, 64]                    # E A D G B E
MAX_FRET = 4                                         # stay in the first four frets above the capo


def chord_sets(name, easy):
    r, qual, bass, _ = parse(name)
    allowed = {(r + i) % 12 for i in QUALITY[qual]} | {bass}
    need = {r, bass} | {(r + i) % 12 for i in CORE[qual]}
    if not easy:
        need |= {(r + i) % 12 for i in COLOUR.get(qual, ())}
    return allowed, need, bass


def is_barre_free(combo):
    """At most four fretted notes, so every one gets its own finger: no barre anywhere."""
    return sum(1 for f in combo if f) <= 4


def best_shape(name, capo, easy):
    allowed, need, bass = chord_sets(name, easy)
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
        if (TUNING[s0] + capo + f0) % 12 != bass:    # lowest string plays the bass note
            continue
        pcs = {(TUNING[s] + capo + f) % 12 for s, f in snd}
        if not need <= pcs:
            continue
        first, last = snd[0][0], snd[-1][0]
        inner = sum(1 for s in range(first, last + 1) if combo[s] is None)
        if inner > 1:                                # at most one muted string inside the shape
            continue
        frets = [f for _, f in snd if f > 0]
        span = max(frets) - min(frets) if frets else 0
        if span > 3 or not is_barre_free(combo):
            continue
        opens = sum(1 for _, f in snd if f == 0)
        score = (span * 1.5 + len(frets) + (max(frets) if frets else 0) * .4
                 + inner * 2.5 + (6 - len(snd)) * .5 - opens * .3 + len(allowed - pcs) * .3)
        if best is None or score < best[0]:
            best = (score, combo)
    return best


def guitar_shapes(names, capos=range(0, 8)):
    """Pick the one capo that makes the whole song easiest (every chord must have a barre-free shape),
    then the best shape per chord. Returns capo, {name: ((score, combo), simplified?)}, totals."""
    results = {}
    for capo in capos:
        total, shapes, ok = 0, {}, True
        for nm in names:
            full, easy = best_shape(nm, capo, False), best_shape(nm, capo, True)
            if full is None and easy is None:
                ok = False
                break
            if full is not None and (easy is None or full[0] <= easy[0] + 2.5):
                shapes[nm] = (full, False)
            else:
                _, need_full, _ = chord_sets(nm, False)
                got = {(TUNING[s] + capo + f) % 12 for s, f in enumerate(easy[1]) if f is not None}
                shapes[nm] = (easy, not need_full <= got)
            total += shapes[nm][0][0]
        if ok:
            results[capo] = (total, shapes)
    capo = min(results, key=lambda c: results[c][0])
    return capo, results[capo][1], {c: round(results[c][0], 1) for c in results}


def missing_colour(name, combo, capo):
    r, qual, _, _ = parse(name)
    got = {(TUNING[s] + capo + f) % 12 for s, f in enumerate(combo) if f is not None}
    return [COLOUR_NAME[i] for i in sorted(COLOUR.get(qual, ())) if (r + i) % 12 not in got]


SHAPE_ROOT = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
EASY_QUAL = {'add9': '', '6/9': '6', 'maj9': 'maj7', 'm9': 'm7', '9': '7', '9sus4': '7sus4',
             'maj7#11': 'maj7'}


def shape_name(name, capo, combo, easy):
    """What the fingers make with the capo on (a G shape at capo 2 sounds as A)."""
    r, qual, bass, slash = parse(name)
    q = qual
    if easy:
        missing = missing_colour(name, combo, capo)
        if qual == '6/9' and missing == ['the 9th']:
            q = '6'
        elif qual == '6/9' and missing == ['the 6th']:
            q = 'add9'
        elif missing:
            q = EASY_QUAL.get(qual, qual)
    nm = SHAPE_ROOT[(r - capo) % 12] + q
    if slash:
        nm += '/' + SHAPE_ROOT[(bass - capo) % 12]
    return nm.replace('b', '♭').replace('#', '♯')


def guitar_fingers(combo):
    """Suggested fretting fingers (1 = index ... 4 = pinky), one per fretted note."""
    out = [None] * 6
    notes = sorted(((f, s) for s, f in enumerate(combo) if f), key=lambda x: (x[0], x[1]))
    if not notes:
        return out
    base, nxt = notes[0][0], 1
    for f, s in notes:
        finger = max(f - base + 1, nxt)
        out[s] = min(finger, 4)
        nxt = finger + 1
    return out


def guitar_svg(combo, chord):
    sx, fy, top = 12, 13, 14
    W, H = 5 * sx + 16, top + MAX_FRET * fy + 6
    x = lambda s: 8 + s * sx
    fingers = guitar_fingers(combo)
    parts = [f'<svg class="gb" viewBox="0 0 {W} {H}" role="img" aria-label="{chord} on guitar">']
    parts.append(f'<rect class="g-nut" x="{x(0)}" y="{top - 2.5}" width="{5 * sx}" height="2.5"/>')
    for i in range(1, MAX_FRET + 1):
        parts.append(f'<line class="g-line" x1="{x(0)}" x2="{x(5)}" y1="{top + i * fy}" y2="{top + i * fy}"/>')
    for s in range(6):
        parts.append(f'<line class="g-line" x1="{x(s)}" x2="{x(s)}" y1="{top}" y2="{top + MAX_FRET * fy}"/>')
    for s, f in enumerate(combo):
        if f is None:
            parts.append(f'<text class="g-mark" x="{x(s)}" y="{top - 5}">×</text>')
        elif f == 0:
            parts.append(f'<circle class="g-open" cx="{x(s)}" cy="{top - 7.5}" r="2.6"/>')
        else:
            cy = top + (f - .5) * fy
            parts.append(f'<circle class="g-dot" cx="{x(s)}" cy="{cy}" r="4.4"/>')
            parts.append(f'<text class="g-fn" x="{x(s)}" y="{cy + 2.2}">{fingers[s]}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def sounding_notes(combo, capo, chord):
    return ' '.join(note_name((TUNING[s] + capo + f) % 12, chord) for s, f in enumerate(combo) if f is not None)
